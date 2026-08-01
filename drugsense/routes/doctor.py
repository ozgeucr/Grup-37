from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import bq_client
from google.cloud import bigquery
from .drugs import get_muadiller
from .patient import get_patient_profile
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone

router = APIRouter()
PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
logger = logging.getLogger(__name__)

# --- MODELLER ---
class PrescriptionRequest(BaseModel):
    patient_id: str
    doctor_id: str
    new_drug_name: str
    current_cart: List[str] = [] 
    accept_responsibility: bool = False
    override_reason: Optional[str] = None

class SaveDrugItem(BaseModel):
    drug_name: str
    status: str
    override_reason: Optional[str] = None

class SavePrescriptionRequest(BaseModel):
    patient_id: str
    doctor_id: str
    drugs: List[SaveDrugItem]


# --- YARDIMCI FONKSİYONLAR (Tekli Sorgular) ---

def get_drug_ingredient(drug_name: str):
    """titck_drugs tablosundan tek bir ilacın etken maddesini çeker."""
    query = f"SELECT active_ingredient FROM `{PROJECT_ID}.{DATASET_ID}.drugs` WHERE LOWER(drug_name) = @drug LIMIT 1"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("drug", "STRING", drug_name.lower())])
    res = list(bq_client.query(query, job_config=job_config).result())
    return res[0].active_ingredient if res else None

def get_interaction(ing1: str, ing2: str):
    """ddinter_interactions tablosundan iki etken madde arası etkileşimi sorgular."""
    query = f"""
        SELECT level FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE (LOWER(drug1_name) = @ing1 AND LOWER(drug2_name) = @ing2) 
           OR (LOWER(drug1_name) = @ing2 AND LOWER(drug2_name) = @ing1)
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("ing1", "STRING", ing1.lower()),
            bigquery.ScalarQueryParameter("ing2", "STRING", ing2.lower())
        ]
    )
    res = list(bq_client.query(query, job_config=job_config).result())
    return res[0].level if res else None


# --- YARDIMCI FONKSİYONLAR (Toplu Sorgular ve Akıllı Çözümleyici) ---

def get_bulk_drug_ingredients(drug_names: list[str]) -> dict:
    """YENİ: Hem ticari isimleri hem de etken maddeleri akıllıca tanır ve eşleştirir."""
    if not drug_names:
        return {}
    
    lower_drugs = [d.lower() for d in drug_names]
    
    query = f"""
        SELECT LOWER(drug_name) as d_name, LOWER(active_ingredient) as a_ing 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(drug_name) IN UNNEST(@drug_list)
           OR LOWER(active_ingredient) IN UNNEST(@drug_list)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ArrayQueryParameter("drug_list", "STRING", lower_drugs)]
    )
    res = bq_client.query(query, job_config=job_config).result()
    
    result_dict = {}
    for row in res:
        # Eğer doktor ticari isim yazdıysa (Örn: Majezik)
        if row.d_name in lower_drugs:
            result_dict[row.d_name] = row.a_ing
        # Eğer doktor doğrudan etken madde yazdıysa (Örn: Ibuprofen)
        if row.a_ing in lower_drugs:
            result_dict[row.a_ing] = row.a_ing
            
    return result_dict

def get_bulk_interactions(new_ing: str, patient_ings: list[str]) -> dict:
    if not new_ing or not patient_ings:
        return {}
        
    query = f"""
        SELECT Drug_A as drug1_name, Drug_B as drug2_name, Level as level 
        FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE (LOWER(Drug_A) = LOWER(@new_ing) AND LOWER(Drug_B) IN UNNEST(@patient_ings))
           OR (LOWER(Drug_B) = LOWER(@new_ing) AND LOWER(Drug_A) IN UNNEST(@patient_ings))
        
        UNION ALL
        
        SELECT ingredient_1 as drug1_name, ingredient_2 as drug2_name, risk_level as level 
        FROM `{PROJECT_ID}.{DATASET_ID}.interactions`
        WHERE (LOWER(ingredient_1) = LOWER(@new_ing) AND LOWER(ingredient_2) IN UNNEST(@patient_ings))
           OR (LOWER(ingredient_2) = LOWER(@new_ing) AND LOWER(ingredient_1) IN UNNEST(@patient_ings))
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing.lower()),
            bigquery.ArrayQueryParameter("patient_ings", "STRING", [ing.lower() for ing in patient_ings])
        ]
    )
    res = bq_client.query(query, job_config=job_config).result()
    
    interactions = {}
    for row in res:
        if row.drug1_name.lower() == new_ing.lower():
            interacting_drug = row.drug2_name.lower()
        else:
            interacting_drug = row.drug1_name.lower()
            
        interactions[interacting_drug] = row.level
        
    return interactions


# --- YARDIMCI FONKSİYONLAR (Güvenlik Filtreleri) ---

def check_drug_disease_contraindications(new_ing: str, patient_diseases: list) -> list:
    if not new_ing or not patient_diseases:
        return []
        
    disease_codes = [d.icd10_code for d in patient_diseases if hasattr(d, 'icd10_code')]
    if not disease_codes:
        return []

    query = f"""
        SELECT icd10_code, disease_name, risk_level, warning_message
        FROM `{PROJECT_ID}.{DATASET_ID}.drug_diseases`
        WHERE LOWER(active_ingredient) = LOWER(@new_ing)
          AND icd10_code IN UNNEST(@disease_codes)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing.lower()),
            bigquery.ArrayQueryParameter("disease_codes", "STRING", disease_codes)
        ]
    )
    res = bq_client.query(query, job_config=job_config).result()
    
    conflicts = []
    for row in res:
        conflicts.append({
            "disease_name": row.disease_name,
            "icd10_code": row.icd10_code,
            "level": row.risk_level,
            "warning": row.warning_message
        })
    return conflicts

def check_food_interactions(new_ing: str) -> list:
    if not new_ing:
        return []
    query = f"SELECT interacting_food, risk_level, warning_message FROM `{PROJECT_ID}.{DATASET_ID}.drug_foods` WHERE LOWER(active_ingredient) = LOWER(@new_ing)"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing.lower())])
    res = list(bq_client.query(query, job_config=job_config).result())
    return [{"food": row.interacting_food, "level": row.risk_level, "message": row.warning_message} for row in res]

def check_therapeutic_duplication(new_ing: str, patient_active_ings: list[str]) -> bool:
    if not new_ing or not patient_active_ings:
        return False
    return new_ing.lower() in [ing.lower() for ing in patient_active_ings if ing]

def check_age_warnings(new_ing: str, patient_age: int) -> str:
    if not new_ing or patient_age is None:
        return ""
    ing_lower = new_ing.lower()
    if patient_age < 16 and "acetylsalicylic acid" in ing_lower:
        return "KRİTİK UYARI (Pediatrik): 16 yaş altı çocuklarda Reye Sendromu riski nedeniyle kesinlikle kontrendikedir."
    if patient_age >= 65:
        if any(nsaid in ing_lower for nsaid in ["dexketoprofen", "flurbiprofen", "naproxen", "ibuprofen", "diclofenac"]):
            return "Geriatrik Uyarı (65+): NSAİİ kullanımı mide kanaması ve böbrek yetmezliği riskini artırır. En düşük etkili doz tercih edilmelidir."
        if "tramadol" in ing_lower:
            return "Geriatrik Uyarı (65+): Solunum depresyonu ve düşme riski artar. Doz ayarlaması gereklidir."
    return ""


# --- YARDIMCI FONKSİYONLAR (Veritabanı Kayıt İşlemleri) ---

def save_single_drug_to_db(prescription_id: str, patient_tc: str, doctor_tc: str, drug_name: str, status: str, override_reason: Optional[str] = None):
    current_time = datetime.now(timezone.utc).isoformat()
    insert_query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.prescriptions`
        (prescription_id, patient_tc_no, doctor_tc_no, drug_name, status, override_reason, created_at)
        VALUES (@p_id, @pat_tc, @doc_tc, @drug, @status, @reason, CAST(@created_at AS TIMESTAMP))
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("p_id", "STRING", prescription_id),
            bigquery.ScalarQueryParameter("pat_tc", "STRING", patient_tc),
            bigquery.ScalarQueryParameter("doc_tc", "STRING", doctor_tc),
            bigquery.ScalarQueryParameter("drug", "STRING", drug_name),
            bigquery.ScalarQueryParameter("status", "STRING", status),
            bigquery.ScalarQueryParameter("reason", "STRING", override_reason or ""),
            bigquery.ScalarQueryParameter("created_at", "STRING", current_time),
        ]
    )
    bq_client.query(insert_query, job_config=job_config).result()

def add_to_patient_medications(patient_tc: str, doctor_tc: str, drug_name: str):
    insert_query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.patient_medications`
        (tc_no, drug_name, status, prescribed_date, prescribing_doctor)
        SELECT @tc_no, @drug_name, 'Aktif', CURRENT_DATE(), full_name
        FROM `{PROJECT_ID}.{DATASET_ID}.users`
        WHERE CAST(tc_no AS STRING) = @doctor_tc
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("tc_no", "STRING", patient_tc),
            bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name),
            bigquery.ScalarQueryParameter("doctor_tc", "STRING", doctor_tc)
        ]
    )
    try:
        bq_client.query(insert_query, job_config=job_config).result()
    except Exception as e:
        logger.error(f"Hastanın ilaç profili güncellenirken hata: {str(e)}")


# --- DİNAMİK İSTATİSTİK ENDPOINT'İ ---

@router.get("/doctor/stats/{doctor_tc}")
def get_doctor_stats(doctor_tc: str):
    """Doktorun dashboard'u için gerçek zamanlı canlı verileri BigQuery'den çeker."""
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    query = f"""
        SELECT 
            COUNT(DISTINCT prescription_id) as total_rx,
            COUNT(DISTINCT CASE WHEN DATE(created_at) = CURRENT_DATE() THEN prescription_id END) as today_rx,
            COUNT(CASE WHEN status IN ('WARNING', 'CRITICAL') THEN 1 END) as total_warnings,
            COUNT(CASE WHEN status = 'CRITICAL' THEN 1 END) as critical_warnings,
            COUNT(DISTINCT patient_tc_no) as unique_patients,
            COUNT(DISTINCT CASE WHEN DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN patient_tc_no END) as recent_patients,
            COUNT(CASE WHEN status = 'SAFE' THEN 1 END) as safe_rx
        FROM `{PROJECT_ID}.{DATASET_ID}.prescriptions`
        WHERE CAST(doctor_tc_no AS STRING) = @doctor_tc
    """
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("doctor_tc", "STRING", doctor_tc)])
    res = list(bq_client.query(query, job_config=job_config).result())
    
    if not res:
        return {
            "active_prescriptions": {"value": "0", "sub": "+0 bugün"},
            "warnings": {"value": "0", "sub": "0 kritik"},
            "scanned_patients": {"value": "0", "sub": "+0 bu hafta"},
            "ai_score": {"value": "%100", "sub": "AI Engine v3.2"}
        }
    
    row = res[0]
    total_rx = row.total_rx or 0
    safe_rx = row.safe_rx or 0
    ai_score = round((safe_rx / total_rx * 100), 1) if total_rx > 0 else 100.0

    return {
        "active_prescriptions": {"value": str(total_rx), "sub": f"+{row.today_rx or 0} bugün"},
        "warnings": {"value": str(row.total_warnings or 0), "sub": f"{row.critical_warnings or 0} kritik"},
        "scanned_patients": {"value": str(row.unique_patients or 0), "sub": f"+{row.recent_patients or 0} bu hafta"},
        "ai_score": {"value": f"%{ai_score}", "sub": "AI Engine v3.2"}
    }


# --- ANA ENDPOINTLER ---

@router.post("/doctor/prescribe-and-analyze")
def prescribe_and_analyze(request: PrescriptionRequest):
    try:
        patient = get_patient_profile(request.patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hasta profili alınırken hata oluştu.")
    
    patient_drug_names = [med.drug_name for med in patient.active_medications] + request.current_cart
    all_drugs_to_check = patient_drug_names + [request.new_drug_name]

    ingredients_dict = get_bulk_drug_ingredients(all_drugs_to_check)
    new_ing = ingredients_dict.get(request.new_drug_name.lower())
    
    if not new_ing:
        return {
            "patient": patient.full_name,
            "new_drug": request.new_drug_name,
            "overall_status": "MANUAL_REVIEW", 
            "system_note": "İlaç tanımlanamadı.", 
            "recommendation": "Bu ilaç (veya etken madde) veritabanında bulunamadı. Lütfen klinik inceleme yapın."
        }

    report = {
        "patient": patient.full_name,
        "new_drug": request.new_drug_name,
        "overall_status": "SAFE",
        "is_prescription_blocked": False,
        "polypharmacy": len(patient_drug_names) >= 5,
        "suggestions": [],
        "recommendation": "İlaç güvenle reçeteye eklenebilir."
    }

    if report["polypharmacy"]:
        report["suggestions"].append("Hastada polifarmasi riski (5+ ilaç kullanımı) bulunmaktadır.")

    patient_ings = [ingredients_dict.get(drug.lower()) for drug in patient_drug_names if ingredients_dict.get(drug.lower())]
    
    if check_therapeutic_duplication(new_ing, patient_ings):
        report["overall_status"] = "WARNING"
        report["suggestions"].append("DUPLİKASYON UYARISI: Hasta veya reçete sepeti halihazırda bu etken maddeyi içermektedir.")

    if patient.age:
        age_warning = check_age_warnings(new_ing, patient.age)
        if age_warning:
            report["overall_status"] = "CRITICAL" if "KRİTİK" in age_warning else "WARNING"
            if report["overall_status"] == "CRITICAL": report["is_prescription_blocked"] = True
            report["suggestions"].append(age_warning)

    for allergy in patient.allergies:
        if allergy.allergen_name.lower() in new_ing.lower():
            report["overall_status"] = "CRITICAL"
            report["is_prescription_blocked"] = True
            report["suggestions"].append(f"KRİTİK ALERJİ: {allergy.allergen_name} alerjisi tespit edildi!")

    disease_conflicts = check_drug_disease_contraindications(new_ing, patient.diseases)
    for conflict in disease_conflicts:
        level = conflict["level"].strip().capitalize()
        warning_text = f"Hastalık Çatışması ({conflict['disease_name']}): {conflict['warning']}"
        if level == "Major":
            report["overall_status"] = "CRITICAL"
            report["is_prescription_blocked"] = True
        elif level == "Moderate" and report["overall_status"] != "CRITICAL":
            report["overall_status"] = "WARNING"
        report["suggestions"].append(warning_text)

    food_interactions = check_food_interactions(new_ing)
    for fw in food_interactions:
        food_level = fw['level'].strip().capitalize()
        report["suggestions"].append(f"Besin Etkileşimi [{food_level}] ({fw['food']}): {fw['message']}")

    interactions_dict = get_bulk_interactions(new_ing, patient_ings)
    for med in patient_drug_names:
        med_ing = ingredients_dict.get(med.lower())
        if not med_ing: continue
        level = interactions_dict.get(med_ing.lower())
        if level:
            level_str = level.strip().capitalize()
            if level_str == "Major":
                report["overall_status"] = "CRITICAL"
                report["is_prescription_blocked"] = True
                report["suggestions"].append(f"DİKKAT: {med} ile MAJÖR düzeyde ilaç etkileşimi!")
            elif level_str == "Moderate" and report["overall_status"] != "CRITICAL":
                report["overall_status"] = "WARNING"
                report["suggestions"].append(f"Uyarı: {med} ile Orta düzey etkileşim.")

    if report["is_prescription_blocked"]:
        if not request.accept_responsibility:
            raise HTTPException(status_code=400, detail=f"DİKKAT: {request.new_drug_name} engellendi. İlacı listeye eklemek için sorumluluk onayını vermeli ve gerekçe sunmalısınız.")
        elif not request.override_reason:
            raise HTTPException(status_code=400, detail="Gerekçe (override_reason) girmek zorundasınız.")
        else:
            report["is_prescription_blocked"] = False
            report["overall_status"] = "OVERRIDDEN_BY_DOCTOR"
            report["recommendation"] = f"Hekim inisiyatifiyle onaylandı. Gerekçe: {request.override_reason}"

    return report


@router.post("/doctor/save-prescription")
def save_prescription_batch(request: SavePrescriptionRequest):
    if not request.drugs:
        raise HTTPException(status_code=400, detail="Reçete sepeti boş.")
        
    prescription_id = f"RX-{uuid.uuid4().hex[:8].upper()}"
    try:
        for item in request.drugs:
            save_single_drug_to_db(prescription_id, request.patient_id, request.doctor_id, item.drug_name, item.status, item.override_reason)
            add_to_patient_medications(request.patient_id, request.doctor_id, item.drug_name)
        return {"status": "success", "message": "Reçete başarıyla imzalandı ve sisteme kaydedildi.", "prescription_id": prescription_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Reçete kaydedilemedi.")


@router.get("/doctor-patient-history/{doctor_tc}/{patient_tc}")
def get_doctor_filtered_history(doctor_tc: str, patient_tc: str):
    """Zaman damgalı (Gün hesaplamalı) geçmiş reçete bilgisi çeker."""
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    prescription_query = f"""
        SELECT p.prescription_id, p.drug_name, p.status, p.created_at,
               DATE_DIFF(CURRENT_DATE(), DATE(p.created_at), DAY) as days_passed
        FROM `{PROJECT_ID}.{DATASET_ID}.prescriptions` p
        WHERE CAST(p.patient_tc_no AS STRING) = @patient_tc 
          AND CAST(p.doctor_tc_no AS STRING) = @doctor_tc
        ORDER BY p.created_at DESC
    """
    
    rx_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("patient_tc", "STRING", patient_tc),
            bigquery.ScalarQueryParameter("doctor_tc", "STRING", doctor_tc)
        ]
    )
    
    rx_rows = bq_client.query(prescription_query, job_config=rx_config).result()
    
    history_records = []
    for row in rx_rows:
        days = row.days_passed
        time_label = f"Bugün" if days == 0 else f"{days} gün önce"
        history_records.append({
            "prescription_id": row.prescription_id,
            "drug_name": row.drug_name,
            "status": row.status,
            "time_label": time_label,
            "created_at": str(row.created_at)
        })

    return {"filtered_prescriptions": history_records}

class ApproveSideEffectRequest(BaseModel):
    report_id: str
    patient_tc: str
    allergen_name: str
    severity: str

@router.post("/doctor/approve-side-effect")
def approve_side_effect(request: ApproveSideEffectRequest):
    """Doktor bildirimi onaylar, raporu APPROVED yapar ve hastanın alerji listesine ekler."""
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    try:
        # 1. Rapor durumunu APPROVED yap
        update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.side_effect_reports`
            SET status = 'APPROVED'
            WHERE report_id = @report_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("report_id", "STRING", request.report_id)]
        )
        bq_client.query(update_query, job_config=job_config).result()

        # 2. Hastanın resmi alerji profiline (patient_allergies) ekle
        insert_allergy_query = f"""
            INSERT INTO `{PROJECT_ID}.{DATASET_ID}.patient_allergies`
            (tc_no, allergen_name, severity, source)
            VALUES (@tc_no, @allergen_name, @severity, 'Doktor Onaylı Bildirim')
        """
        allergy_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tc_no", "STRING", request.patient_tc),
                bigquery.ScalarQueryParameter("allergen_name", "STRING", request.allergen_name),
                bigquery.ScalarQueryParameter("severity", "STRING", request.severity),
            ]
        )
        bq_client.query(insert_allergy_query, job_config=allergy_config).result()

        return {"status": "success", "message": "Bildirim onaylandı ve hastanın resmi alerji listesine eklendi."}
    except Exception as e:
        logger.error(f"Alerji onaylanırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail="İşlem başarısız oldu.")