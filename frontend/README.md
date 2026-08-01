# 💊 DrugSense: Yapay Zeka Destekli Klinik Karar Destek ve Reçete Güvenlik Sistemi

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Google-BigQuery-4285F4?style=for-the-badge&logo=googlecloud" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.x-38B2AC?style=for-the-badge&logo=tailwindcss" />
  <img src="https://img.shields.io/badge/AI-Clinical%20Decision%20Support-blueviolet?style=for-the-badge" />
</p>

---

## 📖 DrugSense Hakkında

**DrugSense**, **hekimler, eczacılar, hastalar ve acil sağlık ekipleri** için ilaç güvenliğini ve klinik karar vermeyi geliştirmek amacıyla geliştirilmiş yapay zeka destekli bir **Klinik Karar Destek Sistemi (CDSS)** platformudur.

Platform; **gerçek zamanlı reçete analizi, etken madde bazlı etkileşim tespiti, alerji yönetimi, kronik hastalık kontrolü ve acil tıbbi erişimi** bir araya getirerek parçalanmış sağlık bilgilerini güvenli ve akıllı bir ekosistemde entegre eder.

Geleneksel reçete sistemlerinden farklı olarak DrugSense, her ilacı hastaya ulaşmadan önce **yapay zeka ve kural tabanlı güvenlik mekanizmalarıyla** değerlendirerek sağlık profesyonellerinin önlenebilir tıbbi hataları azaltmasına yardımcı olur.

---

## 🎯 Proje Hedefleri

DrugSense şu amaçları hedefler:

* Reçeteler onaylanmadan önce ilaç hatalarını azaltmak.
* İlaç-İlaç Etkileşimlerini (DDI) önlemek.
* Etken maddelere dayalı alerji risklerini tespit etmek.
* Yinelenen tedavileri (duplikasyon) engellemek.
* Yapay zeka destekli önerilerle reçete güvenliğini artırmak.
* Eczacıların ilaç dağıtımı öncesinde reçete güvenliğini doğrulamasını sağlamak.
* Hastaların dijital olarak yan etki bildirmesine olanak tanımak.
* Acil sağlık ekiplerine **Camı Kır (Break-Glass) Acil Durum Erişim** özelliği ile hayat kurtaran bilgileri sunmak.

---

## ✨ Temel Özellikler

### 🩺 Doktor Portalı
Klinisyen arayüzü akıllı bir reçete yazma ortamı sunar.

* T.C. Kimlik Numarası ile hasta arama
* Hasta profilinin otomatik olarak çekilmesi
* Aktif ilaç geçmişi
* Kronik hastalıkların görselleştirilmesi
* Alerji analizi
* Yapay zeka destekli reçete güvenlik analizi
* Toplu reçete yönetimi
* Çoklu ilaç reçete sepeti
* İlaç etkileşim analizi
* İlaç-besin etkileşim analizi
* Yinelenen tedavi tespiti
* Kritik uyarılar için inisiyatif (override) mekanizması
* Yan etki raporu onay sistemi
* Gerçek zamanlı güvenlik önerileri

### 💊 Eczacı Portalı
İlaç dağıtımı öncesinde doğrulama yapılması için tasarlanmıştır.

* Aktif reçetelerin sorgulanması
* Reçete doğrulama
* Hasta profili incelemesi
* İlaç etkileşim analizi
* Alternatif ilaç önerileri
* Manuel reçetesiz (OTC) ilaç güvenlik kontrolü
* Dağıtım onaylama
* Reçete geçmişi
* Güvenlik önem derecesi görselleştirilmesi
* Yapay zeka destekli eczane iş akışı

### 👤 Hasta Portalı
Hastaların ilaç geçmişlerini güvenli bir şekilde incelemesine ve takip etmesine olanak tanır.

* Kişisel ilaç paneli
* Aktif ilaçlar
* Geçmiş reçeteler
* Kronik hastalıklar
* Alerji geçmişi
* İlaç hatırlatıcıları
* Yapay zeka üretimi ilaç güvenlik bildirimleri
* Yan etki bildirimi
* İlaç güvenlik uyarıları

### 🚨 Camı Kır (Break-Glass) Acil Durum Portalı
DrugSense'in en önemli yeniliklerinden biri **Camı Kır Acil Erişim Sistemi**'dir. Bu modül yalnızca ambulans ekipleri, acil servis hekimleri, paramedikler ve kritik bakım üniteleri için tasarlanmıştır.

* Hayati tehlike arz eden durumlarda, acil sağlık personeli kimlik doğrulamasına gerek kalmaksızın yalnızca hastanın **kritik tıbbi bilgilerine** (ilaç alerjileri, kronik hastalıklar, cerrahi geçmiş) güvenli bir şekilde erişebilir.
* Her acil durum erişimi loglanır, denetlenir, zaman damgası eklenir ve sağlık profesyoneli ile ilişkilendirilerek kalıcı olarak saklanır.

---

## 🤖 Yapay Zeka Özellikleri

DrugSense, ilaçlar reçete edilmeden önce gerçek zamanlı klinik güvenlik analizi gerçekleştirir. Yapay zeka motoru şunları değerlendirir:

* İlaç-İlaç Etkileşimleri (DDI)
* İlaç-Alerji çakışmaları
* İlaç-Hastalık kontrendikasyonları
* Aynı etken maddenin mükerrer kullanımı
* Polifarmasi (çoklu ilaç) riskleri
* Besin etkileşimleri
* Yaşa özel riskler
* Klinik öneriler

| Seviye | Anlamı |
| --- | --- |
| 🟢 GÜVENLİ | Klinik risk tespit edilmedi |
| 🟡 DİKKAT | Orta düzeyde klinik dikkat gerektirir |
| 🔴 KRİTİK | Ciddi etkileşim tespit edildi |

---

## 🧠 Klinik Karar Destek İş Akışı

```text
Doktor ──> Hasta Seçimi ──> İlaç Seçimi ──> DrugSense AI Analizi
                                                    │
                                                    ▼
Güvenlik Kararı <── [ GÜVENLİ / DİKKAT / KRİTİK ] <── İlaç/Alerji/Hastalık Kontrolü
       │
       ▼
Reçete Oluşturuldu


---
## Sistem Mimarisi

                    React Frontend
                           │
                        REST API
                           │
                           ▼
                    FastAPI Backend
                           │
     ┌─────────────────────┼─────────────────────┐
     ▼                     ▼                     ▼
Kimlik Doğrulama     Yapay Zeka Motoru    BigQuery Veritabanı

---
## Teknoliji Yığını:

* Frontend: React, Vite, Tailwind CSS, Lucide React, JavaScript (JSX)
* Backend: FastAPI, Python, REST API
* Veritabanı: Google Cloud BigQuery
* Klinik Servisler: DDInter Veritabanı, TİTCK İlaç Veritabanı, Kural Tabanlı Klinik Motoru
---
## Proje Yapısı

frontend/
├── public/
├── src/
│   ├── assets/
│   ├── pages/
│   │   ├── LandingPage.jsx
│   │   ├── Login.jsx
│   │   ├── Doctor_DashBoard.jsx
│   │   ├── Pharmacist_DashBoard.jsx
│   │   ├── Patient.jsx
│   │   └── EmergencyBreakGlassPortal.jsx
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── package.json
├── vite.config.js
└── README.md

# ⚙️ Kurulum

Aşağıdaki adımları takip ederek DrugSense Frontend uygulamasını yerel ortamınızda çalıştırabilirsiniz.

## 1. Depoyu Klonlayın

```bash
git clone https://github.com/ozgeucr/Grup-37.git
```

## 2. Frontend Dizinine Geçin

```bash
cd Grup-37/frontend
```

## 3. Bağımlılıkları Yükleyin

```bash
npm install
```

## 4. Geliştirme Sunucusunu Başlatın

```bash
npm run dev
```

Uygulama başarıyla başlatıldıktan sonra aşağıdaki adresten erişebilirsiniz:

```text
http://localhost:5173
```

> **Not:** Frontend'in doğru şekilde çalışabilmesi için FastAPI backend servisinin aşağıdaki adreste aktif olarak çalışıyor olması gerekmektedir.

```text
http://localhost:8000
```

---

# 🔒 Güvenlik

DrugSense, modern sağlık bilişimi standartlarına uygun güvenlik mekanizmaları ile geliştirilmiştir.

Uygulamada kullanılan başlıca güvenlik özellikleri:

- 🔐 Rol Tabanlı Erişim Kontrolü (RBAC)
- 👤 Güvenli Kimlik Doğrulama
- 🔒 Oturum (Session) İzolasyonu
- 📝 Reçete Denetim İzi (Audit Trail)
- 🚨 Camı Kır (Break-Glass) Acil Durum Loglama Sistemi
- ✅ Doktor İnisiyatifi (Override) Yetkilendirme Kontrolleri
- 📊 Gerçek Zamanlı Erişim ve İşlem Logları

Tüm kritik işlemler, acil durum erişimleri ve doktor inisiyatifleri sistem tarafından kayıt altına alınarak denetlenebilir şekilde saklanmaktadır.

---

#  DrugSense

<p align="center">

### **Daha Güvenli Reçeteler • Daha Akıllı Kararlar • Daha İyi Sağlık Hizmeti**

*Yapay Zeka Destekli Klinik Karar Destek ve Reçete Güvenlik Sistemi*

</p>