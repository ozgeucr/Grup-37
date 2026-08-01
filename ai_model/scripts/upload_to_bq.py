from google.cloud import bigquery
import pandas as pd

client = bigquery.Client()
table_id = "drugsense-503118.drugsense_dataset.drug_diseases"

# Dosyayı doğrudan pathten okuyoruz (Metin içi virgül karışmasın diye quotechar eklendi)
df = pd.read_csv("drugsense/data/drug_diseases.csv", quotechar='"')

job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()

print("✅ Başarılı! drug_diseases tablosu doğrudan dosyadan BigQuery'ye yüklendi.")