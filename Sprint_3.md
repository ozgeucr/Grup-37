# Sprint 3

* **Backlog Düzeni ve Story Seçimleri:** Bir önceki sprintte oluşturulan teknik altyapı ve tamamlanan veri ön işleme çalışmalarının ardından Sprint 3 boyunca önceliğimiz; **uçtan uca (end-to-end) sistem entegrasyonu**, **yapay zeka modelinin eğitimi ve sisteme entegre edilmesi**, **frontend geliştirme sürecinin tamamlanması** ve **ürünün final hale getirilmesi** olmuştur. Bu sprint kapsamında DDInter veri seti kullanılarak XGBoost tabanlı ilaç etkileşim modeli başarıyla eğitilmiş ve FastAPI backend mimarisine entegre edilmiştir. React, Vite ve TailwindCSS kullanılarak Doktor, Eczacı, Hasta ve Paramedik panelleri geliştirilmiş; sistemin kritik özelliklerinden biri olan **Break-Glass (Acil Erişim)** modülü tamamlanarak paramediklerin acil durumlarda hastaların kronik hastalık, alerji ve operasyon bilgilerine güvenli şekilde erişmesi sağlanmıştır. Bunun yanında frontend ile backend arasındaki tüm API entegrasyonları tamamlanmış ve sistem uçtan uca çalışır duruma getirilmiştir.

<img width="938" height="705" alt="Ekran Resmi 2026-08-02 18 32 57" src="https://github.com/user-attachments/assets/c0034b48-bc5c-4e9c-9401-249f3a112d0f" />

<img width="845" height="473" alt="Ekran Resmi 2026-08-02 18 31 37" src="https://github.com/user-attachments/assets/c161afc3-1570-47d5-94d9-0584a4ad69f7" />


* **Scrum ve Asenkron İletişim Süreci:** Sprint boyunca yapay zeka modeli, backend servisleri ve frontend arayüzlerinin tek bir sistem altında birleştirilmesi sürecinde takım içi iletişim en yoğun seviyede gerçekleşmiştir. Özellikle API yönlendirme problemleri (404 Not Found), veri doğrulama hataları (422 Unprocessable Entity), BigQuery veri tipi uyuşmazlıkları (`STRING`, `INT64`, `DATE`) ve SQL sorgularındaki tip dönüşümleri asenkron iletişim ve eşli programlama (pair programming) oturumları sayesinde kısa sürede çözülmüştür. Geliştirme süreci boyunca karşılaşılan engeller düzenli olarak paylaşılmış, gerekli revizyonlar hızlı şekilde uygulanmış ve sistem entegrasyonu başarıyla tamamlanmıştır.

*(Takım iletişimine dair kesitler, model eğitim süreçleri, entegrasyon çalışmaları, test çıktıları ve geliştirme kanıtlarına **[Sprint 3 İletişim, Model Eğitimi, Entegrasyon ve Kanıtlar (Artifacts)](https://github.com/ozgeucr/Grup-37/blob/main/Sprint_3_Attachments/README.md)** sayfasından ulaşabilirsiniz.)*

---

## Sprint Board Update

Sprint Board'umuzun Sprint 3 kapanış durumu aşağıdaki gibidir.

Önceliklendirilen görevler takım kapasitesine göre tamamlanmıştır.

### Tamamlanan Görevler (Done)

* DDInter veri seti kullanılarak XGBoost tabanlı yapay zeka modelinin eğitilmesi ve optimize edilmesi.
* Yapay zeka modelinin FastAPI backend altyapısına entegre edilmesi.
* Model tahminleri için önbellekleme (cache) mekanizmasının oluşturulması.
* React tabanlı Doktor, Eczacı, Hasta ve Paramedik panellerinin geliştirilmesi.
* Break-Glass (Acil Erişim) modülünün geliştirilmesi ve audit log mekanizmasının eklenmesi.
* Frontend ile Backend arasındaki Axios tabanlı API haberleşmesinin tamamlanması.
* BigQuery tarafındaki SQL Injection güvenlik önlemlerinin uygulanması.
* Veri tipi uyuşmazlıklarının (`STRING`, `INT64`, `DATE`) giderilmesi.
* Swagger/OpenAPI dokümantasyonunun güncellenmesi.
* Sistemin uçtan uca entegrasyon testlerinin tamamlanması.

---

## Ürün Durumu

Sprint 3 sonunda proje planlanan kapsam doğrultusunda tamamlanmış ve bağımsız modüller bir araya getirilerek tam fonksiyonel bir **Klinik Karar Destek Sistemi (Clinical Decision Support System - CDSS)** oluşturulmuştur.

### API ve Yapay Zeka Altyapısı

* XGBoost tabanlı ilaç etkileşim modeli başarıyla eğitilmiş ve reçete analiz servislerine entegre edilmiştir.
* Model, ilaç etkileşim risklerini ve güven skorlarını eş zamanlı olarak üretebilmektedir.
* FastAPI servisleri ile AI modeli sorunsuz şekilde haberleşmektedir.

### Veritabanı Entegrasyonu

* Google Cloud BigQuery altyapısı tamamen sisteme entegre edilmiştir.
* Parametreli SQL sorguları kullanılarak güvenli veri erişimi sağlanmıştır.
* UUID tabanlı kayıt mekanizmaları ve tarih formatları standart hale getirilmiştir.
* Audit Log sistemi ile kritik işlemler kayıt altına alınmaktadır.

### Kullanıcı Arayüzü

Tamamlanan arayüzler:

* Doktor Paneli
* Eczacı Paneli
* Hasta Paneli
* Paramedik Paneli
* Break-Glass (Acil Erişim) Modülü
* Giriş (Login) Sistemi

Frontend ve backend tam entegre çalışmakta olup kullanıcı işlemleri gerçek zamanlı olarak API üzerinden gerçekleştirilmektedir.

---

## Sprint Review

### Alınan Kararlar

* Uçtan uca çalışan sistem mimarisi onaylanmıştır.
* Break-Glass (Acil Erişim) modülü klinik senaryolar açısından başarılı bulunmuş ve audit kayıt mekanizmasıyla birlikte sistemin önemli güvenlik bileşenlerinden biri olarak kabul edilmiştir.
* Yapay zeka modelinden dönen tahmin sonuçlarının standart formatta backend tarafından işlenmesi ve frontend'e güvenli biçimde aktarılması kararlaştırılmıştır.
* Frontend, backend, yapay zeka modeli ve BigQuery altyapısının tam entegrasyonu tamamlanarak proje final sürümüne ulaştırılmıştır.

---

## Sprint Retrospective

### Neler İyi Gitti?

* Yapay zeka modelinin backend'e entegrasyonu sorunsuz şekilde tamamlandı.
* Frontend ve backend ekipleri koordineli çalışarak API entegrasyonunu başarıyla gerçekleştirdi.
* Break-Glass modülü planlanan fonksiyonların tamamını yerine getirecek şekilde geliştirildi.
* BigQuery tip uyuşmazlıkları, SQL sorguları ve API yönlendirme problemleri hızlı şekilde çözüldü.
* Modüler proje yapısı sayesinde geliştirme ve hata ayıklama süreçleri kolaylaştı.
* Tüm bileşenler başarıyla entegre edilerek çalışan bir Klinik Karar Destek Sistemi ortaya çıkarıldı.

### Neler Geliştirilebilir?

* API endpoint isimlendirmeleri ve JSON veri sözleşmeleri geliştirme sürecinin başında daha ayrıntılı dokümante edilebilir.
* BigQuery tablo şemaları ile backend modellerinin eşleştirilmesi daha erken standartlaştırılabilir.
* Test senaryoları geliştirme sürecinin daha erken aşamalarında otomatik hale getirilebilir.

### Genel Değerlendirme

Sprint 3 ile birlikte DrugSense projesi planlanan tüm temel hedeflerini başarıyla tamamlamıştır. Yapay zeka destekli ilaç etkileşim analizi, Google Cloud BigQuery veritabanı, FastAPI tabanlı backend servisleri ve React tabanlı kullanıcı arayüzleri tek bir sistem altında birleştirilmiş; doktor, eczacı, hasta ve paramedik kullanıcıları için uçtan uca çalışan güvenli bir **Klinik Karar Destek Sistemi (CDSS)** ortaya çıkarılmıştır.
