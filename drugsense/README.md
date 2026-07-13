# DrugSense - Klinik Karar Destek Sistemi

DrugSense, BigQuery veritabanı altyapısını ve FastAPI framework'ünü kullanan, hekimlerin klinik karar süreçlerini desteklemek amacıyla tasarlanmış bir **ilaç-ilaç etkileşimi** ve **yardımcı madde duyarlılığı** sorgulama sistemidir.

Proje, Türkiye İlaç ve Tıbbi Cihaz Kurumu (TİTCK) onaylı en yaygın Türkçe ilaçların yanı sıra bilimsel **DDInter** etkileşim veri tabanını ve kritik **nöroloji/epilepsi yama kurallarını** bir araya getirir.

---

## 📂 Proje Klasör Yapısı

```text
drugsense/
├── gcp_key.json         # Google Cloud Yetkilendirme Anahtarı
├── main.py              # FastAPI Uygulaması (API Servisi)
├── README.md            # Proje Dokümantasyonu
│
├── data/                # Temizlenmiş ve Hazırlanmış Veri Klasörü
│   ├── ddinter_data.csv                    # DDInter klinik etkileşim verileri
│   ├── titck_drugs.csv                     # TİTCK uyumlu 25 popüler ilaç listesi
│   ├── titck_ingredients.csv               # Bu ilaçların yardımcı maddeleri (Excipients)
│   └── custom_neurology_interactions.csv   # Epilepsiye özel eklenmiş kritik etkileşim kuralları
│
└── scripts/             # Veri Tabanı Kurulum ve Yükleme Betikleri
    ├── setup_bigquery.py                   # BigQuery Şema ve Tablo Oluşturma Betiği
    └── upload_to_bq.py                     # CSV Verilerini BigQuery'ye Yükleme (Mükerrer Önlemeli)
```

---

## 🗄️ Veri Tabanı ve Şema Yapısı

BigQuery üzerinde `drugsense_dataset` veri seti altında aşağıdaki 5 ana tablo bulunmaktadır:

### 1. `drugs` (İlaçlar Tablosu)
Sistemde kayıtlı ilaçların temel bilgilerini içerir.

| Sütun Adı | Veri Tipi | Mod | Açıklama |
| :--- | :--- | :--- | :--- |
| `drug_id` | STRING | REQUIRED | İlacın benzersiz kimliği (Örn: D001) |
| `drug_name` | STRING | REQUIRED | İlacın ticari/piyasa adı (Örn: Parol, Depakin) |
| `source` | STRING | NULLABLE | Verinin alındığı kaynak (Örn: TİTCK) |
| `active_ingredient` | STRING | NULLABLE | İlacın etken maddesi (Örn: Acetaminophen, Valproic Acid) |
| `atc_code` | STRING | NULLABLE | İlacın Anatomik Terapötik Kimyasal (ATC) kodu |

### 2. `ingredients` (Yardımcı Maddeler Tablosu)
İlaçların içerdikleri yardımcı maddeleri (excipients) listeler.

| Sütun Adı | Veri Tipi | Mod | Açıklama |
| :--- | :--- | :--- | :--- |
| `drug_id` | STRING | REQUIRED | İlacın benzersiz kimliği (`drugs` tablosu ile ilişkili) |
| `ingredient_name` | STRING | REQUIRED | Yardımcı maddenin adı (Örn: Laktoz monohidrat, Nişasta) |

### 3. `interactions` (İlaç Etkileşimleri Tablosu)
Etken maddeler arasındaki etkileşim risklerini ve açıklamalarını içerir.

| Sütun Adı | Veri Tipi | Mod | Açıklama |
| :--- | :--- | :--- | :--- |
| `ingredient_1` | STRING | REQUIRED | Etkileşime giren 1. etken madde |
| `ingredient_2` | STRING | REQUIRED | Etkileşime giren 2. etken madde |
| `risk_level` | STRING | REQUIRED | Etkileşim risk seviyesi (Major, Moderate, Minor) |
| `mechanism_description` | STRING | NULLABLE | Etkileşimin fizyolojik/klinik mekanizma açıklaması |
| `source` | STRING | NULLABLE | Etkileşim bilgisinin kaynağı (Örn: DDInter, Custom_Neurology) |

### 4. `patient_allergies` (Hasta Alerji Tablosu)
Hastaların hassas veya alerjik olduğu maddeleri listeler.

| Sütun Adı | Veri Tipi | Mod | Açıklama |
| :--- | :--- | :--- | :--- |
| `patient_id` | STRING | REQUIRED | Hastanın benzersiz kimliği |
| `allergen_name` | STRING | REQUIRED | Alerjenin adı (Etken madde veya yardımcı madde olabilir) |

### 5. `patient_medications` (Hasta Reçete/İlaç Tablosu)
Hastaların aktif olarak kullandığı ilaçları listeler.

| Sütun Adı | Veri Tipi | Mod | Açıklama |
| :--- | :--- | :--- | :--- |
| `patient_id` | STRING | REQUIRED | Hastanın benzersiz kimliği |
| `drug_id` | STRING | REQUIRED | Hastanın kullandığı ilacın ID'si |

---

## 🚀 Çalıştırma Talimatları

### 1. Gereksinimlerin Kurulması
Gerekli Python paketlerini yükleyin:
```bash
pip install fastapi uvicorn google-cloud-bigquery pandas pyarrow db-dtypes
```

### 2. GCP Kimlik Doğrulaması
`gcp_key.json` dosyanızı proje kök dizinine (`drugsense/`) yerleştirin.
> ⚠️ Bu dosya `.gitignore`'a eklenmiştir.

### 3. BigQuery Şemasının Oluşturulması
BigQuery veri kümenizi ve boş tablolarınızı oluşturmak için:
```bash
python scripts/setup_bigquery.py
```

### 4. Verilerin Yüklenmesi (Seeding)
`data/` klasöründeki TİTCK ilaç listesini, yardımcı maddeleri, DDInter etkileşimlerini ve özel nöroloji kurallarını BigQuery'ye yüklemek için seeding betiğini çalıştırın. Bu betik **mükerrer (duplicate) kayıt oluşumunu engeller**:
```bash
python scripts/upload_to_bq.py
```

### 5. API Servisinin Başlatılması
FastAPI sunucusunu lokalde ayağa kaldırmak için:
```bash
uvicorn main:app --reload
```

Sunucu başladıktan sonra aşağıdaki adresten **interaktif Swagger UI**'a erişebilirsiniz:
```
http://127.0.0.1:8000/docs
```

---

## 🛠️ Teknoloji Yığını

| Teknoloji | Kullanım Amacı |
| :--- | :--- |
| **FastAPI** | REST API servisi |
| **Google BigQuery** | Bulut tabanlı veritabanı |
| **Google Cloud Python SDK** | BigQuery istemci kütüphanesi |
| **Pandas** | CSV veri işleme |
| **DDInter Dataset** | Klinik ilaç etkileşim verisi |
| **TİTCK** | Türkiye onaylı ilaç listesi |

