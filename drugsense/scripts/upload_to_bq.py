import os
import pandas as pd
from google.cloud import bigquery

# Robust GCP Credentials Pathing (works from root or scripts/ folder)
if os.path.exists("gcp_key.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
elif os.path.exists("../gcp_key.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../gcp_key.json"
else:
    print("Hata: gcp_key.json kimlik doğrulama dosyası bulunamadı!")

client = bigquery.Client()
PROJECT_ID = client.project
DATASET_ID = "drugsense_dataset"

# Detect if running from scripts directory to adjust data path
data_dir = "data"
if not os.path.exists(data_dir) and os.path.exists("../data"):
    data_dir = "../data"

def upload_all_data():
    print("--- BigQuery Veri Yükleme İşlemi Başladı ---")

    # 1. TİTCK İlaç Listesi (WRITE_TRUNCATE ile temiz yükleme)
    drugs_path = os.path.join(data_dir, "titck_drugs.csv")
    if os.path.exists(drugs_path):
        print("1. TİTCK ilaç listesi yükleniyor...")
        df_drugs = pd.read_csv(drugs_path)
        # BigQuery'ye yükleme
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.drugs"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        print(f"-> {len(df_drugs)} satır ilaç verisi 'drugs' tablosuna yazılıyor (Temiz yükleme)...")
        client.load_table_from_dataframe(df_drugs, table_ref, job_config=job_config).result()
        print(" BAŞARILI: TİTCK ilaç listesi yüklendi.\n")
    else:
        print(" Uyarı: titck_drugs.csv bulunamadı!\n")

    # 2. TİTCK Yardımcı Maddeleri (Excipients - WRITE_TRUNCATE ile temiz yükleme)
    ingredients_path = os.path.join(data_dir, "titck_ingredients.csv")
    if os.path.exists(ingredients_path):
        print("2. İlaç yardımcı maddeleri yükleniyor...")
        df_ingredients = pd.read_csv(ingredients_path)
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.ingredients"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        print(f"-> {len(df_ingredients)} satır yardımcı madde verisi 'ingredients' tablosuna yazılıyor (Temiz yükleme)...")
        client.load_table_from_dataframe(df_ingredients, table_ref, job_config=job_config).result()
        print(" BAŞARILI: Yardımcı madde verileri yüklendi.\n")
    else:
        print(" Uyarı: titck_ingredients.csv bulunamadı!\n")

    # 3. DDInter Etkileşim Verileri + Özel Nöroloji Yaması (BİRLEŞTİRİLİP tek seferde WRITE_TRUNCATE ile yükleniyor)
    ddinter_path = os.path.join(data_dir, "ddinter_data.csv")
    neurology_path = os.path.join(data_dir, "custom_neurology_interactions.csv")
    
    df_all_interactions = pd.DataFrame()
    
    # DDInter'ı yükle
    if os.path.exists(ddinter_path):
        print("3. DDInter etkileşim verileri okunuyor...")
        df_ddinter = pd.read_csv(ddinter_path)
        
        rename_mapping = {
            'Drug_A': 'ingredient_1',
            'Drug_B': 'ingredient_2',
            'Level': 'risk_level'
        }
        df_ddinter = df_ddinter.rename(columns=rename_mapping)
        df_ddinter['source'] = 'DDInter'
        
        expected_columns = ['ingredient_1', 'ingredient_2', 'risk_level', 'mechanism_description', 'source']
        df_ddinter = df_ddinter.reindex(columns=expected_columns)
        df_ddinter['mechanism_description'] = df_ddinter['mechanism_description'].fillna('Açıklama belirtilmemiş.')
        
        df_all_interactions = pd.concat([df_all_interactions, df_ddinter], ignore_index=True)
    else:
        print(" Uyarı: ddinter_data.csv bulunamadı!")

    # Özel Nöroloji kurallarını yükle
    if os.path.exists(neurology_path):
        print("4. Özel Nöroloji/Epilepsi etkileşim kuralları okunuyor...")
        df_neuro = pd.read_csv(neurology_path)
        df_all_interactions = pd.concat([df_all_interactions, df_neuro], ignore_index=True)
    else:
        print(" Uyarı: custom_neurology_interactions.csv bulunamadı!")

    if not df_all_interactions.empty:
        # Mükerrer satırları engellemek için duplicate kontrolü (etken madde kombinasyonlarına göre)
        print("-> Mükerrer (duplicate) kayıtlar eleniyor...")
        initial_len = len(df_all_interactions)
        
        # A-B ve B-A şeklindeki çiftleri aynı kabul edip tekilleştirmek için etken maddeleri sıralayarak anahtar yapıyoruz
        sorted_ingredients = df_all_interactions.apply(
            lambda row: tuple(sorted([str(row['ingredient_1']).lower(), str(row['ingredient_2']).lower()])), 
            axis=1
        )
        df_all_interactions['temp_key'] = sorted_ingredients
        
        # Mükerrer çiftleri siliyoruz (özel nöroloji kurallarının DDInter'ı ezmesi için son eklenen 'last' kaydı tutuyoruz)
        df_all_interactions = df_all_interactions.drop_duplicates(subset=['temp_key'], keep='last')
        df_all_interactions = df_all_interactions.drop(columns=['temp_key'])
        
        final_len = len(df_all_interactions)
        print(f"-> Toplam {initial_len} satırdan {initial_len - final_len} mükerrer kayıt temizlendi. Kalan: {final_len} satır.")

        # interactions tablosuna WRITE_TRUNCATE ile yükleme
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.interactions"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        print(f"-> interactions tablosuna temiz yazma yapılıyor...")
        client.load_table_from_dataframe(df_all_interactions, table_ref, job_config=job_config).result()
        print(" BAŞARILI: Tüm etkileşim verileri yüklendi.\n")
    else:
        print(" Hata: Yüklenecek etkileşim verisi bulunamadı!\n")

    print("--- Tüm Veri Yükleme İşlemleri Tamamlandı ---")

if __name__ == "__main__":
    upload_all_data()
