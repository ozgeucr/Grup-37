from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import bq_client
from google.cloud import bigquery
from .drugs import get_muadiller
from .patient import get_patient_profile
import logging
from typing import Optional, List
from datetime import datetime

router = APIRouter()
PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
logger = logging.getLogger(__name__)

# --- MODELLER ---
class PrescriptionRequest(BaseModel):
    patient_id: str
    new_drug_name: str
    accept_responsibility: bool = False
    override_reason: Optional[str] = None

# --- YARDIMCI FONKSİYONLAR (Tekli Sorgular) ---

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

# --- YARDIMCI FONKSİYONLAR (Toplu Sorgular) ---

def get_bulk_drug_ingredients(drug_names: list[str]) -> dict:
    """Verilen ilaç listesinin etken maddelerini tek seferde çeker ve dictionary döner."""
    if not drug_names:
        return {}
    
    lower_drugs = [d.lower() for d in drug_names]
    
    query = f"""
        SELECT LOWER(drug_name) as d_name, active_ingredient 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
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
        SELECT Drug_A as drug1_name, Drug_B as drug2_name, Level as level 
        FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE (LOWER(Drug_A) = LOWER(@new_ing) AND LOWER(Drug_B) IN UNNEST(@patient_ings))
           OR (LOWER(Drug_B) = LOWER(@new_ing) AND LOWER(Drug_A) IN UNNEST(@patient_ings))
        
        UNION ALL
        
        SELECT ingredient_1 as drug1_name, ingredient_2 as drug2_name, risk_level as level 
        FROM `{PROJECT_ID}.{DATASET_ID}.interactions`
        WHERE (LOWER(ingredient_1) = LOWER(@new_ing) AND LOWER(ingredient_2) IN UNNEST(@patient_ings))
           OR (LOWER(ingredient_2) = LOWER(@new_ing) AND LOWER(ingredient_1) IN UNNEST(@patient_ings))
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing.lower()),
            bigquery.ArrayQueryParameter("patient_ings", "STRING", [ing.lower() for ing in patient_ings])
        ]
    )
    res = bq_client.query(query, job_config=job_config).result()
    
    interactions = {}
    for row in res:
        if row.drug1_name.lower() == new_ing.lower():
            interacting_drug = row.drug2_name.lower()
        else:
            interacting_drug = row.drug1_name.lower()
            
        interactions[interacting_drug] = row.level
        
    return interactions

def check_drug_disease_contraindications(new_ing: str, patient_diseases: list) -> list:
    """Hastanın kronik hastalıkları (ICD-10) ile yeni ilacın etken maddesini karşılaştırır."""
    if not new_ing or not patient_diseases:
        return []
        
    disease_codes = [d.icd10_code for d in patient_diseases if hasattr(d, 'icd10_code')]
    if not disease_codes:
        return []

    query = f"""
        SELECT icd10_code, disease_name, risk_level, warning_message
        FROM `{PROJECT_ID}.{DATASET_ID}.drug_diseases`
        WHERE LOWER(active_ingredient) = LOWER(@new_ing)
          AND icd10_code IN UNNEST(@disease_codes)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing.lower()),
            bigquery.ArrayQueryParameter("disease_codes", "STRING", disease_codes)
        ]
    )
    res = bq_client.query(query, job_config=job_config).result()
    
    conflicts = []
    for row in res:
        conflicts.append({
            "disease_name": row.disease_name,
            "icd10_code": row.icd10_code,
            "level": row.risk_level,
            "warning": row.warning_message
        })
    return conflicts

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
    """Sistemin kalbi: Reçeteleme ve Çok Boyutlu Güvenlik Duvarı (İlaç-İlaç, Alerji, İlaç-Hastalık)."""
    
    # 1. Hata Yönetimi: Hasta profili kontrolü
    try:
        patient = get_patient_profile(request.patient_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Hasta profili hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Hasta profili alınırken hata oluştu.")
    
    patient_drug_names = [med.drug_name for med in patient.active_medications]
    all_drugs_to_check = patient_drug_names + [request.new_drug_name]

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
        "disease_conflict_count": 0,
        "polypharmacy": len(patient.active_medications) >= 5,
        "interactions": [],
        "allergy_warnings": [],
        "disease_warnings": [],
        "suggestions": [],
        "recommendation": "Reçete güvenle oluşturulabilir."
    }

    # Polifarmasi Kontrolü
    if report["polypharmacy"]:
        report["suggestions"].append("Hastada polifarmasi riski bulunmaktadır.")

    # 2. ALERJİ KONTROLÜ
    for allergy in patient.allergies:
        if allergy.allergen_name.lower() in new_ing.lower():
            report["allergy_count"] += 1
            report["overall_status"] = "CRITICAL"
            report["is_prescription_blocked"] = True
            report["allergy_warnings"].append(f"{allergy.allergen_name} alerjisi tespit edildi!")

    # 3. İLAÇ - HASTALIK (KONTRENDİKASYON) KONTROLÜ
    disease_conflicts = check_drug_disease_contraindications(new_ing, patient.diseases)
    for conflict in disease_conflicts:
        report["disease_conflict_count"] += 1
        level = conflict["level"].strip().capitalize()
        warning_text = f"Hasta Hastalığı ({conflict['disease_name']}) ile Çatışma: {conflict['warning']}"
        report["disease_warnings"].append(warning_text)
        
        if level == "Major":
            report["overall_status"] = "CRITICAL"
            report["is_prescription_blocked"] = True
            if warning_text not in report["suggestions"]:
                report["suggestions"].append(warning_text)
        elif level == "Moderate":
            if report["overall_status"] != "CRITICAL":
                report["overall_status"] = "WARNING"
            if warning_text not in report["suggestions"]:
                report["suggestions"].append(warning_text)

    # Hastanın etken maddelerinin listesini hazırlayalım
    patient_ings = [
        ingredients_dict.get(drug.lower()) 
        for drug in patient_drug_names 
        if ingredients_dict.get(drug.lower())
    ]

    interactions_dict = get_bulk_interactions(new_ing, patient_ings)

    # 4. ETKİLEŞİM KONTROLÜ
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

    # 5. FİNAL KARAR VE RİSK YÖNETİMİ (SORUMLULUK ONAYI)
    if report["is_prescription_blocked"]:
        if not request.accept_responsibility:
            raise HTTPException(
                status_code=400,
                detail=f"DİKKAT: {request.new_drug_name} reçetesi sistem tarafından engellendi (Majör İlaç Etkileşimi / Alerji / Hastalık Kontrendikasyonu). İlacı yazmak için 'accept_responsibility' onayını vermeli ve bir gerekçe (override_reason) sunmalısınız."
            )
        elif request.accept_responsibility and not request.override_reason:
            raise HTTPException(
                status_code=400,
                detail="Sorumluluk kabul edildi ancak yasal loglama için bir 'override_reason' (gerekçe) girmek zorundasınız."
            )
        else:
            report["is_prescription_blocked"] = False
            report["overall_status"] = "OVERRIDDEN_BY_DOCTOR"
            report["recommendation"] = f"Reçete hekim inisiyatifiyle onaylandı. Gerekçe: {request.override_reason}"
            logger.info(f"Hekim inisiyatifi kullanıldı. Hasta: {request.patient_id}, İlaç: {request.new_drug_name}, Gerekçe: {request.override_reason}")
    else:
        if report["overall_status"] == "WARNING":
            report["recommendation"] = "Yakın klinik takip önerilir."
        else:
            report["recommendation"] = "Reçete güvenle oluşturulabilir."

    return report

# --- Branş Filtreli Hasta Geçmişi Endpoint'i ---

@router.get("/doctor-patient-history/{doctor_tc}/{patient_tc}")
def get_doctor_filtered_history(doctor_tc: str, patient_tc: str):
    """Doktorun kendi branşına (veya rolüne) ait hastanın geçmiş reçete ve işlemlerini filtreler."""
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    doctor_query = f"""
        SELECT role, full_name 
        FROM `{PROJECT_ID}.{DATASET_ID}.users` 
        WHERE CAST(tc_no AS STRING) = @doctor_tc LIMIT 1
    """
    doc_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("doctor_tc", "STRING", doctor_tc)]
    )
    doc_rows = list(bq_client.query(doctor_query, job_config=doc_config).result())
    
    if not doc_rows:
        raise HTTPException(status_code=404, detail="Doktor bulunamadı.")
    
    doctor_role = doc_rows[0].role

    prescription_query = f"""
        SELECT p.prescription_id, p.doctor_tc_no, p.drug_name, p.status, p.override_reason, p.created_at
        FROM `{PROJECT_ID}.{DATASET_ID}.prescriptions` p
        WHERE CAST(p.patient_tc_no AS STRING) = @patient_tc 
          AND CAST(p.doctor_tc_no AS STRING) = @doctor_tc
    """
    
    rx_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("patient_tc", "STRING", patient_tc),
            bigquery.ScalarQueryParameter("doctor_tc", "STRING", doctor_tc)
        ]
    )
    
    rx_rows = bq_client.query(prescription_query, job_config=rx_config).result()
    
    history_records = [
        {
            "prescription_id": row.prescription_id,
            "drug_name": row.drug_name,
            "status": row.status,
            "override_reason": row.override_reason,
            "created_at": str(row.created_at)
        }
        for row in rx_rows
    ]

    return {
        "doctor_tc": doctor_tc,
        "doctor_role": doctor_role,
        "patient_tc": patient_tc,
        "filtered_prescriptions": history_records
    }