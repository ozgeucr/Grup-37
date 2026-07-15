import os
from google.cloud import bigquery

# Ortam değişkeni yüklendi mi?
print("Anahtar yolu:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

# İstemci oluşturmayı dene
try:
    client = bigquery.Client()
    print("✅ Başarılı! GCP'ye bağlandık.")
except Exception as e:
    print(f"❌ Bağlantı hatası: {e}")