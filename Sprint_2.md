# Sprint 2 - DrugSense Proje Raporu

## 📌 Backlog Düzeni ve Story Seçimleri
Bir önceki sprintte karar verilen "veritabanının ve backend uç noktalarının oluşturulması" hedefi doğrultusunda backlog'umuz teknik altyapı, kodlama ve veri ön işleme (data preprocessing) görevlerine odaklanmıştır. Bu sprintte projenin modüler dosya mimarisi (`routes`, `models`, `database`, `scripts`, `data`) kurulmuş, FastAPI kullanılarak backend iskeleti ayağa kaldırılmıştır. Google Cloud BigQuery bağlantısının sağlanması ve veri çekme işlemlerinin (`GET /patient/profile/{tc_no}`) API uç noktalarına entegre edilmesi önceliklendirilmiştir. Git versiyon kontrol sistemi için `.gitignore` yapılandırması tamamlanarak güvenli bir geliştirme ortamı sağlanmıştır.

Bu sprintin en kritik bir diğer aşaması ise veri setlerinin düzenlenmesidir. Sprint 1'de toplanan dağınık ham veriler (TİTCK, OpenFDA ve etkileşim veri setleri), yapay zeka modelinin eğitimine (training) uygun hale getirilmek üzere detaylı bir veri temizleme (data cleaning) ve birleştirme işleminden geçirilmiştir. 

## 📅 Scrum ve Asenkron İletişim Süreci
Sprint 1'de benimsediğimiz **Asenkron Check-in** modeli bu süreçte de hızımızı artırmış, özellikle hata ayıklama (debugging) aşamalarında takım içi iletişim kanalları aktif kullanılmıştır. Sprint 1 retrospektifinde aldığımız "eşli programlama (pair-programming)" kararı, kodlama standartlarının belirlenmesinde, Git repository temizliğinde ve karmaşık veri setlerinin birleştirilmesi (merge) stratejilerinde çok etkili olmuştur. Veritabanı şemalarındaki uyuşmazlıklardan kaynaklı (Blocker) durumlar, asenkron iletişim sayesinde anında raporlanmış ve eşzamanlı çözüm planları devreye sokulmuştur.

## 📋 Sprint Board Update
Sprint board'umuzun güncel durumu aşağıdaki gibidir.

[DrugSense Sprint 2.pdf](https://github.com/user-attachments/files/30102210/DrugSense.Sprint.2.pdf)

Önceliklendirilen görevler takım kapasitesine göre işleme alınmıştır:

**Tamamlanan ve Üzerinde Çalışılan Görevler (In Progress / Done):**
*   Veri setindeki eksik değerlerin analiz edilmesi, işlenmesi ve temizleme stratejisinin belirlenmesi[cite: 1].
*   Veri formatlarının standartlaştırılması, veri setinin backend için uygun formata dönüştürülmesi ve model eğitimine uygun hale getirilmesi[cite: 1].
*   Veritabanı bağlantısının kurulması[cite: 1].

**Planlanan Görevler (To Do / Backlog):**
*   İlaç etkileşim analizi için uygun algoritmanın belirlenmesi ve algoritma seçeneklerinin karşılaştırılması[cite: 1].
*   İlk model eğitiminin yapılması ve sürecin başlatılması[cite: 1].
*   İlaç etkileşim sorgulama API'sinin ve İlaç/alerji etkileşim sorgulama API'sinin kodlanması[cite: 1].
*   Kullanıcı kayıt ve profil API'sinin kodlanması[cite: 1].
*   API uç noktalarının test edilmesi[cite: 1].
*   Kullanıcı senaryolarının oluşturulması[cite: 1].
*   Model sonuçlarının ve çıktılarının backend üzerinden erişilebilir hale getirilip entegre edilmesi[cite: 1].

*(Not: Board'un son görseli buraya eklenecektir.)*
<!-- GÖRSEL EKLENDİĞİNDE BURAYA SRC LİNKİNİ YAPIŞTIRIN: <img width="846" height="621" alt="Ekran Resmi - Sprint 2 Board" src="..." /> -->

## 🚀 Ürün Durumu (Product Status)
Bu sprintte araştırma aşamasından geliştirme (development) ve veri mühendisliği aşamasına geçilmiştir.
*   **API Altyapısı:** FastAPI sunucusu başarılı bir şekilde çalışmakta ve `/docs` üzerinden Swagger UI dokümantasyonu sunulmaktadır.
*   **Veritabanı Entegrasyonu:** BigQuery istemcisi (`bq_client`) projeye başarıyla entegre edilmiştir. Veritabanı ile backend arasındaki veri tipleri (`INT64`, `STRING`) ve şema senkronizasyonu üzerindeki optimizasyonlar devam etmektedir.
*   **Veri Seti (Dataset) Hazırlığı:** Ham veri setlerinin gereksiz ve eksik verilerden (null/NaN) arındırılması, formatlarının standartlaştırılması ve tek bir konsolide yapı altında birleştirilmesi (data wrangling) başarıyla tamamlanmıştır. Yapay zeka modelini besleyecek ana veri kaynağı hazır durumdadır.

## 🔍 Sprint Review
**Alınan Kararlar:** Proje kod yapısının tek bir dosya yerine modüler bir yapıda (`patient.py`, `drugs.py`, `doctor.py` vb.) kurgulanması onaylanmıştır. API güvenliğini sağlamak adına kimlik bilgisi dosyaları yerel izolasyona alınmıştır. Dağınık haldeki veri setlerinin başarılı bir şekilde birleştirilmesiyle, makine öğrenmesi algoritmalarının eğitimine başlanması için gereken en önemli veri bariyeri aşılmıştır. Veritabanı sorgularının (SQL) API ile tam entegre çalışabilmesi için BigQuery tablolarının dondurulup (freeze) backend ekibine kesin bildirilmesi kararlaştırılmıştır.

## 🔄 Sprint Retrospective
*   **Neler iyi gitti?** Veri temizleme ve birleştirme süreçlerinin hedeflenen sürede tamamlanması, takımın veri işleme süreçlerindeki yetkinliğini gösterdi. Proje kod yapısının en baştan modüler hale getirilmesi ve Git üzerinde yapılan radikal temizlik, ilerleyen süreçlerdeki kod karmaşasını engelledi. Backend iskeletinin hızlıca ayağa kaldırılması takıma büyük bir ivme kazandırdı.
*   **Neler geliştirilebilir?** BigQuery'de tablolar oluşturulurken, backend kodunda kullanılacak veri tipleri ve sütun isimleri sprintin en başında daha net bir şekilde eşleştirilmeli ve dokümante edilmelidir. Bu sayede API tarafında alınan "Tip Uyuşmazlığı" (Type Mismatch) hatalarının ve zaman kayıplarının önüne geçilebilir.
*   **Sonraki Sprint Planı:** Sprint 3'te, güncellenen BigQuery şeması ile API uç noktalarının tam uyumlu hale getirilip hasta/ilaç/alerji profillerinin sorunsuz çekilmesi hedeflenmektedir. Eş zamanlı olarak, temizlenen konsolide veri setleri kullanılarak yapay zeka modelinin eğitim ve test süreçlerine başlanması planlanmaktadır.
