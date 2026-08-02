import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from ..database import bq_client
from ..models import MuadilResponse
from google.cloud import bigquery

# Loglama ayarlarını yapılandırıyoruz
logger = logging.getLogger(__name__)

# Arkadaşının eklediği Yapay Zeka Modelini içe aktarıyoruz
try:
    from ai_model.api.predict import predict_interaction
except ImportError as e:
    # Model yüklenemediğinde terminale ve loglara kırmızı alarm düşer!
    logger.critical(f"YAPAY ZEKA MODELİ YÜKLENEMEDİ! Fallback devrede. Hata: {e}")
    # Eğer import yolunda bir farklılık olursa diye yedek sarmalayıcı
    def predict_interaction(drug_a, drug_b):
        return {
            "risk_level": "Unknown", 
            "mechanism": "AI Model yüklenemedi.", 
            "method": "Fallback",
            "confidence": 0
        }

router = APIRouter(
    tags=["Drugs & Interactions"]
)

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"

@router.get("/get-muadiller/{drug_name}", response_model=MuadilResponse)
def get_muadiller(drug_name: str):
    """Verilen ilacın etken maddesini bulur ve aynı etken maddeye sahip diğer ilaçları listeler."""
    
    query_active_ingredient = f"""
        SELECT active_ingredient 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(drug_name) = @drug_name
    """
    
    job_config_ai = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower().strip())]
    )
    
    query_job_ai = bq_client.query(query_active_ingredient, job_config=job_config_ai)
    results_ai = list(query_job_ai.result())
    
    if not results_ai:
        raise HTTPException(status_code=404, detail="İlaç bulunamadı.")
    
    active_ingredient = results_ai[0].active_ingredient
    
    query_alternatives = f"""
        SELECT drug_name 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(active_ingredient) = @active_ingredient AND LOWER(drug_name) != @drug_name
    """
    
    job_config_alt = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("active_ingredient", "STRING", active_ingredient.lower()),
            bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower().strip())
        ]
    )
    
    query_job_alt = bq_client.query(query_alternatives, job_config=job_config_alt)
    results_alt = list(query_job_alt.result())
    
    alternative_drugs = [row.drug_name for row in results_alt]

    if not alternative_drugs:
        raise HTTPException(status_code=404, detail="Aynı etken maddeye sahip başka ilaç bulunamadı.")
    
    return MuadilResponse(
        original_drug=drug_name,
        active_ingredient=active_ingredient,
        alternative_drugs=alternative_drugs
    )


@router.get("/check-drug-disease/{drug_name}/{icd10_code}")
def check_drug_disease_risk(drug_name: str, icd10_code: str):
    """Verilen ilacın, hastanın belirli bir tanısı/hastalığı (ICD-10) ile çelişip çelişmediğini kontrol eder."""
    
    query = f"""
        SELECT d.active_ingredient, dd.disease_name, dd.risk_level, dd.warning_message
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs` d
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.drug_diseases` dd
          ON LOWER(d.active_ingredient) = LOWER(dd.active_ingredient)
         AND UPPER(dd.icd10_code) = UPPER(@icd10_code)
        WHERE LOWER(d.drug_name) = LOWER(@drug_name)
        LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower().strip()),
            bigquery.ScalarQueryParameter("icd10_code", "STRING", icd10_code.strip())
        ]
    )
    
    result = list(bq_client.query(query, job_config=job_config).result())
    
    if not result:
        raise HTTPException(status_code=404, detail="İlaç veritabanında bulunamadı.")
        
    row = result[0]
    
    if not row.risk_level:
        return {
            "drug_name": drug_name,
            "active_ingredient": row.active_ingredient,
            "icd10_code": icd10_code,
            "risk_status": "SAFE",
            "warning": "Bu ilaç ile belirtilen hastalık arasında kayıtlı bir kontrendikasyon (risk) bulunamadı."
        }
        
    return {
        "drug_name": drug_name,
        "active_ingredient": row.active_ingredient,
        "icd10_code": icd10_code,
        "disease_name": row.disease_name,
        "risk_status": row.risk_level,
        "warning": row.warning_message
    }


# --- YAPAY ZEKA MODELİ İÇİN ÖNBELLEK (CACHE) SARMALAYICISI ---
@lru_cache(maxsize=1000)
def cached_predict(drug_a: str, drug_b: str):
    """Sık sorgulanan ilaç çiftlerini hafızada tutarak ML modeline tekrar yük bindirmeyi engeller."""
    sorted_drugs = sorted([drug_a.lower().strip(), drug_b.lower().strip()])
    result = predict_interaction(sorted_drugs[0], sorted_drugs[1])
    
    # Güvenlilık önlemi: confidence alanı None dönebilen modeller için fallback eklenmiştir
    if isinstance(result, dict) and "confidence" in result:
        if result["confidence"] is None:
            result["confidence"] = 0.0
            
    return result


# --- YAPAY ZEKA DESTEKLİ ETKİLEŞİM ENDPOINT'İ ---
@router.get("/check-ai-interaction/{drug_a}/{drug_b}")
def check_ai_drug_interaction(drug_a: str, drug_b: str):
    """İki ilaç arasındaki etkiyi Yapay Zeka (ML) Modeli ile analiz eder."""
    
    if drug_a.lower().strip() == drug_b.lower().strip():
        raise HTTPException(status_code=400, detail="Aynı ilaç birbiriyle karşılaştırılamaz.")
        
    try:
        ai_result = cached_predict(drug_a, drug_b)
        return {
            "status": "success",
            "interaction_analysis": ai_result
        }
    except Exception as e:
        logger.error(f"Yapay Zeka Analiz Hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Model analizi sırasında bir sunucu hatası oluştu.")