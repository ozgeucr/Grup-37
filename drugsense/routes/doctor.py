from fastapi import APIRouter, HTTPException
from ..database import bq_client
from google.cloud import bigquery
from .drugs import get_muadiller
from .patient import get_patient_profile
import logging

router = APIRouter()
PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
logger = logging.getLogger(__name__)

# --- YARDIMCI FONKSİYONLAR ---

def get_drug_ingredient(drug_name: str):
    """titck_drugs tablosundan etken maddeyi çeker."""
    query = f"SELECT active_ingredient FROM `{PROJECT_ID}.{DATASET_ID}.titck_drugs` WHERE LOWER(drug_name) = @drug LIMIT 1"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("drug", "STRING", drug_name.lower())])
    res = list(bq_client.query(query, job_config=job_config).result())
    return res[0].active_ingredient if res else None

def get_interaction(ing1: str, ing2: str):
    """ddinter_interactions tablosundan etkileşimi sorgular."""
    query = f"""
        SELECT level FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE (LOWER(drug1_name) = @ing1 AND LOWER(drug2_name) = @ing2) 
           OR (LOWER(drug1_name) = @ing2 AND LOWER(drug2_name) = @ing1)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("ing1", "STRING", ing1.lower()),
            bigquery.ScalarQueryParameter("ing2", "STRING", ing2.lower())
        ]
    )
    res = list(bq_client.query(query, job_config=job_config).result())
    return res[0].level if res else None

# --- ENDPOINTLER ---

@router.get("/check-and-suggest/{drug_1}/{drug_2}")
def check_and_suggest(drug_1: str, drug_2: str):
    """İki ilaç arası manuel etkileşim kontrolü."""
    ing1, ing2 = get_drug_ingredient(drug_1), get_drug_ingredient(drug_2)
    if not ing1 or not ing2:
        raise HTTPException(status_code=404, detail="İlaç bilgisi bulunamadı.")
    
    level = get_interaction(ing1, ing2)
    return {"status": level or "Safe", "mechanism": "Etkileşim analizi tamamlandı."}

@router.post("/prescribe-and-analyze/{patient_id}/{new_drug_name}")
def prescribe_and_analyze(patient_id: str, new_drug_name: str):
    """Sistemin kalbi: Reçeteleme güvenlik duvarı."""
    
    # 1. Hata Yönetimi: Hasta profili kontrolü
    try:
        patient = get_patient_profile(patient_id)
    except HTTPException as he:
        raise he
    except Exception:
        raise HTTPException(status_code=500, detail="Hasta profili alınırken hata oluştu.")
    
    new_ing = get_drug_ingredient(new_drug_name)
    
    if not new_ing:
        return {
            "patient": patient.full_name,
            "new_drug": new_drug_name,
            "overall_status": "MANUAL_REVIEW", 
            "system_note": "İlaç tanımlanamadı.", 
            "recommendation": "Lütfen klinik inceleme yapın."
        }

    report = {
        "patient": patient.full_name,
        "new_drug": new_drug_name,
        "overall_status": "SAFE",
        "is_prescription_blocked": False,
        "interaction_count": 0,
        "allergy_count": 0,
        "polypharmacy": len(patient.active_medications) >= 5,
        "interactions": [],
        "allergy_warnings": [],
        "suggestions": [],
        "recommendation": "Reçete güvenle oluşturulabilir."
    }

    # Polifarmasi Kontrolü
    if report["polypharmacy"]:
        report["suggestions"].append("Hastada polifarmasi riski bulunmaktadır.")

    # 2. GÜÇLENDİRİLMİŞ ALERJİ KONTROLÜ
    for allergy in patient.allergies:
        if allergy.allergen_name.lower() in new_ing.lower():
            report["allergy_count"] += 1
            report["overall_status"] = "CRITICAL"
            report["is_prescription_blocked"] = True
            report["allergy_warnings"].append(f"{allergy.allergen_name} alerjisi tespit edildi!")

    # 3. GÜÇLENDİRİLMİŞ ETKİLEŞİM KONTROLÜ
    for med in patient.active_medications:
        med_ing = get_drug_ingredient(med.drug_name)
        if med_ing:
            level = get_interaction(new_ing, med_ing)
            if level:
                level_str = level.strip().capitalize()
                report["interaction_count"] += 1
                report["interactions"].append({"drug": med.drug_name, "level": level_str})
                
                if level_str == "Major":
                    report["overall_status"] = "CRITICAL"
                    report["is_prescription_blocked"] = True
                    
                    # Güvenli Muadil Çağrısı
                    try:
                        muadiller = get_muadiller(new_drug_name)
                        sugg = f"{new_drug_name} yerine alternatifler: {muadiller.alternative_drugs}"
                        if sugg not in report["suggestions"]:
                            report["suggestions"].append(sugg)
                    except Exception:
                        if "Alternatif bulunamadı." not in report["suggestions"]:
                            report["suggestions"].append("Alternatif bulunamadı.")
                
                elif level_str == "Moderate":
                    if report["overall_status"] != "CRITICAL":
                        report["overall_status"] = "WARNING"
                    warn = f"Dikkat: {med.drug_name} ile {level_str} etkileşim."
                    if warn not in report["suggestions"]:
                        report["suggestions"].append(warn)

    # 4. Final Karar Önerisi
    if report["is_prescription_blocked"]:
        report["recommendation"] = "Reçete oluşturulmamalıdır."
    elif report["overall_status"] == "WARNING":
        report["recommendation"] = "Yakın klinik takip önerilir."

    return report