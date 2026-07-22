from fastapi import APIRouter, HTTPException
from google.cloud import bigquery
from ..database import bq_client
from ..models import PatientProfile, AllergyRecord, MedicationRecord, DiseaseRecord
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

router = APIRouter()

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"


@router.get("/profile/{tc_no}", response_model=PatientProfile)
def get_patient_profile(tc_no: str):
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    # Ortak konfigürasyon
    query_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("tc_no", "STRING", tc_no)]
    )

    # 1. Hasta bilgisi (PROJECT_ID ve DATASET_ID düzeltildi)
    patient_query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.patients` WHERE CAST(tc_no AS STRING) = @tc_no LIMIT 1"
    patient_rows = list(bq_client.query(patient_query, job_config=query_config).result())
    
    if not patient_rows:
        raise HTTPException(status_code=404, detail="Hasta bulunamadı.")
    patient = patient_rows[0]

    # 2. Alerjiler
    allergy_query = f"SELECT allergen_name, severity, source FROM `{PROJECT_ID}.{DATASET_ID}.patient_allergies` WHERE CAST(tc_no AS STRING) = @tc_no"
    allergies = [
        AllergyRecord(allergen_name=row.allergen_name, severity=row.severity, source=row.source)
        for row in bq_client.query(allergy_query, job_config=query_config).result()
    ]

    # 3. Hastalıklar (Kronik Tanılar)
    disease_query = f"SELECT icd10_code, disease_name, diagnosed_date FROM `{PROJECT_ID}.{DATASET_ID}.patient_diseases` WHERE CAST(patient_tc_no AS STRING) = @tc_no"
    diseases = [
        DiseaseRecord(icd10_code=row.icd10_code, disease_name=row.disease_name, diagnosed_date=str(row.diagnosed_date))
        for row in bq_client.query(disease_query, job_config=query_config).result()
    ]

    # 4. Aktif ve Geçmiş İlaçlar
    medication_query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.patient_medications` WHERE CAST(tc_no AS STRING) = @tc_no"
    active_medications = []
    past_medications = []

    for row in bq_client.query(medication_query, job_config=query_config).result():
        medication = MedicationRecord(
            drug_name=row.drug_name, 
            status=row.status, 
            prescribed_date=str(row.prescribed_date), 
            prescribing_doctor=row.prescribing_doctor
        )
        if row.status.lower() == "aktif":
            active_medications.append(medication)
        else:
            past_medications.append(medication)

    return PatientProfile(
        tc_no=str(patient.tc_no),
        full_name=patient.full_name,
        age=patient.age,
        blood_type=patient.blood_type,
        allergies=allergies,
        diseases=diseases,
        active_medications=active_medications,
        past_medications=past_medications
    )

class SideEffectReport(BaseModel):
    patient_tc: str
    drug_name: str
    symptoms: str
    severity: str  # Örn: "Hafif", "Orta", "Şiddetli"

# 2. Yan Etki Bildirme Endpoint'i
@router.post("/report-side-effect")
def report_medication_side_effect(report: SideEffectReport):
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
    report_date = datetime.now(timezone.utc).isoformat()
    
    # BigQuery'ye "Beklemede" (PENDING) statüsü ile kayıt atıyoruz
    query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.side_effect_reports`
        (report_id, patient_tc, drug_name, symptoms, severity, report_date, status)
        VALUES (@report_id, @tc_no, @drug_name, @symptoms, @severity, CAST(@report_date AS TIMESTAMP), 'PENDING')
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("report_id", "STRING", report_id),
            bigquery.ScalarQueryParameter("tc_no", "STRING", report.patient_tc),
            bigquery.ScalarQueryParameter("drug_name", "STRING", report.drug_name),
            bigquery.ScalarQueryParameter("symptoms", "STRING", report.symptoms),
            bigquery.ScalarQueryParameter("severity", "STRING", report.severity),
            bigquery.ScalarQueryParameter("report_date", "STRING", report_date),
        ]
    )

    try:
        bq_client.query(query, job_config=job_config).result()
        return {
            "status": "success",
            "message": "Yan etki bildiriminiz başarıyla alındı ve doktorunuzun onayına sunuldu.",
            "report_id": report_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bildirim kaydedilemedi: {str(e)}")