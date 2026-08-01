import os
from google.cloud import bigquery

# database.py dosyası drugsense/ klasöründe, gcp_key.json ise bir üst klasörde (Grup-37)
# Bu yüzden dinamik olarak anahtarı bulmasını sağlıyoruz
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_PATH = os.path.join(BASE_DIR, "gcp_key.json")

# Google Cloud'a kimlik dosyamızın yerini gösteriyoruz
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

# Tüm uygulamada kullanılacak olan o meşhur bq_client değişkenimiz
try:
    bq_client = bigquery.Client()
    print("✅ BigQuery istemcisi (bq_client) başarıyla başlatıldı!")
except Exception as e:
    print(f"❌ BigQuery bağlantı hatası: {e}")
    bq_client = None