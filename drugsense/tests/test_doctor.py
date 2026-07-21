import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Yolu 'drugsense' paketinden başlayarak veriyoruz
from drugsense.routes.doctor import router 

app = FastAPI()
app.include_router(router)

client = TestClient(app)

# --- SAHTE (MOCK) VERİ MODELLERİ ---
class MockMedication:
    def __init__(self, drug_name):
        self.drug_name = drug_name

class MockAllergy:
    def __init__(self, allergen_name):
        self.allergen_name = allergen_name

class MockPatient:
    def __init__(self, full_name, active_medications, allergies):
        self.full_name = full_name
        self.active_medications = active_medications
        self.allergies = allergies

class MockMuadil:
    def __init__(self, alternative_drugs):
        self.alternative_drugs = alternative_drugs

# --- TESTLER ---
class TestPrescriptionAPI:

    # 1. TEST: Check and Suggest Endpoint'i - Başarılı Senaryo
    @patch("drugsense.routes.doctor.get_drug_ingredient")
    @patch("drugsense.routes.doctor.get_interaction")
    def test_check_and_suggest_safe(self, mock_get_interaction, mock_get_ingredient):
        mock_get_ingredient.side_effect = ["paracetamol", "ibuprofen"]
        mock_get_interaction.return_value = None 

        response = client.get("/check-and-suggest/parol/brufen")
        
        assert response.status_code == 200
        assert response.json()["status"] == "Safe"

    # 2. TEST: Doktor Reçeteleme - Her Şey Güvenli (SAFE)
    @patch("drugsense.routes.doctor.get_patient_profile")
    @patch("drugsense.routes.doctor.get_bulk_drug_ingredients")
    @patch("drugsense.routes.doctor.get_bulk_interactions")
    def test_prescribe_and_analyze_safe(self, mock_interactions, mock_ingredients, mock_patient):
        mock_patient.return_value = MockPatient(
            full_name="Ahmet Yılmaz",
            active_medications=[MockMedication("Lansor")],
            allergies=[]
        )
        mock_ingredients.return_value = {
            "parol": "paracetamol",
            "lansor": "lansoprazole"
        }
        mock_interactions.return_value = {}

        payload = {"patient_id": "12345", "new_drug_name": "Parol"}
        response = client.post("/doctor/prescribe-and-analyze", json=payload)
        
        data = response.json()
        assert response.status_code == 200
        assert data["overall_status"] == "SAFE"
        assert data["is_prescription_blocked"] is False

    # 3. TEST: Alerji Durumu - Reçete Bloke Edilmeli (CRITICAL)
    @patch("drugsense.routes.doctor.get_patient_profile")
    @patch("drugsense.routes.doctor.get_bulk_drug_ingredients")
    def test_prescribe_and_analyze_allergy_block(self, mock_ingredients, mock_patient):
        mock_patient.return_value = MockPatient(
            full_name="Ayşe Kaya",
            active_medications=[],
            allergies=[MockAllergy("paracetamol")]
        )
        mock_ingredients.return_value = {"parol": "paracetamol"}

        payload = {"patient_id": "67890", "new_drug_name": "Parol"}
        response = client.post("/doctor/prescribe-and-analyze", json=payload)
        
        data = response.json()
        assert response.status_code == 200
        assert data["overall_status"] == "CRITICAL"
        assert data["is_prescription_blocked"] is True

    # 4. TEST: Major Etkileşim ve Muadil Önerme
    @patch("drugsense.routes.doctor.get_patient_profile")
    @patch("drugsense.routes.doctor.get_bulk_drug_ingredients")
    @patch("drugsense.routes.doctor.get_bulk_interactions")
    @patch("drugsense.routes.doctor.get_muadiller")
    def test_prescribe_and_analyze_major_interaction(self, mock_muadiller, mock_interactions, mock_ingredients, mock_patient):
        mock_patient.return_value = MockPatient(
            full_name="Mehmet Demir",
            active_medications=[MockMedication("Coumadin")],
            allergies=[]
        )
        mock_ingredients.return_value = {
            "aspirin": "acetylsalicylic acid",
            "coumadin": "warfarin"
        }
        mock_interactions.return_value = {"warfarin": "Major"}
        mock_muadiller.return_value = MockMuadil("Alternatif İlaç X, Y, Z")

        payload = {"patient_id": "11111", "new_drug_name": "Aspirin"}
        response = client.post("/doctor/prescribe-and-analyze", json=payload)
        
        data = response.json()
        assert response.status_code == 200
        assert data["overall_status"] == "CRITICAL"
        assert data["is_prescription_blocked"] is True
        assert data["interactions"][0]["level"] == "Major"