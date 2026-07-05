#  Sprint 1

* **Backlog Düzeni ve Story Seçimleri:** İlk sprint için backlog'umuz tamamen araştırma görevlerine ve projeyi sağlam bir temele oturtmaya odaklanacak şekilde düzenlenmiştir. Klinik karar destek sistemimizi besleyecek veri setlerinin kaynak araştırmaları yapılmış; TİTCK yerel ilaç verileri ve evrensel alerjen/yardımcı madde bilgileri için OpenFDA API altyapıları incelenmiştir. Ek olarak, daha kapsamlı etkileşim verilerine ulaşmak adına DrugBank platformuna akademik erişim başvurusu yapılmıştır. Veri setlerinin birleştirilip temizlenmesi, oluşturulan bu veri setiyle var olan bir yapay zeka modelinin eğitilmesi ve backend mimarisinin ayağa kaldırılması Sprint 2 hedefleri olarak planlanıp backlog'a eklenmiştir.

* **Scrum ve Asenkron İletişim Süreci:** Projemizin ve takım üyelerimizin dinamikleri göz önüne alınarak klasik "Daily Scrum" ritüeli, takımın hızını artırmak adına **Asenkron Check-in** modeline adapte edilmiştir. Geliştirme süreci boyunca iletişimimiz mesajlaşma kanalları üzerinden kesintisiz olarak devam etmiş; projenin veri mimarisi kararları, blocker (engelleyici) sorunların çözümü ve durum değerlendirmeleri için ise belirlenen spesifik günlerde eşzamanlı (sesli/görüntülü) odak toplantıları gerçekleştirilmiştir. 
   *(Takım iletişimine dair kesitler, toplantı notları ve araştırma kanıtlarına **[Sprint 1 İletişim ve Toplantı Kanıtları (Artifacts)](./Sprint_1_Attachments/README.md)** sayfamızdan ulaşabilirsiniz.)*

* **Sprint Board Update:** Sprint board'umuzun güncel durumu aşağıdaki gibidir:

<img width="846" height="621" alt="Ekran Resmi 2026-07-05 14 21 24" src="https://github.com/user-attachments/assets/50dcdaff-84e1-4d70-9419-674b4ad9485a" />

* **Ürün Durumu:** Bu sprintte odak noktası kodlama ve arayüz tasarımı değil, veri mimarisi ve araştırmadır. Projenin genel iş akış diyagramları ve sistem mimarisi taslakları oluşturulmuştur.
<img width="981" height="638" alt="Ekran Resmi 2026-07-05 14 20 54" src="https://github.com/user-attachments/assets/c015d54f-398b-4aec-a7e6-973e27bda70f" />

* **Sprint Review:** 
  **Alınan Kararlar:** TİTCK ve OpenFDA entegrasyonuna dayalı veri mimarisi onaylanmış, DrugBank başvuru süreci tamamlanmış ve proje rolleri kesinleştirilmiştir. Geliştirme ortamları ve backend altyapısı için kullanılacak ana teknoloji (Python vb.) standartlaştırılmıştır.

* **Sprint Retrospective:**
  * Takım içi iletişim kanalları başarıyla oturtuldu ve projenin araştırma/veri keşfi süreci verimli bir şekilde tamamlandı.
  * Bir sonraki sprint'te (Sprint 2) TİTCK ve OpenFDA verilerinin temizlenerek entegre edilmesine, veritabanının ve backend uç noktalarının oluşturulmasına ağırlık verilmesi kararlaştırıldı.
  * Sprint 2'de elde edilecek temiz verilerle yapay zeka modelinin öğretilme (eğitim) aşamasına başlanması planlandı.
  * Önümüzdeki sprintte başlayacak olan yoğun kodlama ve entegrasyon süreçlerinin daha hızlı ilerlemesi için takım içi pair-programming (eşli programlama) yapılmasına karar verildi.
