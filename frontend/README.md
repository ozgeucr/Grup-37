#  DrugSense Frontend - Klinik Karar Destek & Acil Erişim Portalı

DrugSense Frontend, **React**, **Vite** ve **Tailwind CSS** teknolojileri kullanılarak geliştirilmiş modern bir web uygulamasıdır. Sistem; hekimlerin, eczacıların, hastaların ve acil sağlık personelinin güvenli bir şekilde sisteme erişmesini sağlayan rol tabanlı kullanıcı arayüzünü sunmaktadır.

Frontend uygulaması, FastAPI tabanlı backend servisleri ile entegre çalışarak klinik karar destek süreçlerini, ilaç analizlerini ve acil durum erişim mekanizmasını kullanıcı dostu bir arayüz üzerinden yönetmektedir.

---

#  Özellikler

##  Doktor Paneli

- Güvenli reçete oluşturma
- Yapay zekâ destekli ilaç analizi
- İlaç-ilaç etkileşim kontrolü
- Gıda-ilaç etkileşim analizi
- Alerji kontrolü
- Kronik hastalık kontrolü
- Pediatrik ve geriatrik risk analizi
- Aynı etken madde kontrolü
- Polifarmasi analizi
- Akıllı reçete önerileri

---

##  Acil Erişim (Break Glass)

Paramediklerin kritik durumlarda hastaya saniyeler içerisinde erişebilmesini sağlayan modüldür.

Özellikleri:

- Camı Kır (Break Glass) mekanizması
- Kronik hastalıkların görüntülenmesi
- Hasta alerjilerinin görüntülenmesi
- Geçmiş operasyon bilgilerinin gösterilmesi
- Yapılan erişimlerin Audit Log sistemine kaydedilmesi
- Acil erişim bildirimlerinin oluşturulması

---

##  Eczacı Paneli

- Reçete görüntüleme
- Güvenlik analiz sonuçlarını inceleme
- İlaç etkileşim raporları
- Reçete doğrulama
- Klinik uyarı ekranları

---

##  Hasta Paneli

- Aktif ilaçlarını görüntüleme
- Reçete geçmişi
- Yan etki bildirme
- Kişisel sağlık geçmişi
- İlaç kullanım bilgileri

---

##  Rol Tabanlı Giriş Sistemi

Sistem aşağıdaki kullanıcı rollerini desteklemektedir.

- Doktor
- Eczacı
- Hasta
- Paramedik

Her kullanıcı yalnızca kendi yetkisine ait ekranlara erişebilir.

---

#  Kullanılan Teknolojiler

- React
- Vite
- Tailwind CSS
- React Router
- Axios
- JavaScript (ES6+)

---

#  Proje Yapısı

```text
frontend/
│
├── public/
│
├── src/
│   │
│   ├── assets/
│   │
│   ├── components/
│   │
│   ├── pages/
│   │   ├── Doctor_DashBoard.jsx
│   │   ├── EmergencyBreakGlassPage.jsx
│   │   ├── LandingPage.jsx
│   │   ├── Login.jsx
│   │   ├── Patient.jsx
│   │   └── Pharmacist_DashBoard.jsx
│   │
│   ├── services/
│   │
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
│
├── package.json
├── vite.config.js
└── README.md
```

---

#  Kurulum

## 1. Depoyu Klonlayın

```bash
git clone https://github.com/ozgeucr/Grup-37.git
```

---

## 2. Frontend Klasörüne Girin

```bash
cd Grup-37/frontend
```

---

## 3. Bağımlılıkları Kurun

```bash
npm install
```

---

## 4. Geliştirme Sunucusunu Başlatın

```bash
npm run dev
```

Uygulama varsayılan olarak aşağıdaki adreste çalışacaktır:

```text
http://drugsense.local:5173/
```

---

#  Backend Entegrasyonu

Frontend uygulaması FastAPI backend'i ile haberleşmektedir.

Backend sunucusunun aşağıdaki adreste çalışıyor olması gerekmektedir:

```text
http://localhost:8000
```

---

#  Kullanılan API Endpointleri

## Doktor Analizi

```http
POST /doctor/prescribe-and-analyze
```

Yapay zekâ destekli reçete analizi gerçekleştirir.

---

## Acil Erişim (Break Glass)

```http
POST /emergency/break-glass
```

Paramediğin hastanın kritik sağlık bilgilerine kontrollü erişimini sağlar.

---

## Hasta Bilgileri

```http
GET /patient/...
```

Hasta bilgileri ve ilaç geçmişi görüntülenir.

---

## Eczacı İşlemleri

```http
POST /pharmacist/...
```

Reçete doğrulama ve ilaç güvenliği analizleri gerçekleştirilir.

---

#  Arayüz Özellikleri

- Responsive tasarım
- Modern kullanıcı deneyimi
- Material UI ikonları
- Tailwind CSS bileşenleri
- Rol bazlı yönlendirme
- Kullanıcı dostu dashboard yapısı
- Dinamik API entegrasyonu

---

#  Break Glass Modülü

Bu modül yalnızca **Paramedik** rolüne sahip kullanıcılar tarafından kullanılabilir.

Başarılı bir erişim sonrasında sistem aşağıdaki bilgileri getirir:

- Kronik hastalıklar
- Hasta alerjileri
- Geçmiş operasyonlar
- Acil durum uyarıları

Ayrıca;

- Audit Log kaydı oluşturulur.
- Acil erişim bildirimi oluşturulur.
- Tüm erişimler kayıt altına alınır.

---

#  Notlar

- Backend çalışmadan frontend tam olarak işlevsel olmayacaktır.
- API adresi gerektiğinde `services` klasöründen değiştirilebilir.
- Tüm kullanıcı girişleri rol bazlı doğrulanmaktadır.
- FastAPI backend ile JSON tabanlı REST API üzerinden haberleşmektedir.

---

# 📄 Lisans

Bu proje yalnızca eğitim ve akademik amaçlarla geliştirilmiştir.
