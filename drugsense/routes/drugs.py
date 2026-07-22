from fastapi import APIRouter, HTTPException
from ..database import bq_client
from ..models import MuadilResponse
from google.cloud import bigquery

router = APIRouter()

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"

@router.get("/get-muadiller/{drug_name}", response_model=MuadilResponse)
def get_muadiller(drug_name: str):
    """Verilen ilacın etken maddesini bulur ve aynı etken maddeye sahip diğer ilaçları listeler."""
    
    # Önce ilacın etken maddesini buluyoruz
    query_active_ingredient = f"""
        SELECT active_ingredient 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(drug_name) = @drug_name
    """
    
    job_config_ai = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower())]
    )
    
    query_job_ai = bq_client.query(query_active_ingredient, job_config=job_config_ai)
    results_ai = list(query_job_ai.result())
    
    if not results_ai:
        raise HTTPException(status_code=404, detail="İlaç bulunamadı.")
    
    active_ingredient = results_ai[0].active_ingredient
    
    # Şimdi aynı etken maddeye sahip diğer ilaçları buluyoruz
    query_alternatives = f"""
        SELECT drug_name 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(active_ingredient) = @active_ingredient AND LOWER(drug_name) != @drug_name
    """
    
    job_config_alt = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("active_ingredient", "STRING", active_ingredient.lower()),
            bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower())
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
    
    # 1. İlacın etken maddesini bulalım
    ing_query = f"""
        SELECT active_ingredient 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(drug_name) = @drug_name
        LIMIT 1
    """
    ing_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower())])
    ing_res = list(bq_client.query(ing_query, job_config=ing_config).result())
    
    if not ing_res:
        raise HTTPException(status_code=404, detail="İlaç veritabanında bulunamadı.")
    
    active_ingredient = ing_res[0].active_ingredient

    # 2. drug_diseases tablosunda bu etken madde ve hastalık eşleşmesini sorgulayalım
    check_query = f"""
        SELECT disease_name, risk_level, warning_message
        FROM `{PROJECT_ID}.{DATASET_ID}.drug_diseases`
        WHERE LOWER(active_ingredient) = LOWER(@active_ingredient)
          AND UPPER(icd10_code) = UPPER(@icd10_code)
        LIMIT 1
    """
    check_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("active_ingredient", "STRING", active_ingredient),
            bigquery.ScalarQueryParameter("icd10_code", "STRING", icd10_code)
        ]
    )
    check_res = list(bq_client.query(check_query, job_config=check_config).result())
    
    if not check_res:
        return {
            "drug_name": drug_name,
            "active_ingredient": active_ingredient,
            "icd10_code": icd10_code,
            "risk_status": "SAFE",
            "warning": "Bu ilaç ile belirtilen hastalık arasında kayıtlı bir kontrendikasyon (risk) bulunamadı."
        }
        
    risk_data = check_res[0]
    return {
        "drug_name": drug_name,
        "active_ingredient": active_ingredient,
        "icd10_code": icd10_code,
        "disease_name": risk_data.disease_name,
        "risk_status": risk_data.risk_level, # Örn: Major, Moderate
        "warning": risk_data.warning_message
    }