from fastapi import APIRouter, HTTPException
from ..database import bq_client
from google.cloud import bigquery
from .patient import get_patient_profile
from .drugs import get_muadiller
import logging
from functools import lru_cache

router = APIRouter()

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"
logger = logging.getLogger(__name__)


# ------------------------
# Yardımcı Fonksiyonlar
# ------------------------
@lru_cache(maxsize=128)
def get_drug_ingredient(drug_name: str):
    """İlacın etken maddesini getirir."""
    query = f"""
        SELECT active_ingredient
        FROM `{PROJECT_ID}.{DATASET_ID}.titck_drugs`
        WHERE LOWER(drug_name)=@drug
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "drug",
                "STRING",
                drug_name.lower()
            )
        ]
    )

    result = list(bq_client.query(query, job_config=job_config).result())

    if result:
        return result[0].active_ingredient

    return None


def get_interaction(ing1: str, ing2: str):
    """DDInter etkileşimini sorgular."""

    query = f"""
        SELECT level
        FROM `{PROJECT_ID}.{DATASET_ID}.ddinter_interactions`
        WHERE
        (LOWER(drug1_name)=@ing1 AND LOWER(drug2_name)=@ing2)

        OR

        (LOWER(drug1_name)=@ing2 AND LOWER(drug2_name)=@ing1)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "ing1",
                "STRING",
                ing1.lower()
            ),
            bigquery.ScalarQueryParameter(
                "ing2",
                "STRING",
                ing2.lower()
            )
        ]
    )

    result = list(bq_client.query(query, job_config=job_config).result())

    if result:
        return result[0].level

    return None


# ------------------------
# ECZACI GÜVENLİK KONTROLÜ
# ------------------------

@router.get("/check-safety/{patient_id}/{drug_name}")
def check_safety(patient_id: str, drug_name: str):

    try:
        patient = get_patient_profile(patient_id)
    except HTTPException:
        raise

    new_ing = get_drug_ingredient(drug_name)

    if not new_ing:
        raise HTTPException(
            status_code=404,
            detail="İlaç veritabanında bulunamadı."
        )

    report = {
        "patient": patient.full_name,
        "drug": drug_name,
        "status": "SAFE",
        "polypharmacy": len(patient.active_medications) >= 5,
        "warnings": [],
        "interactions": [],
        "alternatives": [],
        "recommendation": "İlaç güvenle teslim edilebilir."
    }

    # Polifarmasi

    if report["polypharmacy"]:
        report["warnings"].append(
            "Hastada polifarmasi riski bulunmaktadır."
        )

    # Alerji Kontrolü

    for allergy in patient.allergies:

        if allergy.allergen_name.lower() in new_ing.lower():

            report["status"] = "CRITICAL"

            report["warnings"].append(
                f"{allergy.allergen_name} alerjisi tespit edildi."
            )

    # Etkileşim Kontrolü

    for med in patient.active_medications:

        med_ing = get_drug_ingredient(med.drug_name)

        if not med_ing:
            continue

        level = get_interaction(new_ing, med_ing)

        if not level:
            continue

        level = level.strip().capitalize()

        report["interactions"].append({
            "drug": med.drug_name,
            "level": level
        })

        if level == "Major":

            report["status"] = "CRITICAL"

            report["warnings"].append(
                f"{med.drug_name} ile Major etkileşim bulundu."
            )

        elif level == "Moderate":

            if report["status"] != "CRITICAL":
                report["status"] = "WARNING"

            report["warnings"].append(
                f"{med.drug_name} ile Moderate etkileşim bulundu."
            )

    # Muadil Önerisi

    if report["status"] == "CRITICAL":

        try:

            muadil = get_muadiller(drug_name)

            report["alternatives"] = muadil.alternative_drugs

            report["recommendation"] = (
                "Muadil ilaç önerisi değerlendirilmelidir."
            )

        except Exception:

            report["recommendation"] = (
                "Muadil bulunamadı. Doktor ile iletişime geçiniz."
            )

    elif report["status"] == "WARNING":

        report["recommendation"] = (
            "İlaç verilebilir ancak hastaya danışmanlık verilmesi önerilir."
        )

    return report