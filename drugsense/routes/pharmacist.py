from fastapi import APIRouter, HTTPException
from ..database import bq_client
from google.cloud import bigquery
from .patient import get_patient_profile
from .drugs import get_muadiller
# Tüm güvenlik fonksiyonlarını doctor modülünden çekiyoruz
from .doctor import (
    get_bulk_drug_ingredients, 
    get_bulk_interactions, 
    check_drug_disease_contraindications,
    check_food_interactions,
    check_therapeutic_duplication,
    check_age_warnings
)
import logging

router = APIRouter()

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
logger = logging.getLogger(__name__)


# ------------------------
# ECZACI GÜVENLİK KONTROLÜ
# ------------------------

@router.get("/check-safety/{patient_id}/{drug_name}")
def check_safety(patient_id: str, drug_name: str):
    """Eczacının reçetesiz ilaç satışı veya muadil değişimi sırasındaki güvenlik duvarı."""

    try:
        patient = get_patient_profile(patient_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hasta profili çekilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Hasta profili alınamadı.")

    # 1. Hastanın mevcut ilaçları ve yeni ilaç için etken maddeleri toplu olarak çekiyoruz
    patient_drug_names = [med.drug_name for med in patient.active_medications]
    all_drugs_to_check = patient_drug_names + [drug_name]

    ingredients_dict = get_bulk_drug_ingredients(all_drugs_to_check)
    new_ing = ingredients_dict.get(drug_name.lower())

    if not new_ing:
        raise HTTPException(
            status_code=404,
            detail="İlaç veya etken madde veritabanında bulunamadı."
        )

    report = {
        "patient": patient.full_name,
        "patient_age": patient.age,
        "drug": drug_name,
        "status": "SAFE",
        "polypharmacy": len(patient.active_medications) >= 5,
        "warnings": [],
        "disease_warnings": [],
        "food_warnings": [],
        "interactions": [],
        "alternatives": [],
        "recommendation": "İlaç güvenle teslim edilebilir."
    }

    # Polifarmasi
    if report["polypharmacy"]:
        report["warnings"].append(
            "Hastada polifarmasi riski bulunmaktadır (5 veya daha fazla aktif ilaç kullanımı)."
        )

    # 2. AYNI GRUP İLAÇ (DUPLİKASYON) KONTROLÜ
    patient_ings = [
        ingredients_dict.get(drug.lower()) 
        for drug in patient_drug_names 
        if ingredients_dict.get(drug.lower())
    ]
    is_duplicated = check_therapeutic_duplication(new_ing, patient_ings)
    if is_duplicated:
        report["status"] = "WARNING"
        report["warnings"].append("DUPLİKASYON UYARISI: Hasta halihazırda bu etken maddeyi içeren bir ilaç kullanmaktadır.")

    # 3. YAŞ - DOZAJ KONTROLÜ
    if patient.age:
        age_warning = check_age_warnings(new_ing, patient.age)
        if age_warning:
            if "KRİTİK" in age_warning:
                report["status"] = "CRITICAL"
            elif report["status"] != "CRITICAL":
                report["status"] = "WARNING"
            report["warnings"].append(age_warning)

    # 4. ALERJİ KONTROLÜ
    for allergy in patient.allergies:
        if allergy.allergen_name.lower() in new_ing.lower():
            report["status"] = "CRITICAL"
            report["warnings"].append(
                f"KRİTİK: {allergy.allergen_name} alerjisi tespit edildi!"
            )

    # 5. İLAÇ - HASTALIK (KONTRENDİKASYON) KONTROLÜ
    disease_conflicts = check_drug_disease_contraindications(new_ing, patient.diseases)
    for conflict in disease_conflicts:
        level = conflict["level"].strip().capitalize()
        warning_text = f"Hastalık Çatışması ({conflict['disease_name']}): {conflict['warning']}"
        report["disease_warnings"].append(warning_text)
        
        if level == "Major":
            report["status"] = "CRITICAL"
            if warning_text not in report["warnings"]:
                report["warnings"].append(warning_text)
        elif level == "Moderate":
            if report["status"] != "CRITICAL":
                report["status"] = "WARNING"
            if warning_text not in report["warnings"]:
                report["warnings"].append(warning_text)

    # 6. İLAÇ - BESİN ETKİLEŞİMİ KONTROLÜ (Eczacı hastayı doğrudan uyarır)
    food_interactions = check_food_interactions(new_ing)
    for fw in food_interactions:
        food_level = fw['level'].strip().capitalize()
        food_text = f"Besin Etkileşimi [{food_level}] ({fw['food']}): {fw['message']}"
        report["food_warnings"].append(food_text)
        
        if food_level == "Major":
            if report["status"] != "CRITICAL":
                report["status"] = "WARNING" 
        
        report["warnings"].append(food_text)

    # 7. ETKİLEŞİM KONTROLÜ (İlaç-İlaç)
    interactions_dict = get_bulk_interactions(new_ing, patient_ings)

    for med in patient.active_medications:
        med_ing = ingredients_dict.get(med.drug_name.lower())
        if not med_ing:
            continue

        level = interactions_dict.get(med_ing.lower())
        if not level:
            continue

        level = level.strip().capitalize()
        report["interactions"].append({
            "drug": med.drug_name,
            "level": level
        })

        if level == "Major":
            report["status"] = "CRITICAL"
            warn_msg = f"{med.drug_name} ile Major etkileşim bulundu."
            if warn_msg not in report["warnings"]:
                report["warnings"].append(warn_msg)
        elif level == "Moderate":
            if report["status"] != "CRITICAL":
                report["status"] = "WARNING"
            warn_msg = f"{med.drug_name} ile Moderate etkileşim bulundu."
            if warn_msg not in report["warnings"]:
                report["warnings"].append(warn_msg)

    # 8. Muadil Önerisi ve Final Karar
    if report["status"] == "CRITICAL":
        try:
            muadil = get_muadiller(drug_name)
            report["alternatives"] = muadil.alternative_drugs
            report["recommendation"] = "DİKKAT: İlaç satışı risklidir! Güvenli bir muadil değerlendirilmeli veya hekime danışılmalıdır."
        except Exception:
            report["recommendation"] = "Muadil bulunamadı. Lütfen ilacı teslim etmeden önce reçete eden hekim ile iletişime geçiniz."

    elif report["status"] == "WARNING":
        report["recommendation"] = "İlaç verilebilir ancak olası yan etkiler, diyet kuralları ve yaş uyarıları konusunda hastaya detaylı danışmanlık verilmelidir."

    return report


# --- 1. AKTİF REÇETELERİ LİSTELEME ENDPOINT'İ ---
@router.get("/active-prescriptions/{patient_tc}")
def get_active_prescriptions(patient_tc: str):
    """Eczacının, hastanın henüz alınmamış (PENDING) aktif reçetelerini görmesini sağlar."""
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    query = f"""
        SELECT prescription_id, doctor_tc_no, drug_name, status, created_at
        FROM `{PROJECT_ID}.{DATASET_ID}.prescriptions`
        WHERE CAST(patient_tc_no AS STRING) = @patient_tc
          AND UPPER(status) = 'PENDING'
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("patient_tc", "STRING", patient_tc)]
    )
    
    rows = bq_client.query(query, job_config=job_config).result()
    
    prescriptions = [
        {
            "prescription_id": row.prescription_id,
            "doctor_tc_no": row.doctor_tc_no,
            "drug_name": row.drug_name,
            "status": row.status,
            "created_at": str(row.created_at)
        }
        for row in rows
    ]

    return {
        "patient_tc": patient_tc,
        "active_prescriptions_count": len(prescriptions),
        "prescriptions": prescriptions
    }


# --- 2. İLACI TESLİM ETME (DISPENSED) ENDPOINT'İ ---
@router.post("/dispense-medication/{prescription_id}")
def dispense_medication(prescription_id: str):
    """Eczacı ilacı hastaya teslim ettiğinde reçete durumunu DISPENSED yapar."""
    if bq_client is None:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")

    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.prescriptions`
        SET status = 'DISPENSED'
        WHERE prescription_id = @prescription_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("prescription_id", "STRING", prescription_id)]
    )

    try:
        bq_client.query(query, job_config=job_config).result()
        return {
            "status": "success",
            "message": f"{prescription_id} nolu reçete başarıyla teslim edildi (DISPENSED olarak güncellendi)."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reçete güncellenemedi: {str(e)}")