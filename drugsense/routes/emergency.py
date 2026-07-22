from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid
import logging
from ..database import bq_client
from google.cloud import bigquery

router = APIRouter()
PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
logger = logging.getLogger(__name__)

# İstek (Request) Modeli
class BreakGlassRequest(BaseModel):
    paramedic_tc: str
    patient_tc: str
    reason: str = "Acil Müdahale"

def log_emergency_action(actor_tc: str, target_tc: str, details: str):
    """Bu fonksiyon arka planda çalışır. Paramediği bekletmeden veritabanına log düşer."""
    log_id = f"EMG-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. Audit Log (Yasal Denetim Kaydı)
    audit_query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.audit_logs` 
        (log_id, actor_tc_no, action_type, target_tc_no, timestamp, details)
        VALUES (@log_id, @actor, 'EMERGENCY_ACCESS', @target, CAST(@time AS TIMESTAMP), @details)
    """
    
    # 2. Hasta ve Doktor Paneli İçin Bildirim Kaydı (Eğer notifications tablon varsa buraya düşer)
    # Not: Sistemde bildirim paneli için audit_logs veya ayrı bir bildirim tablosu kullanılabilir.
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("log_id", "STRING", log_id),
            bigquery.ScalarQueryParameter("actor", "STRING", actor_tc),
            bigquery.ScalarQueryParameter("target", "STRING", target_tc),
            bigquery.ScalarQueryParameter("time", "STRING", now),
            bigquery.ScalarQueryParameter("details", "STRING", details)
        ]
    )
    try:
        bq_client.query(audit_query, job_config=job_config).result()
        logger.info(f"KIRMIZI ALARM LOGLANDI VE BİLDİRİM OLUŞTURULDU: {actor_tc} -> {target_tc}")
    except Exception as e:
        logger.error(f"Acil durum loglama/bildirim hatası: {e}")

@router.post("/break-glass")
def emergency_break_glass(request: BreakGlassRequest, background_tasks: BackgroundTasks):
    """Paramediklerin hastanın hayati verilerine saniyeler içinde erişmesini sağlar."""
    
    # 1. YETKİ KONTROLÜ (Sadece PARAMEDIC girebilir)
    user_query = f"SELECT role, full_name FROM `{PROJECT_ID}.{DATASET_ID}.users` WHERE tc_no = @tc LIMIT 1"
    user_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("tc", "STRING", request.paramedic_tc)])
    user_res = list(bq_client.query(user_query, job_config=user_config).result())
    
    if not user_res or user_res[0].role != "PARAMEDIC":
        raise HTTPException(status_code=403, detail="Erişim reddedildi! Sadece yetkili Acil Tıp Personeli 'Camı Kır' yetkisine sahiptir.")
    
    paramedic_name = user_res[0].full_name

    # 2. HASTA KONTROLÜ VE HAYATİ VERİLERİ (Hastalıklar)
    disease_query = f"SELECT disease_name, diagnosed_date FROM `{PROJECT_ID}.{DATASET_ID}.patient_diseases` WHERE patient_tc_no = @tc"
    disease_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("tc", "STRING", request.patient_tc)])
    disease_res = list(bq_client.query(disease_query, job_config=disease_config).result())
    
    # Alerjiler
    allergy_query = f"SELECT allergen_name, severity FROM `{PROJECT_ID}.{DATASET_ID}.patient_allergies` WHERE CAST(tc_no AS STRING) = @tc"
    allergy_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("tc", "STRING", request.patient_tc)])
    allergy_res = list(bq_client.query(allergy_query, job_config=allergy_config).result())

    # Geçmiş Operasyonlar / Müdahaleler (Eğer tablonuzda varsa, yoksa boş döner)
    try:
        surgery_query = f"SELECT surgery_name, surgery_date FROM `{PROJECT_ID}.{DATASET_ID}.patient_surgeries` WHERE CAST(patient_tc_no AS STRING) = @tc"
        surgery_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("tc", "STRING", request.patient_tc)])
        surgery_res = list(bq_client.query(surgery_query, job_config=surgery_config).result())
    except Exception:
        surgery_res = [] # Tablo henüz yoksa sistemi patlatmaz

    # 3. ARKA PLANDA LOGLAMA VE BİLDİRİM (Camı Kırıyoruz)
    background_tasks.add_task(
        log_emergency_action, 
        actor_tc=request.paramedic_tc, 
        target_tc=request.patient_tc, 
        details=f"ACİL DURUM: {paramedic_name} tarafından acil müdahale tetiklendi. Gerekçe: {request.reason}. Hastaya acil müdahale yapıldı bildirimi gönderildi."
    )

    # 4. HAYAT KURTARAN VERİYİ DÖN
    return {
        "status": "EMERGENCY_OVERRIDE_ACTIVE",
        "patient_tc": request.patient_tc,
        "warning": "BU BİLGİLER SADECE ACİL MÜDAHALE İÇİNDİR. Hasta ve doktor paneline acil müdahale bildirimi düşülmüştür.",
        "vital_data": {
            "chronic_diseases": [{"disease": row.disease_name, "date": str(row.diagnosed_date)} for row in disease_res],
            "surgeries": [{"surgery": row.surgery_name, "date": str(row.surgery_date)} for row in surgery_res] if surgery_res else [],
            "allergies": [{"allergen": row.allergen_name, "severity": row.severity} for row in allergy_res]
        }
    }