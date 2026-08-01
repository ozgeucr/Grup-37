import os
from google.cloud import bigquery

# Kimlik doğrulama dosyanın yolunu kendi bilgisayarına göre ayarla
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

client = bigquery.Client()
PROJECT_ID = client.project
DATASET_ID = "drugsense_dataset"

# Tablo isimleri ve şemaları
tables_to_create = {
    "users": [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tc_no", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("full_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("role", "STRING", mode="REQUIRED"), # DOCTOR, PHARMACIST, PATIENT, PARAMEDIC
        bigquery.SchemaField("password_hash", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED")
    ],
    "audit_logs": [
        bigquery.SchemaField("log_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("actor_tc_no", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("action_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("target_tc_no", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("details", "STRING", mode="NULLABLE")
    ],
    "prescriptions": [
        bigquery.SchemaField("prescription_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("doctor_tc_no", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("patient_tc_no", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("drug_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"), # PENDING, DISPENSED
        bigquery.SchemaField("override_reason", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
    ],
    "patient_reported_effects": [
        bigquery.SchemaField("report_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("patient_tc_no", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("drug_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("symptom", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("verification_status", "STRING", mode="REQUIRED"), # PENDING, VERIFIED
        bigquery.SchemaField("reported_at", "TIMESTAMP", mode="REQUIRED")
    ],
    "patient_diseases": [
        bigquery.SchemaField("patient_tc_no", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("icd10_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("disease_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("diagnosed_date", "DATE", mode="NULLABLE")
    ]
}

def create_tables():
    dataset_ref = client.dataset(DATASET_ID)
    
    for table_name, schema in tables_to_create.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            # Tablo zaten varsa hata fırlatmaz, yoksa oluşturur
            client.create_table(table, exists_ok=True)
            print(f"✅ {table_name} tablosu başarıyla oluşturuldu veya zaten mevcut.")
        except Exception as e:
            print(f"❌ {table_name} oluşturulurken hata: {e}")

if __name__ == "__main__":
    create_tables()