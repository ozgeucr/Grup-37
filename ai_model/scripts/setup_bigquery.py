import os
from google.cloud import bigquery

# Robust GCP Credentials Pathing (works from root or scripts/ folder)
if os.path.exists("gcp_key.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
elif os.path.exists("../gcp_key.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../gcp_key.json"
else:
    print("Hata: gcp_key.json kimlik doğrulama dosyası bulunamadı!")

client = bigquery.Client()

# Kendi GCP Proje ID'ni yaz (GCP konsolunun üst barında yazar)
PROJECT_ID = client.project
DATASET_ID = "drugsense_dataset"
DATASET_REF = f"{PROJECT_ID}.{DATASET_ID}"

def create_schema():
    # Dataset oluşturma
    dataset = bigquery.Dataset(DATASET_REF)
    dataset.location = "EU"  # Verilerin tutulacağı bölge
    try:
        client.create_dataset(dataset, exists_ok=True)
        print(f"Dataset '{DATASET_ID}' hazır.")
    except Exception as e:
        print(f"Dataset oluşturulurken hata: {e}")

    # Tablo Şemaları Tanımları
    tables = {
        "drugs": [
            bigquery.SchemaField("drug_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("drug_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("active_ingredient", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("atc_code", "STRING", mode="NULLABLE"),
        ],
        "ingredients": [
            bigquery.SchemaField("drug_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("ingredient_name", "STRING", mode="REQUIRED"),
        ],
        "interactions": [
            bigquery.SchemaField("ingredient_1", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("ingredient_2", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("risk_level", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("mechanism_description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
        ],
        "patient_allergies": [
            bigquery.SchemaField("patient_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("allergen_name", "STRING", mode="REQUIRED"),
        ],
        "patient_medications": [
            bigquery.SchemaField("patient_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("drug_id", "STRING", mode="REQUIRED"),
        ]
    }

    # Tabloları BigQuery'de oluşturma
    for table_name, schema in tables.items():
        table_ref = f"{DATASET_REF}.{table_name}"
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table, exists_ok=True)
        print(f"Tablo '{table_name}' başarıyla oluşturuldu veya zaten var.")

if __name__ == "__main__":
    create_schema()
