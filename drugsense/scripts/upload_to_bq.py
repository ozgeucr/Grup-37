import os
from google.cloud import bigquery

# Ana dizin
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CSV dosyalarının bulunduğu klasör
DATA_DIR = os.path.join(BASE_DIR, "drugsense", "data")

# Google Cloud kimlik bilgileri
KEY_PATH = os.path.join(BASE_DIR, "gcp_key.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

# BigQuery istemcisi
client = bigquery.Client()

# Yüklenecek dosyalar ve karşılık gelen BigQuery tabloları
files = {
    "ddinter_data.csv": "ddinter_interactions",
    "patients.csv": "patients",
    "patient_allergies.csv": "patient_allergies",
    "patient_medications.csv": "patient_medications",
    # İstersen bunları da açabilirsin:
    # "custom_neurology.csv": "custom_neurology",
    # "titck_drugs.csv": "titck_drugs",
    # "titck_ingredients.csv": "titck_ingredients",
}

for filename, table_name in files.items():

    file_path = os.path.join(DATA_DIR, filename)
    table_id = f"{client.project}.drugsense_dataset.{table_name}"

    if not os.path.exists(file_path):
        print(f"❌ Dosya bulunamadı: {file_path}")
        continue

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"🚀 {filename} yükleniyor...")

    try:
        with open(file_path, "rb") as source_file:
            job = client.load_table_from_file(
                source_file,
                table_id,
                job_config=job_config,
            )

        job.result()

        print(f"✅ {table_name} tablosu başarıyla yüklendi.")

    except Exception as e:
        print(f"❌ {table_name} yüklenirken hata oluştu:")
        print(e)

print("\n🎉 Tüm yükleme işlemleri tamamlandı.")