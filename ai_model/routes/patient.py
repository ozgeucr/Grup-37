import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid

# Projendeki veritabanı modülü (Göreceli yollar projene göre ayarlanabilir)
from ..database import bq_client

router = APIRouter(tags=["Patient Profile"])
logger = logging.getLogger(__name__)

PROJECT_ID = bq_client.project if bq_client else "default_project"
DATASET_ID = "drugsense_dataset"


# ==========================================
# VERİ MODELLERİ (PYDANTIC)
# ==========================================
class MedicationRecord(BaseModel):
    drug_name: str
    status: str
    prescribed_date: str
    prescribing_doctor: Optional[str] = "-"

class AllergyRecord(BaseModel):
    allergen_name: str
    severity: str

class DiseaseRecord(BaseModel):
    disease_name: str
    icd10_code: str

class PatientProfile(BaseModel):
    tc_no: str
    full_name: str
    age: Optional[int] = None
    blood_type: Optional[str] = None
    allergies: List[AllergyRecord] = Field(default_factory=list)
    diseases: List[DiseaseRecord] = Field(default_factory=list)
    active_medications: List[MedicationRecord] = Field(default_factory=list)
    past_medications: List[MedicationRecord] = Field(default_factory=list)

class SideEffectReport(BaseModel):
    tc_no: str = Field(alias="patient_tc") 
    drug_name: str
    symptoms: str  # Frontend'den gelen veri
    severity: str
    
    class Config:
        populate_by_name = True 


# ==========================================
# VERİTABANI YARDIMCI FONKSİYONU
# ==========================================
def execute_bq_query(query: str, parameters: list) -> list:
    if not bq_client:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")
    
    job_config = bigquery.QueryJobConfig(query_parameters=parameters)
    try:
        return list(bq_client.query(query, job_config=job_config).result())
    except Exception as e:
        logger.error(f"BigQuery Sorgu Hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Veritabanı sorgusu sırasında hata oluştu.")


# ==========================================
def get_patient_profile(tc_no: str) -> PatientProfile:
    clean_tc = tc_no.strip()

    print("=" * 60)
    print(f"🔍 Hasta aranıyor : {clean_tc}")
    print(f"📦 Project        : {PROJECT_ID}")
    print(f"📂 Dataset        : {DATASET_ID}")

    user_query = f"""
        SELECT
            tc_no,
            full_name,
            age,
            blood_type
        FROM `{PROJECT_ID}.{DATASET_ID}.patients`
        WHERE TRIM(CAST(tc_no AS STRING)) = @tc_no
        LIMIT 1
    """

    print("SQL:")
    print(user_query)

    user_res = execute_bq_query(
        user_query,
        [
            bigquery.ScalarQueryParameter(
                "tc_no",
                "STRING",
                clean_tc
            )
        ]
    )

    print(f"Bulunan kayıt sayısı : {len(user_res)}")

    if len(user_res) > 0:
        print(dict(user_res[0].items()))

    if not user_res:
        raise HTTPException(
            status_code=404,
            detail=f"Hasta bulunamadı ({clean_tc})"
        )

    row = user_res[0]

    profile = PatientProfile(
        tc_no=clean_tc,
        full_name=row.full_name,
        age=row.age,
        blood_type=row.blood_type
    )

    # ---------------- ALLERGIES ----------------

    allergy_query = f"""
        SELECT
            allergen_name,
            severity
        FROM `{PROJECT_ID}.{DATASET_ID}.patient_allergies`
        WHERE TRIM(CAST(tc_no AS STRING))=@tc_no
    """

    allergies = execute_bq_query(
        allergy_query,
        [bigquery.ScalarQueryParameter("tc_no", "STRING", clean_tc)]
    )

    for a in allergies:
        profile.allergies.append(
            AllergyRecord(
                allergen_name=a.allergen_name,
                severity=a.severity
            )
        )

    # ---------------- DISEASES ----------------

    disease_query = f"""
        SELECT
            disease_name,
            icd10_code
        FROM `{PROJECT_ID}.{DATASET_ID}.patient_diseases`
        WHERE TRIM(CAST(tc_no AS STRING))=@tc_no
    """

    diseases = execute_bq_query(
        disease_query,
        [bigquery.ScalarQueryParameter("tc_no", "STRING", clean_tc)]
    )

    for d in diseases:
        profile.diseases.append(
            DiseaseRecord(
                disease_name=d.disease_name,
                icd10_code=d.icd10_code
            )
        )

    # ---------------- MEDICATIONS ----------------

    med_query = f"""
        SELECT
            drug_name,
            status,
            prescribed_date,
            prescribing_doctor
        FROM `{PROJECT_ID}.{DATASET_ID}.patient_medications`
        WHERE TRIM(CAST(tc_no AS STRING))=@tc_no
    """

    meds = execute_bq_query(
        med_query,
        [bigquery.ScalarQueryParameter("tc_no", "STRING", clean_tc)]
    )

    for m in meds:

        med = MedicationRecord(
            drug_name=m.drug_name,
            status=m.status,
            prescribed_date=str(m.prescribed_date),
            prescribing_doctor=m.prescribing_doctor or "-"
        )

        if str(m.status).lower() in ["aktif", "active"]:
            profile.active_medications.append(med)
        else:
            profile.past_medications.append(med)

    print("✅ Hasta başarıyla bulundu.")
    print("=" * 60)

    return profile


# ==========================================
# API ENDPOINT'LERİ
# ==========================================
@router.get("/profile/{tc_no}", response_model=PatientProfile)
def api_get_patient_profile(tc_no: str):
    return get_patient_profile(tc_no)


@router.post("/side-effect", status_code=status.HTTP_201_CREATED)
def report_side_effect(report: SideEffectReport):
    report_id = f"SE-{uuid.uuid4().hex[:8].upper()}"
    current_time = datetime.now(timezone.utc).isoformat()
    
    # DÜZELTME: Tablodaki gerçek kolon adı olan 'symptom' kullanıldı (fazladan verification_status parametresi temizlendi)
    query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.side_effect_reports`
        (report_id, tc_no, drug_name, symptom, verification_status, reported_at)
        VALUES (@r_id, @tc_no, @drug, @symptom, 'PENDING', CAST(@reported_at AS TIMESTAMP))
    """
    params = [
        bigquery.ScalarQueryParameter("r_id", "STRING", report_id),
        bigquery.ScalarQueryParameter("tc_no", "STRING", report.tc_no),
        bigquery.ScalarQueryParameter("drug", "STRING", report.drug_name),
        bigquery.ScalarQueryParameter("symptom", "STRING", report.symptoms),
        bigquery.ScalarQueryParameter("reported_at", "STRING", current_time)
    ]
    
    execute_bq_query(query, params)
    
    return {"status": "success", "message": "Yan etki bildirimi başarıyla oluşturuldu.", "report_id": report_id}


@router.get("/pending-side-effects/{tc_no}")
def get_pending_side_effects(tc_no: str):
    # DÜZELTME: Tablodaki tekil 'symptom' kolonu sorgulanıyor ve mapleme yapılıyor
    query = f"""
        SELECT
            report_id,
            drug_name,
            symptom,
            verification_status,
            reported_at
        FROM `{PROJECT_ID}.{DATASET_ID}.side_effect_reports`
        WHERE
            CAST(tc_no AS STRING) = @tc_no
            AND verification_status = 'PENDING'
        ORDER BY reported_at DESC
    """

    params = [
        bigquery.ScalarQueryParameter(
            "tc_no",
            "STRING",
            tc_no.strip()
        )
    ]

    rows = execute_bq_query(query, params)

    return {
        "pending_reports": [
            {
                "report_id": r.report_id,
                "drug_name": r.drug_name,
                "symptoms": r.symptom, # Frontend 'symptoms' beklediği için veritabanındaki 'symptom' buraya mapleniyor
                "verification_status": r.verification_status,
                "reported_at": str(r.reported_at)
            }
            for r in rows
        ]
    }