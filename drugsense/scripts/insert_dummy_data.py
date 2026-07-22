import os
from datetime import datetime, timezone
from google.cloud import bigquery

# Kimlik doğrulama
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

client = bigquery.Client()
PROJECT_ID = client.project
DATASET_ID = "drugsense_dataset"

def insert_dummy_data():
    # Zaman damgaları için (BigQuery JSON insert'te ISO string sever)
    now = datetime.now(timezone.utc).isoformat()

    # 1. KULLANICILAR (Farklı senaryolar için çeşitli hastalar ve personeller)
    users_data = [
        {"user_id": "U001", "tc_no": "11111111111", "full_name": "Dr. Ayşe Yılmaz", "role": "DOCTOR", "password_hash": "hash123", "is_active": True},
        {"user_id": "U002", "tc_no": "22222222222", "full_name": "Ecz. Ali Kaya", "role": "PHARMACIST", "password_hash": "hash123", "is_active": True},
        {"user_id": "U004", "tc_no": "44444444444", "full_name": "Paramedik Fatma Şahin", "role": "PARAMEDIC", "password_hash": "hash123", "is_active": True},
        # Hastalar
        {"user_id": "U003", "tc_no": "12345678901", "full_name": "Hasta Ahmet Demir", "role": "PATIENT", "password_hash": "hash123", "is_active": True}, # Epilepsi hastası
        {"user_id": "U005", "tc_no": "98765432109", "full_name": "Hasta Elif Yücel", "role": "PATIENT", "password_hash": "hash123", "is_active": True}, # Ülser hastası
        {"user_id": "U006", "tc_no": "55555555555", "full_name": "Hasta Yaşar Gök", "role": "PATIENT", "password_hash": "hash123", "is_active": True}  # Yaşlı/Polifarmasi adayı
    ]
    
    # 2. HASTALIKLAR (Kronik durum kontrolleri için)
    diseases_data = [
        {"patient_tc_no": "12345678901", "icd10_code": "G40", "disease_name": "Epilepsi", "diagnosed_date": "2020-05-10"},
        {"patient_tc_no": "12345678901", "icd10_code": "J45", "disease_name": "Astım", "diagnosed_date": "2018-11-22"},
        {"patient_tc_no": "98765432109", "icd10_code": "K27", "disease_name": "Peptik Ülser", "diagnosed_date": "2022-01-15"},
        {"patient_tc_no": "55555555555", "icd10_code": "I10", "disease_name": "Hipertansiyon", "diagnosed_date": "2015-08-30"}
    ]

    # 3. HASTA BEYANLI YAN ETKİLER (Doktor onayı bekleyen ve onaylanmış kayıtlar)
    reported_effects_data = [
        {"report_id": "REP001", "patient_tc_no": "98765432109", "drug_name": "Aspirin", "symptom": "Şiddetli mide ağrısı ve yanma", "verification_status": "PENDING", "reported_at": now},
        {"report_id": "REP002", "patient_tc_no": "55555555555", "drug_name": "Parol", "symptom": "Ciltte döküntü ve kızarıklık", "verification_status": "VERIFIED", "reported_at": now}
    ]

    # 4. REÇETELER (Bekleyenler, Teslim Edilenler ve İnisiyatif Alınanlar)
    prescriptions_data = [
        {"prescription_id": "RX001", "doctor_tc_no": "11111111111", "patient_tc_no": "12345678901", "drug_name": "Depakin", "status": "DISPENSED", "override_reason": None, "created_at": now},
        {"prescription_id": "RX002", "doctor_tc_no": "11111111111", "patient_tc_no": "98765432109", "drug_name": "Brufen", "status": "PENDING", "override_reason": "Hasta ülser ama mide koruyucu ile birlikte yazıldı, takip edilecek.", "created_at": now}
    ]

    # 5. DENETİM LOGLARI (Özellikle Acil Durum / Break-Glass erişimi için)
    audit_logs_data = [
        {"log_id": "LOG001", "actor_tc_no": "11111111111", "action_type": "VIEW_PROFILE", "target_tc_no": "12345678901", "timestamp": now, "details": "Rutin poliklinik muayenesi."},
        {"log_id": "LOG002", "actor_tc_no": "44444444444", "action_type": "EMERGENCY_ACCESS", "target_tc_no": "12345678901", "timestamp": now, "details": "Nöbet geçiren hastaya ambulans müdahalesi (Camı Kır)."}
    ]

    # Tüm tabloları bir sözlükte topluyoruz
    tables_to_insert = {
        "users": users_data,
        "patient_diseases": diseases_data,
        "patient_reported_effects": reported_effects_data,
        "prescriptions": prescriptions_data,
        "audit_logs": audit_logs_data
    }

    print("Veriler BigQuery'ye aktarılıyor, lütfen bekleyin...")
    
    for table_name, rows in tables_to_insert.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        
        try:
            table = client.get_table(table_id)
            errors = client.insert_rows_json(table, rows)
            
            if not errors:
                print(f"✅ {len(rows)} satır veri '{table_name}' tablosuna başarıyla eklendi.")
            else:
                print(f"❌ '{table_name}' tablosuna veri eklenirken hata: {errors}")
        except Exception as e:
            print(f"⚠️ '{table_name}' bulunamadı veya erişilemedi: {e}")

if __name__ == "__main__":
    insert_dummy_data()