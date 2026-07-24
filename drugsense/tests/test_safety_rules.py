import pytest
from unittest.mock import patch, MagicMock

# Projedeki fonksiyonları içe aktarıyoruz
from drugsense.routes.doctor import (
    check_therapeutic_duplication,
    check_age_warnings,
    check_food_interactions
)

class TestClinicalSafetyRules:
    """
    Klinik Karar Destek Sistemi (CDSS) Güvenlik Kuralları Test Süiti.
    Bu sınıf; yaş, duplikasyon ve besin etkileşimi kurallarının 
    hata payı olmadan çalıştığını doğrular.
    """

    # --- 1. AYNI GRUP İLAÇ (DUPLİKASYON) TESTLERİ ---
    def test_therapeutic_duplication_detected(self):
        """Mevcut ilaçlar arasında aynı etken madde varsa True dönmeli."""
        patient_actives = ["Paracetamol", "Ibuprofen", "Metformin"]
        new_drug_ing = "ibuprofen"  # Büyük/küçük harf duyarsız olmalı
        
        result = check_therapeutic_duplication(new_drug_ing, patient_actives)
        assert result is True, "Duplikasyon yakalanamadı!"

    def test_therapeutic_duplication_safe(self):
        """Mevcut ilaçlar arasında aynı etken madde yoksa False dönmeli."""
        patient_actives = ["Paracetamol", "Metformin"]
        new_drug_ing = "Lisinopril"
        
        result = check_therapeutic_duplication(new_drug_ing, patient_actives)
        assert result is False, "Güvenli ilaca yanlışlıkla duplikasyon uyarısı verdi!"

    # --- 2. YAŞ VE DOZAJ TESTLERİ ---
    def test_pediatric_warning_triggered(self):
        """16 yaş altına Aspirin (acetylsalicylic acid) yazıldığında Reye Sendromu uyarısı vermeli."""
        new_drug_ing = "Acetylsalicylic Acid"
        patient_age = 12
        
        result = check_age_warnings(new_drug_ing, patient_age)
        assert "KRİTİK" in result
        assert "Reye Sendromu" in result

    def test_geriatric_nsaid_warning_triggered(self):
        """65 yaş üstüne güçlü NSAİİ yazıldığında kanama/böbrek uyarısı vermeli."""
        new_drug_ing = "Dexketoprofen"
        patient_age = 68
        
        result = check_age_warnings(new_drug_ing, patient_age)
        assert "Geriatrik" in result
        assert "mide kanaması" in result

    def test_age_safe_scenario(self):
        """Risk grubunda olmayan bir yaş ve ilaç kombinasyonunda boş dönmeli."""
        new_drug_ing = "Paracetamol"
        patient_age = 35
        
        result = check_age_warnings(new_drug_ing, patient_age)
        assert result == "", "Güvenli senaryoda gereksiz yaş uyarısı fırlatıldı!"

    # --- 3. İLAÇ-BESİN ETKİLEŞİMİ MOCK TESTLERİ ---
    @patch('drugsense.routes.doctor.bq_client')
    def test_food_interaction_major_risk(self, mock_bq_client):
        """BigQuery'den dönen 'Major' riskli besin etkileşimlerini doğru formatlamalı."""
        # BigQuery sorgusunu taklit (mock) ediyoruz ki test sırasında Google Cloud'a gitmesin
        mock_query_job = MagicMock()
        mock_row = MagicMock()
        mock_row.interacting_food = "Greyfurt Suyu"
        mock_row.risk_level = "Major"
        mock_row.warning_message = "Kas yıkımı riski."
        mock_query_job.result.return_value = [mock_row]
        mock_bq_client.query.return_value = mock_query_job

        new_drug_ing = "Atorvastatin"
        result = check_food_interactions(new_drug_ing)

        assert len(result) == 1
        assert result[0]["food"] == "Greyfurt Suyu"
        assert result[0]["level"] == "Major"
        assert result[0]["message"] == "Kas yıkımı riski."