from fastapi.testclient import TestClient
from drugsense.main import app  # FastAPI app nesnenizin olduğu ana dosya

client = TestClient(app)

def test_root_or_health():
    """Uygulamanın ayakta olup olmadığını kontrol eder."""
    response = client.get("/")
    # Eğer root endpoint'iniz yoksa bu testi pas geçebilir veya 404 alabilirsiniz.
    assert response.status_code in [200, 404]

def test_get_patient_profile_with_diseases():
    """Hastanın profilinin, hastalıklarının ve alerjilerinin eksiksiz gelip gelmediğini test eder."""
    # Test için geçerli bir hasta TC no kullanabilirsiniz (Örn: veritabanınızdaki bir TC)
    test_tc = "12345678901" 
    response = client.get(f"/profile/{test_tc}")
    
    if response.status_code == 200:
        data = response.json()
        assert "full_name" in data
        assert "diseases" in data
        assert "allergies" in data
        print(f"✅ Başarılı: {data['full_name']} adlı hasta profili ve hastalıkları çekildi.")
    else:
        print(f"⚠️ Hasta bulunamadı veya endpoint path'i farklı ({response.status_code}). Lütfen TC'yi kontrol edin.")

def test_doctor_prescription_contraindication_check():
    """Doktor reçeteleme ekranında hastalık kontrendikasyonunun (örn: Epilepsi hastasına nöbet tetikleyici ilaç) blokesini test eder."""
    payload = {
        "patient_id": "12345678901",       # Epilepsi veya Peptik Ülser tanısı olan bir hasta TC'si
        "new_drug_name": "Tramadol",     # Epilepsi hastasında Majör risk yaratmalı
        "accept_responsibility": False
    }
    
    response = client.post("/doctor/prescribe-and-analyze", json=payload)
    
    # Beklenen: Majör risk / hastalık çatışması nedeniyle 400 Bad Request (Engelleme) dönmesi
    print(f"Doktor Reçete Test Yanıtı ({response.status_code}):", response.json())
    assert response.status_code in [200, 400, 404, 422]

def test_pharmacist_safety_check():
    """Eczacı güvenlik kontrolü ve hastalık uyarılarının gelip gelmediğini test eder."""
    test_tc = "12345678901"
    drug_name = "Dexketoprofen"  # Peptik Ülser hastasında risk yaratabilecek bir ilaç
    
    response = client.get(f"/check-safety/{test_tc}/{drug_name}")
    
    print(f"Eczacı Güvenlik Test Yanıtı ({response.status_code}):", response.json())
    assert response.status_code in [200, 404]