import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Projemizin hiyerarşisine uygun import işlemi
from drugsense.routes.pharmacist import router

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

class TestPharmacistAPI:

    # 1. TEST: Güvenli İlaç Teslimatı (SAFE)
    @patch("drugsense.routes.pharmacist.get_patient_profile")
    @patch("drugsense.routes.pharmacist.get_drug_ingredient")
    @patch("drugsense.routes.pharmacist.get_interaction")
    def test_check_safety_safe(self, mock_interaction, mock_ingredient, mock_patient):
        # Sağlıklı hasta taklidi (Alerji yok, sadece 1 ilaç kullanıyor)
        mock_patient.return_value = MockPatient(
            full_name="Fatma Demir",
            active_medications=[MockMedication("Lansor")],
            allergies=[]
        )
        # Etken maddeleri tanımlıyoruz
        mock_ingredient.side_effect = ["paracetamol", "lansoprazole"]
        # Etkileşim yok
        mock_interaction.return_value = None

        response = client.get("/check-safety/11122233344/Parol")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SAFE"
        assert data["polypharmacy"] is False
        assert data["recommendation"] == "İlaç güvenle teslim edilebilir."
        assert len(data["warnings"]) == 0

    # 2. TEST: İlaç Veritabanında Yok (404 Not Found)
    @patch("drugsense.routes.pharmacist.get_patient_profile")
    @patch("drugsense.routes.pharmacist.get_drug_ingredient")
    def test_check_safety_drug_not_found(self, mock_ingredient, mock_patient):
        mock_patient.return_value = MockPatient("Can Yılmaz", [], [])
        
        # Etken madde bulunamadığını taklit ediyoruz
        mock_ingredient.return_value = None

        response = client.get("/check-safety/11122233344/BilinmeyenIlac")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "İlaç veritabanında bulunamadı."

    # 3. TEST: Alerji Tespit Edildi (CRITICAL)
    @patch("drugsense.routes.pharmacist.get_patient_profile")
    @patch("drugsense.routes.pharmacist.get_drug_ingredient")
    def test_check_safety_allergy(self, mock_ingredient, mock_patient):
        # Hastanın İbuprofen alerjisi var
        mock_patient.return_value = MockPatient(
            full_name="Ali Veli",
            active_medications=[],
            allergies=[MockAllergy("ibuprofen")]
        )
        mock_ingredient.return_value = "ibuprofen"

        response = client.get("/check-safety/11122233344/Brufen")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CRITICAL"
        assert any("alerjisi tespit edildi" in w for w in data["warnings"])

    # 4. TEST: Major Etkileşim ve Muadil Önerme (CRITICAL)
    @patch("drugsense.routes.pharmacist.get_patient_profile")
    @patch("drugsense.routes.pharmacist.get_drug_ingredient")
    @patch("drugsense.routes.pharmacist.get_interaction")
    @patch("drugsense.routes.pharmacist.get_muadiller")
    def test_check_safety_major_interaction(self, mock_muadil, mock_interaction, mock_ingredient, mock_patient):
        # Hasta halihazırda Warfarin (Kan sulandırıcı) kullanıyor
        mock_patient.return_value = MockPatient(
            full_name="Ayşe Kaya",
            active_medications=[MockMedication("Coumadin")],
            allergies=[]
        )
        mock_ingredient.side_effect = ["acetylsalicylic acid", "warfarin"]
        
        # Aspirin ve Warfarin arası Major etkileşim
        mock_interaction.return_value = "Major"
        
        # Muadil önerisi dönüyoruz
        mock_muadil.return_value = MockMuadil(["Alternatif A", "Alternatif B"])

        response = client.get("/check-safety/11122233344/Aspirin")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CRITICAL"
        assert len(data["interactions"]) == 1
        assert data["interactions"][0]["level"] == "Major"
        assert data["alternatives"] == ["Alternatif A", "Alternatif B"]
        assert "Muadil ilaç önerisi" in data["recommendation"]