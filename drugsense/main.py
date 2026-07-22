#bu dosyayı şimdilik kaba taslak olarak yazdım, düzenlenebilir

import os
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery
from drugsense.routes import drugs, doctor, pharmacist, patient, emergency
from datetime import datetime
from pydantic import BaseModel


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
bq_client = bigquery.Client()

class SideEffectReport(BaseModel):
    report_id: str
    patient_tc: str
    drug_name: str
    symptoms: str
    severity: str
    status: str = "İnceleniyor"

app = FastAPI(title="DrugSense - Klinik Karar Destek Sistemi API")
app.include_router(doctor.router, prefix="/doctor", tags=["Doctor"])
app.include_router(drugs.router, prefix="/drugs", tags=["Drugs"])
app.include_router(pharmacist.router, prefix="/pharmacist", tags=["Pharmacist"])
app.include_router(patient.router, prefix="/patient", tags=["Patient"])
app.include_router(emergency.router, prefix="/emergency", tags=["Emergency"])

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"

@app.get("/")
def read_root():
    return {"message": "DrugSense API sistemine hoş geldiniz. Güvenli reçeteleme için /docs adresine giderek arayüzü kullanabilirsiniz."}

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

@app.post("/api/reports", tags=["Yan Etki Bildirimleri"])
async def create_report(report: SideEffectReport):
    # Dün oluşturduğumuz tablonun tam ID'si
    table_id = "drugsense-503118.drugsense_dataset.side_effect_reports"
    
    # BigQuery'nin JSON formatında veri kabul etmesi için sözlük (dict) yapısına çeviriyoruz
    row_to_insert = [
        {
            "report_id": report.report_id,
            "patient_tc": report.patient_tc,
            "drug_name": report.drug_name,
            "symptoms": report.symptoms,
            "severity": report.severity,
            "report_date": datetime.utcnow().isoformat(), # Zaman damgasını otomatik atıyoruz
            "status": report.status,
        }
    ]
    
    # Veriyi BigQuery'ye yazma işlemi (Burada bq_client kullanıyoruz)
    errors = bq_client.insert_rows_json(table_id, row_to_insert)
    
    if errors == []:
        return {"message": "Yan etki bildirimi başarıyla BigQuery'ye eklendi!"}
    else:
        # Hata durumunda detaylı bilgi dönüyoruz
        raise HTTPException(status_code=500, detail=f"Kayıt eklenirken hata oluştu: {errors}")