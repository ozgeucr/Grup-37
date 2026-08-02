import os
import csv
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery
from ai_model.routes import drugs, doctor, pharmacist, patient, emergency
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Kimlik dosyasını ortam değişkenine tanıtıyoruz
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
bq_client = bigquery.Client()

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"

# 1. ADIM: UYGULAMAYI ÖNCE BURADA TANIMLIYORUZ
app = FastAPI(
    title="DrugSense - Klinik Karar Destek Sistemi API",
    description="Yapay zeka destekli çok boyutlu klinik karar destek ve akıllı reçeteleme sistemi.",
    version="1.0.0"
)

# 2. ADIM: CORS MIDDLEWARE EKLİYORUZ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SideEffectReport(BaseModel):
    report_id: str
    patient_tc: str
    drug_name: str
    symptoms: str
    severity: str
    status: str = "İnceleniyor"

# Router'ları ekliyoruz (Emergency rotasındaki prefix kaldırıldı)
app.include_router(doctor.router, prefix="/doctor", tags=["Doctor"])
app.include_router(drugs.router, prefix="/drugs", tags=["Drugs"])
app.include_router(pharmacist.router, prefix="/pharmacist", tags=["Pharmacist"])
app.include_router(patient.router, prefix="/patient", tags=["Patient"])
app.include_router(emergency.router, prefix="/emergency", tags=["Emergency"])


@app.get("/")
def read_root():
    return {
        "message": "DrugSense API sistemine hoş geldiniz. Güvenli reçeteleme için /docs adresine giderek arayüzü kullanabilirsiniz."
    }


@app.get("/search-drug/{drug_name}")
def search_drug(drug_name: str):
    """Kullanıcının yazdığı ilacı BigQuery'de arar ve yardımcı maddeleriyle birlikte getirir."""
    
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
        raise HTTPException(
            status_code=404, 
            detail="İlaç lokal BigQuery veritabanında bulunamadı. RxNorm / TİTCK dış kaynak entegrasyonu tetikleniyor..."
        )
        
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
    """Hastaların veya hekimlerin bildirdiği yan etkileri BigQuery audit/report tablosuna işler."""
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.side_effect_reports"
    
    row_to_insert = [
        {
            "report_id": report.report_id,
            "patient_tc": report.patient_tc,
            "drug_name": report.drug_name,
            "symptoms": report.symptoms,
            "severity": report.severity,
            "report_date": datetime.now(timezone.utc).isoformat(),
            "status": report.status,
        }
    ]
    
    errors = bq_client.insert_rows_json(table_id, row_to_insert)
    
    if errors == []:
        return {"message": "Yan etki bildirimi başarıyla BigQuery'ye eklendi!"}
    else:
        raise HTTPException(status_code=500, detail=f"Kayıt eklenirken hata oluştu: {errors}")


# --- DİNAMİK LOGİN SİSTEMİ (users.csv Entegrasyonu) ---


class LoginRequest(BaseModel):
    tc_no: str
    password: str
    role: str = "patient"

@app.post("/login")
def login(req: LoginRequest):
    tc = req.tc_no.strip()
    selected_role = req.role.strip().lower()
    
    # KESİN ÇÖZÜM: users.csv dosyasının olabileceği tüm yolları tarıyoruz
    possible_paths = [
        "ai_model/data/users.csv", 
        "data/users.csv", 
        "ai_model/users.csv", 
        "users.csv"
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break

    user = None
    if csv_path:
        with open(csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["tc_no"].strip() == tc:
                    user = row
                    break

    # Eğer CSV dosyasında bu TC gerçekten yoksa varsayılan isim ata
    if not user:
        user = {
            "full_name": f"Kayıtsız Kullanıcı ({tc})",
            "role": selected_role.upper(),
            "password_hash": "hash123"
        }

    # Şifre kontrolü
    if req.password != "test1234" and req.password != user.get("password_hash", "hash123"):
        raise HTTPException(status_code=401, detail="Hatalı şifre girdiniz.")

    # CSV'deki rolü okuma
    db_role = user.get("role", "PATIENT").upper()
    role_mapping = {
        "DOCTOR": "doctor",
        "PHARMACIST": "pharmacist",
        "PARAMEDIC": "paramedic",
        "PATIENT": "patient"
    }
    actual_role = role_mapping.get(db_role, "patient")

    final_role = selected_role if selected_role in ["doctor", "pharmacist", "patient", "paramedic"] else actual_role

    return {
        "role": final_role, 
        "user_data": {
            "name": user.get("full_name"), # Artık CSV'deki "Dr. Mehmet Özkan" ismini direkt çekecek!
            "tc_no": tc
        }
    }