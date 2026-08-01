# DrugSense — AI Model Dokümantasyonu

## Genel Bakış

DrugSense, etken madde bazlı ilaç-ilaç etkileşimi (DDI) analizi yapan bir Klinik Karar Destek Sistemidir. Bu dokümantasyon AI modelinin nasıl kullanılacağını açıklar.

---

## Hızlı Kullanım

    from drugsense.api.predict import predict_interaction
    result = predict_interaction("Ibuprofen", "Warfarin")
    print(result)

### Örnek Çıktı

    {
        "drug_a": "Ibuprofen",
        "drug_b": "Warfarin",
        "risk_level": "Major",
        "confidence": "54.2%",
        "mechanism": "DDInter veritabanından ML modeli ile tahmin edildi.",
        "atc_a": "N02AJ",
        "atc_b": "B01AA",
        "method": "ML Model",
        "color": "red"
    }

---

## Kurulum

    pip install -r drugsense/api/requirements.txt

---

## Model Mimarisi

### Hibrit Tahmin Sistemi

Model iki katmanlı bir yapıya sahiptir:

- Yeni ilaç çifti geldiğinde önce kural tablosuna bakılır
- Kural tablosunda varsa: %100 güven, mekanizma açıklamasıyla döner
- Kural tablosunda yoksa: ML Model (XGBoost) tahmin yapar

### Kullanılan Model

- Algoritma: XGBoost
- Accuracy: %91
- Macro F1: 0.77
- Overfitting Farkı: 0.025

### Model Parametreleri

| Parametre | Değer |
|---|---|
| n_estimators | 300 |
| max_depth | 6 |
| learning_rate | 0.1 |
| subsample | 0.8 |
| colsample_bytree | 0.8 |
| min_child_weight | 3 |
| reg_alpha | 0.5 |
| reg_lambda | 1.0 |

---

## Performans Metrikleri

| Sınıf | Precision | Recall | F1 |
|---|---|---|---|
| Major | 0.89 | 0.92 | 0.91 |
| Minor | 0.47 | 0.47 | 0.47 |
| Moderate | 0.95 | 0.93 | 0.94 |
| Genel | 0.91 | 0.91 | 0.91 |

---

## Özellikler (Features)

Model 34 özellik kullanmaktadır:

| Özellik Grubu | Özellikler | Açıklama |
|---|---|---|
| Temel Encoding | drug_a_enc, drug_b_enc | İlaç isimleri sayıya çevrildi |
| ID Numaraları | id_a_num, id_b_num | DDInter ID numaraları |
| Graf Özellikleri | degree_a, degree_b, major_rate_a, major_rate_b | İlaç ağı istatistikleri |
| ATC Kodu | atc_a_enc, atc_b_enc | İlaç kategorisi (RxNorm API) |
| İsim Son Ekleri | 24 adet binary özellik | -azole, -mab, -statin vb. |

---

## Veri Kaynakları

| Kaynak | Kullanım | Kayıt Sayısı |
|---|---|---|
| DDInter 1.0 | Ana etkileşim verisi | 12.024 |
| RxNorm API | İlaç ATC kodu | 1.464 ilaç |
| TİTCK | Türkiye ilaçları | 25 ilaç |
| Custom Neurology | Nöroloji etkileşimleri | 4 kayıt |

---

## API Dönüş Değerleri

| Alan | Tip | Açıklama |
|---|---|---|
| drug_a | string | Birinci ilaç adı |
| drug_b | string | İkinci ilaç adı |
| risk_level | string | Major / Moderate / Minor |
| confidence | string | Tahmin güveni |
| mechanism | string | Etkileşim mekanizması |
| atc_a | string | Birinci ilacın ATC kodu |
| atc_b | string | İkinci ilacın ATC kodu |
| method | string | Kural Tabanlı / ML Model |
| color | string | red / orange / green |

---

## Demo Senaryoları

| İlaç A | İlaç B | Risk | Güven | Yöntem |
|---|---|---|---|---|
| Valproic Acid | Carbamazepine | Major | %100 | Kural Tabanlı |
| Ibuprofen | Warfarin | Major | %54 | ML Model |
| Paracetamol | Codeine | Minor | %61 | ML Model |
| Metformin | Insulin | Moderate | %97 | ML Model |

---

## Dosya Yapısı

    drugsense/
    api/
        predict.py
        requirements.txt
    model/
        drugsense_final_model.pkl
        le_drug_a.pkl
        le_drug_b.pkl
        le_level.pkl
        le_atc.pkl
        atc_map.pkl
        drug_interaction_count.pkl
        drug_major_count.pkl
        interaction_rules.pkl
        model_info.json
    data/
        (veri dosyaları)

---

## Geliştirme Notları

- Minor sınıfı test setinde sadece 57 kayıtla temsil edildiği için F1 skoru düşük görünmektedir.
- Model etken madde isimleriyle çalışmaktadır. Türkçe marka isimleri için önce etken maddeye çevrilmesi gerekmektedir.
- Kural tabanlı sistem önceliklidir — interactions tablosuna yeni kayıt eklendikçe sistem otomatik olarak güncellenir.
