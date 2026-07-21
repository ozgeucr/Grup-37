from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import bq_client
from google.cloud import bigquery
from .drugs import get_muadiller
from .patient import get_patient_profile
import logging

router = APIRouter()
PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
logger = logging.getLogger(__name__)

# --- MODELLER ---
# İstek (Request) gövdesini tanımladığımız yer
class PrescriptionRequest(BaseModel):
    patient_id: str
    new_drug_name: str

# --- YARDIMCI FONKSİYONLAR (Tekli Sorgular - Eski endpoint için) ---

def get_drug_ingredient(drug_name: str):
    """titck_drugs tablosundan tek bir ilacın etken maddesini çeker."""
    query = f"SELECT active_ingredient FROM `{PROJECT_ID}.{DATASET_ID}.titck_drugs` WHERE LOWER(drug_name) = @drug LIMIT 1"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("drug", "STRING", drug_name.lower())])
    res = list(bq_client.query(query, job_config=job_config).result())
    return res[0].active_ingredient if res else None

def get_interaction(ing1: str, ing2: str):
    """ddinter_interactions tablosundan iki etken madde arası etkileşimi sorgular."""
    query = f"""
        SELECT level FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE (LOWER(drug1_name) = @ing1 AND LOWER(drug2_name) = @ing2) 
           OR (LOWER(drug1_name) = @ing2 AND LOWER(drug2_name) = @ing1)
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("ing1", "STRING", ing1.lower()),
            bigquery.ScalarQueryParameter("ing2", "STRING", ing2.lower())
        ]
    )
    res = list(bq_client.query(query, job_config=job_config).result())
    return res[0].level if res else None

# --- YARDIMCI FONKSİYONLAR (Toplu Sorgular - Yeni performanslı endpoint için) ---

def get_bulk_drug_ingredients(drug_names: list[str]) -> dict:
    """Verilen ilaç listesinin etken maddelerini tek seferde çeker ve dictionary döner."""
    if not drug_names:
        return {}
    
    lower_drugs = [d.lower() for d in drug_names]
    
    query = f"""
        SELECT LOWER(drug_name) as d_name, active_ingredient 
        FROM `{PROJECT_ID}.{DATASET_ID}.titck_drugs`
        WHERE LOWER(drug_name) IN UNNEST(@drug_list)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ArrayQueryParameter("drug_list", "STRING", lower_drugs)]
    )
    res = bq_client.query(query, job_config=job_config).result()
    return {row.d_name: row.active_ingredient for row in res}

def get_bulk_interactions(new_ing: str, patient_ings: list[str]) -> dict:
    """Yeni etken madde ile hastanın tüm etken maddeleri arasındaki etkileşimleri tek sorguda çeker."""
    if not new_ing or not patient_ings:
        return {}
        
    query = f"""
        SELECT LOWER(drug2_name) as interacting_ing, level 
        FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE LOWER(drug1_name) = @new_ing 
          AND LOWER(drug2_name) IN UNNEST(@patient_ings)
        UNION ALL
        SELECT LOWER(drug1_name) as interacting_ing, level 
        FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE LOWER(drug2_name) = @new_ing 
          AND LOWER(drug1_name) IN UNNEST(@patient_ings)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing.lower()),
            bigquery.ArrayQueryParameter("patient_ings", "STRING", [ing.lower() for ing in patient_ings])
        ]
    )
    res = bq_client.query(query, job_config=job_config).result()
    return {row.interacting_ing: row.level for row in res}


# --- ENDPOINTLER ---

@router.get("/check-and-suggest/{drug_1}/{drug_2}")
def check_and_suggest(drug_1: str, drug_2: str):
    """İki ilaç arası manuel etkileşim kontrolü."""
    ing1, ing2 = get_drug_ingredient(drug_1), get_drug_ingredient(drug_2)
    if not ing1 or not ing2:
        raise HTTPException(status_code=404, detail="İlaç bilgisi bulunamadı.")
    
    level = get_interaction(ing1, ing2)
    return {"status": level or "Safe", "mechanism": "Etkileşim analizi tamamlandı."}


@router.post("/doctor/prescribe-and-analyze")
def prescribe_and_analyze(request: PrescriptionRequest):
    """Sistemin kalbi: Reçeteleme güvenlik duvarı."""
    
    # 1. Hata Yönetimi: Hasta profili kontrolü
    try:
        patient = get_patient_profile(request.patient_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Hasta profili hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Hasta profili alınırken hata oluştu.")
    
    # Tüm ilaç isimlerini tek listede toplayalım
    patient_drug_names = [med.drug_name for med in patient.active_medications]
    all_drugs_to_check = patient_drug_names + [request.new_drug_name]

    # Tek BQ sorgusu ile tüm etken maddeleri çekelim
    ingredients_dict = get_bulk_drug_ingredients(all_drugs_to_check)
    
    new_ing = ingredients_dict.get(request.new_drug_name.lower())
    
    if not new_ing:
        return {
            "patient": patient.full_name,
            "new_drug": request.new_drug_name,
            "overall_status": "MANUAL_REVIEW", 
            "system_note": "İlaç tanımlanamadı.", 
            "recommendation": "Lütfen klinik inceleme yapın."
        }

    report = {
        "patient": patient.full_name,
        "new_drug": request.new_drug_name,
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

    # Hastanın etken maddelerinin listesini hazırlayalım
    patient_ings = [
        ingredients_dict.get(drug.lower()) 
        for drug in patient_drug_names 
        if ingredients_dict.get(drug.lower())
    ]

    # Tek BQ sorgusu ile tüm etkileşimleri çekelim
    interactions_dict = get_bulk_interactions(new_ing, patient_ings)

    # 3. GÜÇLENDİRİLMİŞ ETKİLEŞİM KONTROLÜ (Artık veritabanına gitmiyor, hafızadan okuyor)
    for med in patient.active_medications:
        med_ing = ingredients_dict.get(med.drug_name.lower())
        if not med_ing:
            continue
            
        level = interactions_dict.get(med_ing.lower())
        if level:
            level_str = level.strip().capitalize()
            report["interaction_count"] += 1
            report["interactions"].append({"drug": med.drug_name, "level": level_str})
            
            if level_str == "Major":
                report["overall_status"] = "CRITICAL"
                report["is_prescription_blocked"] = True
                
                # Güvenli Muadil Çağrısı
                try:
                    muadiller = get_muadiller(request.new_drug_name)
                    sugg = f"{request.new_drug_name} yerine alternatifler: {muadiller.alternative_drugs}"
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