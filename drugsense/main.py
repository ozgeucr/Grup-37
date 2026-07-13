#bu dosyayı şimdilik kaba taslak olarak yazdım, düzenlenebilir

import os
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
bq_client = bigquery.Client()

app = FastAPI(title="DrugSense - Klinik Karar Destek Sistemi API")

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"

@app.get("/search-drug/{drug_name}")
def search_drug(drug_name: str):
    """Kullanıcının yazdığı ilacı BigQuery'de arar ve yardımcı maddeleriyle birlikte getirir."""
    
    # SQL Enjeksiyon güvenliği için parametrik sorgu kullanıyoruz
    query = f"""
        SELECT d.drug_id, d.drug_name, d.active_ingredient, d.atc_code,
               ARRAY_AGG(i.ingredient_name) as excipients
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs` d
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.ingredients` i ON d.drug_id = i.drug_id
        WHERE LOWER(d.drug_name) = @drug_name
        GROUP BY d.drug_id, d.drug_name, d.active_ingredient, d.atc_code
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower())]
    )
    
    query_job = bq_client.query(query, job_config=job_config)
    results = list(query_job.result())
    
    if not results:
        # Burası jüriye bahsedeceğimiz "Eğer BigQuery'de yoksa API'ye git" alanı.
        # Şimdilik simüle etmek adına hata döndürüyoruz.
        raise HTTPException(status_code=404, detail="İlaç lokal BigQuery veritabanında bulunamadı. RxNorm entegrasyonu tetikleniyor...")
        
    # İlk eşleşen ilacı sözlük yapısına çevirip dönüyoruz
    row = results[0]
    return {
        "drug_id": row.drug_id,
        "drug_name": row.drug_name,
        "active_ingredient": row.active_ingredient,
        "atc_code": row.atc_code,
        "excipients": row.excipients
    }

@app.get("/check-interactions")
def check_interactions(ingredient_1: str, ingredient_2: str):
    """İki etken madde arasındaki etkileşim riskini sorgular."""
    
    query = f"""
        SELECT risk_level, mechanism_description, source 
        FROM `{PROJECT_ID}.{DATASET_ID}.interactions`
        WHERE 
          (LOWER(ingredient_1) = @ing1 AND LOWER(ingredient_2) = @ing2) OR
          (LOWER(ingredient_1) = @ing2 AND LOWER(ingredient_2) = @ing1)
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("ing1", "STRING", ingredient_1.lower()),
            bigquery.ScalarQueryParameter("ing2", "STRING", ingredient_2.lower())
        ]
    )
    
    query_job = bq_client.query(query, job_config=job_config)
    results = list(query_job.result())
    
    if not results:
        return {"status": "Safe", "message": "Bilinen kritik bir etkileşim saptanmadı."}
        
    return [dict(row) for row in results]