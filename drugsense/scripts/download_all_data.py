import os
from google.cloud import bigquery
from drugsense.database import bq_client

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
EXPORT_DIR = "drugsense/data"

# Klasör yoksa oluşturalım
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

print("BigQuery'deki tüm tablolar taranıyor...")
tables = bq_client.list_tables(DATASET_ID)

for table in tables:
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
    print(f"İndiriliyor: {table.table_id}...")
    
    # Veriyi çekip DataFrame'e çeviriyoruz
    query = f"SELECT * FROM `{table_id}`"
    df = bq_client.query(query).to_dataframe()
    
    # CSV olarak data klasörüne kaydediyoruz
    file_path = f"{EXPORT_DIR}/{table.table_id}.csv"
    df.to_csv(file_path, index=False)
    print(f"  -> Başarıyla kaydedildi: {file_path}")

print("\nTüm veri setleri bilgisayarına indirildi!")