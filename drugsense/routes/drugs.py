from fastapi import APIRouter, HTTPException
from ..database import bq_client
from ..models import MuadilResponse

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