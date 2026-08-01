import pandas as pd
from google.cloud import bigquery
from drugsense.database import bq_client  

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"

# CSV'yi oku
# CSV'yi oku
df = pd.read_csv("drugsense/data/drug_foods.csv")


# Tablo ID'sini belirle
table_id = f"{PROJECT_ID}.{DATASET_ID}.drug_foods"

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",  
)

# Yüklemeyi başlat
print("BigQuery'ye yükleniyor...")
job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()  

print(f"Harika! {job.output_rows} satır {table_id} tablosuna başarıyla yüklendi.")