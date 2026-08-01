import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Projemizin hiyerarşisine uygun import işlemi
from drugsense.routes.patient import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

# --- SAHTE (MOCK) BIGQUERY DÖNÜŞ SATIRLARI ---
# BigQuery'den dönen Row objelerini taklit eden sınıflar

class MockPatientRow:
    tc_no = "12345678901"
    full_name = "Ahmet Yılmaz"
    age = 45
    blood_type = "A+"

class MockAllergyRow:
    allergen_name = "Penicillin"
    severity = "High"
    source = "Doktor Kaydı"

class MockMedicationRow:
    def __init__(self, drug_name, status):
        self.drug_name = drug_name
        self.status = status
        self.prescribed_date = "2023-01-01"
        self.prescribing_doctor = "Dr. Ayşe Kaya"


# --- TESTLER ---

class TestPatientAPI:

    # 1. TEST: Başarılı Hasta Profili Sorgusu (200 OK)
    @patch("drugsense.routes.patient.bq_client")
    def test_get_patient_profile_success(self, mock_bq_client):
        # BigQuery proje adını ayarlıyoruz ki hata vermesin
        mock_bq_client.project = "test_project"

        # 1. Sorgu Yanıtı (Hasta)
        mock_patient_job = MagicMock()
        mock_patient_job.result.return_value = [MockPatientRow()]

        # 2. Sorgu Yanıtı (Alerji)
        mock_allergy_job = MagicMock()
        mock_allergy_job.result.return_value = [MockAllergyRow()]

        # 3. Sorgu Yanıtı (İlaçlar - Biri Aktif, Biri Pasif)
        mock_med_job = MagicMock()
        mock_med_job.result.return_value = [
            MockMedicationRow("Lansor", "Aktif"),
            MockMedicationRow("Parol", "Pasif")
        ]

        # side_effect ile üç sorguyu sırasıyla mock_bq_client'a yüklüyoruz
        mock_bq_client.query.side_effect = [mock_patient_job, mock_allergy_job, mock_med_job]

        # API'ye istek atıyoruz
        response = client.get("/profile/12345678901")
        
        assert response.status_code == 200
        data = response.json()
        
        # Dönüş verilerini doğruluyoruz
        assert data["full_name"] == "Ahmet Yılmaz"
        assert data["age"] == 45
        assert len(data["allergies"]) == 1
        assert data["allergies"][0]["allergen_name"] == "Penicillin"
        
        # Aktif ve Pasif ilaç ayrımının doğru yapıldığını test ediyoruz
        assert len(data["active_medications"]) == 1
        assert data["active_medications"][0]["drug_name"] == "Lansor"
        
        assert len(data["past_medications"]) == 1
        assert data["past_medications"][0]["drug_name"] == "Parol"

    # 2. TEST: Hasta Bulunamadı Durumu (404 Not Found)
    @patch("drugsense.routes.patient.bq_client")
    def test_get_patient_profile_not_found(self, mock_bq_client):
        mock_bq_client.project = "test_project"

        # İlk sorgudan (Hasta) boş liste dönerse
        mock_patient_job = MagicMock()
        mock_patient_job.result.return_value = []
        
        mock_bq_client.query.return_value = mock_patient_job

        response = client.get("/profile/99999999999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Hasta bulunamadı."

    # 3. TEST: BigQuery Bağlantı Hatası (500 Internal Server Error)
    # Burada bq_client'in None olmasını taklit ediyoruz
    @patch("drugsense.routes.patient.bq_client", None)
    def test_get_patient_profile_db_error(self):
        response = client.get("/profile/12345678901")
        
        assert response.status_code == 500
        assert response.json()["detail"] == "BigQuery bağlantısı kurulamadı."