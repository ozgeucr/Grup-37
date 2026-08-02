import logging
from functools import lru_cache
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from google.cloud import bigquery

from ..database import bq_client
from ..models import MuadilResponse

# Hasta profilini çekebilmek için mevcut patient modülünü içe aktarıyoruz
try:
    from .patient import get_patient_profile
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Çift prefix (double prefix) hatasını önlemek için /pharmacist öneki kaldırıldı
router = APIRouter(
    tags=["Eczacı Paneli"]
)

PROJECT_ID = bq_client.project if bq_client else "default_project"
DATASET_ID = "drugsense_dataset"


# ==========================================
# YAPAY ZEKA MODELİ ENTEGRASYONU & VİZYON
# ==========================================
try:
    from ai_model.api.predict import predict_interaction
    AI_MODELS_LOADED = True
except ImportError as e:
    logger.critical(f"YAPAY ZEKA MODELLERİ YÜKLENEMEDİ! Fallback devrede. Hata: {e}")
    AI_MODELS_LOADED = False
    
    def predict_interaction(drug_a: str, drug_b: str) -> dict:
        return {"risk_level": "Unknown", "mechanism": "AI Model yüklenemedi.", "method": "Fallback"}
    
    def rank_alternatives_by_safety(drugs: list, context: list) -> list:
        return drugs
        
    def predict_disease_complication(ingredient: str, icd10: str) -> dict:
        return {"ai_risk_score": 0.0}


# ==========================================
# VERİTABANI YARDIMCI FONKSİYONU
# ==========================================
def execute_bq_query(query: str, parameters: list) -> list:
    """BigQuery sorgularını tek merkezden yönetmek, loglamak ve hataları yakalamak için."""
    if not bq_client:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")
    
    job_config = bigquery.QueryJobConfig(query_parameters=parameters)
    try:
        return list(bq_client.query(query, job_config=job_config).result())
    except Exception as e:
        logger.error(f"BigQuery Sorgu Hatası: {e}")
        raise HTTPException(status_code=500, detail="Veritabanı işlemi sırasında hata oluştu.")


# ==========================================
# BÖLÜM 1: MEVCUT İLAÇ VE AI SERVİSLERİ (/drugs/...)
# ==========================================

@router.get("/drugs/get-muadiller/{drug_name}", response_model=MuadilResponse)
def get_muadiller(
    drug_name: str, 
    patient_cart: Optional[str] = Query(None, description="Opsiyonel: Akıllı sıralama için sepetteki mevcut ilaçlar")
):
    query_ing = f"SELECT active_ingredient FROM `{PROJECT_ID}.{DATASET_ID}.drugs` WHERE LOWER(drug_name) = @drug_name LIMIT 1"
    res_ing = execute_bq_query(query_ing, [bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower())])
    
    if not res_ing:
        raise HTTPException(status_code=404, detail="İlaç bulunamadı.")
    
    active_ingredient = res_ing[0].active_ingredient
    
    query_alt = f"""
        SELECT drug_name FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(active_ingredient) = @active_ingredient AND LOWER(drug_name) != @drug_name
    """
    res_alt = execute_bq_query(query_alt, [
        bigquery.ScalarQueryParameter("active_ingredient", "STRING", active_ingredient.lower()),
        bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower())
    ])
    
    alternative_drugs = [row.drug_name for row in res_alt]

    if not alternative_drugs:
        raise HTTPException(status_code=404, detail="Aynı etken maddeye sahip başka ilaç bulunamadı.")

    if patient_cart and AI_MODELS_LOADED:
        try:
            cart_list = [d.strip().lower() for d in patient_cart.split(",")]
            alternative_drugs = rank_alternatives_by_safety(alternative_drugs, cart_list)
        except Exception as e:
            logger.warning(f"Akıllı sıralama çalıştırılamadı, standart liste dönülüyor: {e}")
    
    return MuadilResponse(
        original_drug=drug_name,
        active_ingredient=active_ingredient,
        alternative_drugs=alternative_drugs
    )


@router.get("/drugs/check-drug-disease/{drug_name}/{icd10_code}")
def check_drug_disease_risk(drug_name: str, icd10_code: str):
    query = f"""
        SELECT d.active_ingredient, dd.disease_name, dd.risk_level, dd.warning_message
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs` d
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.drug_diseases` dd
          ON LOWER(d.active_ingredient) = LOWER(dd.active_ingredient)
         AND UPPER(dd.icd10_code) = UPPER(@icd10_code)
        WHERE LOWER(d.drug_name) = LOWER(@drug_name)
        LIMIT 1
    """
    res = execute_bq_query(query, [
        bigquery.ScalarQueryParameter("drug_name", "STRING", drug_name.lower()),
        bigquery.ScalarQueryParameter("icd10_code", "STRING", icd10_code)
    ])
    
    if not res:
        raise HTTPException(status_code=404, detail="İlaç veritabanında bulunamadı.")
        
    row = res[0]
    active_ing = row.active_ingredient
    
    if row.risk_level:
        return {
            "drug_name": drug_name,
            "active_ingredient": active_ing,
            "icd10_code": icd10_code,
            "disease_name": row.disease_name,
            "risk_status": row.risk_level,
            "source": "Database",
            "warning": row.warning_message
        }
        
    try:
        ai_analysis = predict_disease_complication(active_ing, icd10_code)
        if ai_analysis.get("ai_risk_score", 0) > 75.0:
            return {
                "drug_name": drug_name,
                "icd10_code": icd10_code,
                "risk_status": "POTENTIAL_WARNING",
                "source": "AI_Prediction",
                "warning": f"Model %{ai_analysis['ai_risk_score']} oranında olası bir komplikasyon tespit etti."
            }
    except Exception:
        pass

    return {
        "drug_name": drug_name,
        "active_ingredient": active_ing,
        "icd10_code": icd10_code,
        "risk_status": "SAFE",
        "source": "Database",
        "warning": "Kayıtlı bir kontrendikasyon bulunamadı."
    }

@lru_cache(maxsize=1000)
def cached_predict(drug_a: str, drug_b: str) -> dict:
    sorted_drugs = sorted([drug_a.lower(), drug_b.lower()])
    try:
        return predict_interaction(sorted_drugs[0], sorted_drugs[1])
    except Exception as e:
        return {"risk_level": "Unknown", "mechanism": f"Hata: {e}"}

@router.get("/drugs/check-ai-interaction/{drug_a}/{drug_b}")
def check_ai_drug_interaction(drug_a: str, drug_b: str):
    if drug_a.lower().strip() == drug_b.lower().strip():
        raise HTTPException(status_code=400, detail="Aynı ilaç birbiriyle karşılaştırılamaz.")
    return {"status": "success", "interaction_analysis": cached_predict(drug_a, drug_b)}


# ==========================================
# BÖLÜM 2: REACT FRONTEND İÇİN ECZACI SERVİSLERİ (/pharmacist/...)
# ==========================================

@router.get("/active-prescriptions/{tc_no}")
def get_active_prescriptions(tc_no: str):
    """React Dashboard'un beklediği formatta hastanın aktif reçetelerini döndürür."""
    # DÜZELTME: patient_tc_no yerine güncel tablo kolonu olan tc_no kullanıldı.
    query = f"""
        SELECT p.prescription_id, p.drug_name, p.status, p.created_at, u.full_name as doctor_name
        FROM `{PROJECT_ID}.{DATASET_ID}.prescriptions` p
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.users` u ON CAST(p.doctor_tc_no AS STRING) = CAST(u.tc_no AS STRING)
        WHERE CAST(p.tc_no AS STRING) = @tc_no 
        ORDER BY p.created_at DESC
    """
    res = execute_bq_query(query, [bigquery.ScalarQueryParameter("tc_no", "STRING", tc_no)])
    
    prescriptions = []
    for row in res:
        prescriptions.append({
            "prescription_id": row.prescription_id,
            "drug_name": row.drug_name,
            "status": row.status,
            "created_at": str(row.created_at),
            "doctor_name": row.doctor_name or "Bilinmeyen Hekim"
        })
        
    return {"prescriptions": prescriptions}


@router.get("/check-safety/{tc_no}/{drug_name}")
def check_pharmacist_safety(tc_no: str, drug_name: str):
    """React Dashboard'daki yapay zeka analiz raporunu tam formatında besleyen kapsamlı güvenlik kontrolü."""
    try:
        patient = get_patient_profile(tc_no)
    except Exception:
        raise HTTPException(status_code=404, detail="Hasta profili bulunamadı.")
        
    query_ing = f"SELECT active_ingredient FROM `{PROJECT_ID}.{DATASET_ID}.drugs` WHERE LOWER(drug_name) = LOWER(@drug) LIMIT 1"
    res_ing = execute_bq_query(query_ing, [bigquery.ScalarQueryParameter("drug", "STRING", drug_name)])
    
    if not res_ing:
        return {
            "status": "MANUAL_REVIEW",
            "recommendation": "İlaç (veya etken madde) veritabanında bulunamadı. Lütfen manuel inceleme yapın.",
            "disease_warnings": [], "food_warnings": [], "interactions": [], "warnings": []
        }
        
    new_ing = res_ing[0].active_ingredient.lower()
    
    disease_warnings, food_warnings, interactions, general_warnings = [], [], [], []
    status_rank = 0  # 0: SAFE, 1: WARNING, 2: CRITICAL
    
    # 1. Alerji Kontrolü
    for allergy in patient.allergies:
        if allergy.allergen_name.lower() in new_ing:
            general_warnings.append(f"KRİTİK ALERJİ: {allergy.allergen_name} alerjisi tespit edildi!")
            status_rank = max(status_rank, 2)
            
    # 2. Hastalık Kontrolü
    disease_codes = [d.icd10_code for d in patient.diseases if hasattr(d, 'icd10_code')]
    if disease_codes:
        query_dis = f"""
            SELECT disease_name, risk_level, warning_message
            FROM `{PROJECT_ID}.{DATASET_ID}.drug_diseases`
            WHERE LOWER(active_ingredient) = @new_ing AND icd10_code IN UNNEST(@disease_codes)
        """
        dis_params = [
            bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing),
            bigquery.ArrayQueryParameter("disease_codes", "STRING", disease_codes)
        ]
        conflicts = execute_bq_query(query_dis, dis_params)
        for row in conflicts:
            level = row.risk_level.strip().capitalize()
            warning_text = f"Hastalık Çatışması ({row.disease_name}): {row.warning_message}"
            disease_warnings.append(warning_text)
            if level == "Major": status_rank = max(status_rank, 2)
            elif level == "Moderate": status_rank = max(status_rank, 1)
                
    # 3. Besin Etkileşimi
    query_food = f"SELECT interacting_food, risk_level, warning_message FROM `{PROJECT_ID}.{DATASET_ID}.drug_foods` WHERE LOWER(active_ingredient) = @new_ing"
    for fw in execute_bq_query(query_food, [bigquery.ScalarQueryParameter("new_ing", "STRING", new_ing)]):
        food_level = fw.risk_level.strip().capitalize()
        food_warnings.append(f"[{food_level}] {fw.interacting_food}: {fw.warning_message}")
        if "Major" in food_level: status_rank = max(status_rank, 2)
            
    # 4. Yapay Zeka DDI Kontrolü
    active_meds = [m.drug_name for m in patient.active_medications]
    if active_meds:
        query_bulk = f"SELECT LOWER(drug_name) as d_name, LOWER(active_ingredient) as a_ing FROM `{PROJECT_ID}.{DATASET_ID}.drugs` WHERE LOWER(drug_name) IN UNNEST(@drug_list)"
        bulk_res = execute_bq_query(query_bulk, [bigquery.ArrayQueryParameter("drug_list", "STRING", [d.lower() for d in active_meds])])
        med_ings = {row.d_name: row.a_ing for row in bulk_res}
        
        for med in active_meds:
            med_ing = med_ings.get(med.lower())
            if not med_ing or med_ing == new_ing:
                continue
                
            ai_result = cached_predict(new_ing, med_ing)
            level_str = ai_result.get("risk_level", "").strip().capitalize()
            
            if level_str in ["Major", "Moderate"]:
                interactions.append({
                    "drug": med,
                    "level": level_str,
                    "mechanism": ai_result.get("mechanism", "")
                })
                if level_str == "Major": status_rank = max(status_rank, 2)
                else: status_rank = max(status_rank, 1)
                    
    # 5. Sonuç Derleme
    final_status = "CRITICAL" if status_rank == 2 else "WARNING" if status_rank == 1 else "SAFE"
    recommendation = "İlaç güvenle teslim edilebilir."
    if final_status == "CRITICAL":
        recommendation = "Kritik etkileşim tespit edildi! Reçete reddedilmeli veya hekim onayı alınmalıdır."
    elif final_status == "WARNING":
        recommendation = "Orta düzey risk. Hastayı yan etkiler konusunda uyararak teslim ediniz."
        
    return {
        "status": final_status,
        "recommendation": recommendation,
        "disease_warnings": disease_warnings,
        "food_warnings": food_warnings,
        "interactions": interactions,
        "warnings": general_warnings
    }


@router.post("/dispense-medication/{prescription_id}")
def dispense_medication(prescription_id: str):
    """React Dashboard üzerinden ilacın teslim edildiğini (satışını) veritabanına işler."""
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.prescriptions` 
        SET status = 'DISPENSED' 
        WHERE prescription_id = @rx_id
    """
    execute_bq_query(query, [bigquery.ScalarQueryParameter("rx_id", "STRING", prescription_id)])
    return {"status": "success", "message": f"#{prescription_id} numaralı reçete başarıyla teslim edildi."}