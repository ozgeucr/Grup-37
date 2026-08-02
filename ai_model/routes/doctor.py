from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from google.cloud import bigquery
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from functools import lru_cache
import logging
import uuid

from ..database import bq_client
from .patient import get_patient_profile

router = APIRouter(tags=["Prescription & Analysis"])
logger = logging.getLogger(__name__)

# Konsolda çalışan yapıyı garantilemek için proje adını sabitliyoruz
PROJECT_ID = "drugsense-503118"
DATASET_ID = "drugsense_dataset"

# --- STATÜ ÖNCELİK TABLOSU ---
STATUS_PRIORITY = {
    "SAFE": 0,
    "MANUAL_REVIEW": 1,
    "OVERRIDDEN_BY_DOCTOR": 2,
    "WARNING": 3,
    "CRITICAL": 4
}

def get_highest_status(current_status: str, new_status: str) -> str:
    """İki statüden önceliği en yüksek olanı (sayısal olarak) döndürür."""
    if STATUS_PRIORITY.get(new_status, 0) > STATUS_PRIORITY.get(current_status, 0):
        return new_status
    return current_status


# ==========================================
# YAPAY ZEKA MODELİ ENTEGRASYONU
# ==========================================
try:
    from ai_model.api.predict import predict_interaction
    AI_MODEL_LOADED = True
except ImportError as e:
    logger.critical(f"YAPAY ZEKA MODELİ YÜKLENEMEDİ! Fallback devrede. Hata: {e}")
    AI_MODEL_LOADED = False
    
    def predict_interaction(drug_a: str, drug_b: str) -> dict:
        return {"risk_level": "Unknown", "mechanism": "AI Model yüklenemedi.", "method": "Fallback", "confidence": 0.0}

@lru_cache(maxsize=1000)
def cached_predict(drug_a: str, drug_b: str) -> dict:
    sorted_drugs = sorted([drug_a.lower().strip(), drug_b.lower().strip()])
    try:
        result = predict_interaction(sorted_drugs[0], sorted_drugs[1])
        if isinstance(result, dict):
            if result.get("confidence") is None:
                result["confidence"] = 0.0
        return result
    except Exception as e:
        logger.error(f"AI Tahmin Hatası ({drug_a} - {drug_b}): {e}")
        return {"risk_level": "Unknown", "mechanism": f"Tahmin sırasında hata: {e}", "method": "Fallback", "confidence": 0.0}


# ==========================================
# VERİ MODELLERİ (PYDANTIC)
# ==========================================
class PrescriptionRequest(BaseModel):
    tc_no: str = Field(alias="patient_id")
    doctor_tc: str = Field(alias="doctor_id")
    new_drug_name: str
    current_cart: List[str] = Field(default_factory=list) 
    accept_responsibility: bool = False
    override_reason: Optional[str] = None

    class Config:
        populate_by_name = True

class SaveDrugItem(BaseModel):
    drug_name: str
    status: str
    override_reason: Optional[str] = None

class SavePrescriptionRequest(BaseModel):
    tc_no: str = Field(alias="patient_id")
    doctor_tc: str = Field(alias="doctor_id")
    drugs: List[SaveDrugItem]

    class Config:
        populate_by_name = True

class ApproveSideEffectRequest(BaseModel):
    report_id: str
    tc_no: str
    allergen_name: str
    severity: str

class AddAllergyRequest(BaseModel):
    tc_no: str
    doctor_tc: str
    allergen_name: str
    severity: str


# ==========================================
# VERİTABANI YARDIMCI FONKSİYONLARI
# ==========================================
def execute_bq_query(query: str, parameters: list = None) -> list:
    if not bq_client:
        raise HTTPException(status_code=500, detail="BigQuery bağlantısı kurulamadı.")
    
    job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
    try:
        return list(bq_client.query(query, job_config=job_config).result())
    except Exception as e:
        logger.error(f"BigQuery Sorgu Hatası: {e}")
        raise HTTPException(status_code=500, detail="Veritabanı işlemi sırasında hata oluştu.")

def get_bulk_drug_ingredients(drug_names: List[str]) -> Dict[str, str]:
    if not drug_names:
        return {}
    lower_drugs = [d.lower().strip() for d in drug_names]
    query = f"""
        SELECT LOWER(drug_name) as d_name, LOWER(active_ingredient) as a_ing 
        FROM `{PROJECT_ID}.{DATASET_ID}.drugs`
        WHERE LOWER(drug_name) IN UNNEST(@drug_list) OR LOWER(active_ingredient) IN UNNEST(@drug_list)
    """
    params = [bigquery.ArrayQueryParameter("drug_list", "STRING", lower_drugs)]
    res = execute_bq_query(query, params)
    
    result_dict = {}
    for row in res:
        if row.d_name in lower_drugs: 
            result_dict[row.d_name] = row.a_ing
        if row.a_ing in lower_drugs:  
            result_dict[row.a_ing] = row.a_ing
    return result_dict


# ==========================================
# İŞ MANTIĞI & ANALİZ YARDIMCILARI
# ==========================================
def analyze_patient_compatibility(new_ing: str, patient: Any, patient_active_ings: List[str]) -> Dict[str, Any]:
    status_info = {"overall_status": "SAFE", "is_prescription_blocked": False, "suggestions": []}
    ing_lower = new_ing.lower()

    if ing_lower in [ing.lower() for ing in patient_active_ings if ing]:
        status_info["overall_status"] = get_highest_status(status_info["overall_status"], "WARNING")
        status_info["suggestions"].append("DUPLİKASYON UYARISI: Hasta veya reçete sepeti halihazırda bu etken maddeyi içermektedir.")

    if patient.age:
        if patient.age < 16 and "acetylsalicylic acid" in ing_lower:
            status_info["suggestions"].append("KRİTİK UYARI (Pediatrik): 16 yaş altı Reye Sendromu riski.")
            status_info["overall_status"] = get_highest_status(status_info["overall_status"], "CRITICAL")
            status_info["is_prescription_blocked"] = True
        elif patient.age >= 65:
            nsaids = ["dexketoprofen", "flurbiprofen", "naproxen", "ibuprofen", "diclofenac"]
            if any(n in ing_lower for n in nsaids):
                status_info["suggestions"].append("Geriatrik Uyarı (65+): NSAİİ kullanımı mide kanaması riskini artırır.")
                status_info["overall_status"] = get_highest_status(status_info["overall_status"], "WARNING")
            if "tramadol" in ing_lower:
                status_info["suggestions"].append("Geriatrik Uyarı (65+): Solunum depresyonu ve düşme riski artar.")
                status_info["overall_status"] = get_highest_status(status_info["overall_status"], "WARNING")

    for allergy in patient.allergies:
        if allergy.allergen_name.lower() in ing_lower:
            status_info["suggestions"].append(f"KRİTİK ALERJİ: {allergy.allergen_name} alerjisi tespit edildi!")
            status_info["overall_status"] = get_highest_status(status_info["overall_status"], "CRITICAL")
            status_info["is_prescription_blocked"] = True

    disease_codes = [d.icd10_code for d in patient.diseases if hasattr(d, 'icd10_code')]
    if disease_codes:
        query = f"""
            SELECT disease_name, risk_level, warning_message
            FROM `{PROJECT_ID}.{DATASET_ID}.drug_diseases`
            WHERE LOWER(active_ingredient) = @new_ing AND icd10_code IN UNNEST(@disease_codes)
        """
        params = [
            bigquery.ScalarQueryParameter("new_ing", "STRING", ing_lower),
            bigquery.ArrayQueryParameter("disease_codes", "STRING", disease_codes)
        ]
        conflicts = execute_bq_query(query, params)
        for row in conflicts:
            level = row.risk_level.strip().capitalize()
            warning_text = f"Hastalık Çatışması ({row.disease_name}): {row.warning_message}"
            if level == "Major":
                status_info["overall_status"] = get_highest_status(status_info["overall_status"], "CRITICAL")
                status_info["is_prescription_blocked"] = True
                status_info["suggestions"].append(warning_text)
            elif level == "Moderate":
                status_info["overall_status"] = get_highest_status(status_info["overall_status"], "WARNING")
                status_info["suggestions"].append(warning_text)

    food_query = f"""
        SELECT interacting_food, risk_level, warning_message 
        FROM `{PROJECT_ID}.{DATASET_ID}.drug_foods` 
        WHERE LOWER(active_ingredient) = @new_ing
    """
    food_params = [bigquery.ScalarQueryParameter("new_ing", "STRING", ing_lower)]
    food_interactions = execute_bq_query(food_query, food_params)
    for fw in food_interactions:
        food_level = fw.risk_level.strip().capitalize()
        status_info["suggestions"].append(f"Besin Etkileşimi [{food_level}] ({fw.interacting_food}): {fw.warning_message}")

    return status_info


# ==========================================
# API ENDPOINT'LERİ
# ==========================================
@router.post("/prescribe-and-analyze")
def prescribe_and_analyze(request: PrescriptionRequest):
    try:
        patient = get_patient_profile(request.tc_no)
    except Exception as e:
        logger.error(f"Hasta profili hatası: {e}")
        raise HTTPException(status_code=404, detail="Hasta profili bulunamadı veya alınamadı.")

    patient_drug_names = [med.drug_name for med in patient.active_medications] + request.current_cart
    all_drugs_to_check = patient_drug_names + [request.new_drug_name]
    ingredients_dict = get_bulk_drug_ingredients(all_drugs_to_check)
    
    new_ing = ingredients_dict.get(request.new_drug_name.lower().strip())
    
    if not new_ing:
        return {
            "patient": patient.full_name,
            "new_drug": request.new_drug_name,
            "overall_status": "MANUAL_REVIEW",
            "system_note": "İlaç tanımlanamadı.", 
            "recommendation": "Bu ilaç (veya etken madde) veritabanında bulunamadı. Lütfen klinik inceleme yapın."
        }

    report = {
        "patient": patient.full_name,
        "new_drug": request.new_drug_name,
        "overall_status": "SAFE",
        "is_prescription_blocked": False,
        "polypharmacy": len(patient_drug_names) >= 5,
        "suggestions": [],
        "recommendation": "İlaç güvenle reçeteye eklenebilir."
    }

    if report["polypharmacy"]:
        report["suggestions"].append("Hastada polifarmasi riski (5+ ilaç kullanımı) bulunmaktadır.")

    patient_ings = [ingredients_dict.get(drug.lower().strip()) for drug in patient_drug_names if ingredients_dict.get(drug.lower().strip())]
    patient_analysis = analyze_patient_compatibility(new_ing, patient, patient_ings)
    
    report["suggestions"].extend(patient_analysis["suggestions"])
    report["overall_status"] = get_highest_status(report["overall_status"], patient_analysis["overall_status"])
    if patient_analysis["is_prescription_blocked"]:
        report["is_prescription_blocked"] = True

    for med in patient_drug_names:
        med_ing = ingredients_dict.get(med.lower().strip())
        if not med_ing or new_ing.lower() == med_ing.lower():
            continue
            
        ai_result = cached_predict(new_ing, med_ing)
        level_str = ai_result.get("risk_level", "").strip().capitalize()
        mechanism = ai_result.get("mechanism", "Mekanizma bilgisi bulunamadı.")
        
        raw_conf = ai_result.get("confidence", 0.0)
        conf_val = 0.0
        
        if raw_conf is not None:
            if isinstance(raw_conf, (int, float)):
                conf_val = float(raw_conf)
            elif isinstance(raw_conf, str):
                try:
                    # İçinde '%' geçiyorsa temizle ve ilk parçayı al, float'a çevir
                    cleaned_str = raw_conf.split('%')[0].strip()
                    conf_val = float(cleaned_str)
                    # Eğer 0-1 arasında değil de yüzde olarak (örn: 97.4) geldiyse 100'e böl ki tutarlı olsun
                    if conf_val > 1.0:
                        conf_val = conf_val / 100.0
                except ValueError:
                    conf_val = 0.0
        conf_text = f" [%{int(conf_val*100)} Güven]" if conf_val else ""
        
        if level_str == "Major":
            report["overall_status"] = get_highest_status(report["overall_status"], "CRITICAL")
            report["is_prescription_blocked"] = True
            report["suggestions"].append(f"🤖 AI KRİTİK UYARI: {request.new_drug_name} ile {med} arasında MAJÖR etkileşim! ({mechanism}){conf_text}")
        elif level_str == "Moderate":
            report["overall_status"] = get_highest_status(report["overall_status"], "WARNING")
            report["suggestions"].append(f"🤖 AI UYARI: {request.new_drug_name} ile {med} arasında ORTA düzey etkileşim. ({mechanism}){conf_text}")

    if report["is_prescription_blocked"]:
        if not request.accept_responsibility:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"DİKKAT: {request.new_drug_name} engellendi. İlacı listeye eklemek için sorumluluk onayını vermeli ve gerekçe sunmalısınız."
            )
        if not request.override_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Gerekçe (override_reason) girmek zorundasınız."
            )
            
        report["is_prescription_blocked"] = False
        report["overall_status"] = "OVERRIDDEN_BY_DOCTOR"
        report["recommendation"] = f"Hekim inisiyatifiyle onaylandı. Gerekçe: {request.override_reason}"

    return report


@router.post("/save-prescription", status_code=status.HTTP_201_CREATED)
def save_prescription_batch(request: SavePrescriptionRequest):
    if not request.drugs:
        raise HTTPException(status_code=400, detail="Reçete sepeti boş olamaz.")
        
    prescription_id = f"RX-{uuid.uuid4().hex[:8].upper()}"
    current_time = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now().strftime("%Y-%m-%d") # Temiz tarih formatı (STRING)
    
    try:
        for item in request.drugs:
            rx_query = f"""
                INSERT INTO `{PROJECT_ID}.{DATASET_ID}.prescriptions`
                (prescription_id, doctor_tc_no, tc_no, drug_name, status, override_reason, created_at)
                VALUES (@p_id, @doc_tc, @tc_no, @drug, @status, @reason, CAST(@created_at AS TIMESTAMP))
            """
            rx_params = [
                bigquery.ScalarQueryParameter("p_id", "STRING", prescription_id),
                bigquery.ScalarQueryParameter("doc_tc", "STRING", request.doctor_tc.strip()),
                bigquery.ScalarQueryParameter("tc_no", "STRING", request.tc_no.strip()),
                bigquery.ScalarQueryParameter("drug", "STRING", item.drug_name),
                bigquery.ScalarQueryParameter("status", "STRING", item.status),
                bigquery.ScalarQueryParameter("reason", "STRING", item.override_reason or ""),
                bigquery.ScalarQueryParameter("created_at", "STRING", current_time),
            ]
            execute_bq_query(rx_query, rx_params)
            
            # medication_id alanı tablonuzda REQUIRED ise hata vermemesi için dinamik üretiliyor
            medication_id = f"M{uuid.uuid4().hex[:7].upper()}"
            
            med_query = f"""
                INSERT INTO `{PROJECT_ID}.{DATASET_ID}.patient_medications`
                (medication_id, tc_no, drug_name, status, prescribed_date, prescribing_doctor)
                SELECT @med_id, CAST(@tc_no AS INT64), @drug_name, 'Aktif', @date, full_name
                FROM `{PROJECT_ID}.{DATASET_ID}.users`
                WHERE CAST(tc_no AS STRING) = @doctor_tc LIMIT 1
            """
            med_params = [
                bigquery.ScalarQueryParameter("med_id", "STRING", medication_id),
                bigquery.ScalarQueryParameter("tc_no", "STRING", request.tc_no.strip()),
                bigquery.ScalarQueryParameter("drug_name", "STRING", item.drug_name),
                bigquery.ScalarQueryParameter("date", "STRING", today_str),
                bigquery.ScalarQueryParameter("doctor_tc", "STRING", request.doctor_tc.strip())
            ]
            execute_bq_query(med_query, med_params)
            
        return {"status": "success", "message": "Reçete başarıyla imzalandı ve sisteme kaydedildi.", "prescription_id": prescription_id}
    except Exception as e:
        logger.error(f"Reçete kayıt hatası: {e}")
        raise HTTPException(status_code=500, detail="Veritabanı işlemi sırasında hata oluştu.")

@router.get("/stats/{doctor_tc}")
def get_doctor_stats(doctor_tc: str):
    clean_tc = doctor_tc.strip()
    query = f"""
        SELECT 
            COUNT(DISTINCT prescription_id) as total_rx,
            COUNT(DISTINCT CASE WHEN DATE(created_at) = CURRENT_DATE() THEN prescription_id END) as today_rx,
            COUNT(CASE WHEN status IN ('WARNING', 'CRITICAL') THEN 1 END) as total_warnings,
            COUNT(CASE WHEN status = 'CRITICAL' THEN 1 END) as critical_warnings,
            COUNT(DISTINCT tc_no) as unique_patients,
            COUNT(DISTINCT CASE WHEN DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN tc_no END) as recent_patients,
            COUNT(CASE WHEN status IN ('SAFE', 'OVERRIDDEN_BY_DOCTOR') THEN 1 END) as safe_rx
        FROM `{PROJECT_ID}.{DATASET_ID}.prescriptions`
        WHERE CAST(doctor_tc_no AS STRING) = @doctor_tc
    """
    params = [bigquery.ScalarQueryParameter("doctor_tc", "STRING", clean_tc)]
    res = execute_bq_query(query, params)
    
    if not res:
        return {
            "active_prescriptions": {"value": "0", "sub": "+0 bugün"},
            "warnings": {"value": "0", "sub": "0 kritik"},
            "scanned_patients": {"value": "0", "sub": "+0 bu hafta"},
            "ai_score": {"value": "%100", "sub": "AI Engine v3.2"}
        }
        
    row = res[0]
    total_rx = row.total_rx or 0
    safe_rx = row.safe_rx or 0
    ai_score = round((safe_rx / total_rx * 100), 1) if total_rx > 0 else 100.0

    return {
        "active_prescriptions": {"value": str(total_rx), "sub": f"+{row.today_rx or 0} bugün"},
        "warnings": {"value": str(row.total_warnings or 0), "sub": f"{row.critical_warnings or 0} kritik"},
        "scanned_patients": {"value": str(row.unique_patients or 0), "sub": f"+{row.recent_patients or 0} bu hafta"},
        "ai_score": {"value": f"%{ai_score}", "sub": "AI Engine v3.2"}
    }


@router.get("/patient-history/{doctor_tc}/{tc_no}")
def get_doctor_filtered_history(doctor_tc: str, tc_no: str):
    clean_doc = doctor_tc.strip()
    clean_pat = tc_no.strip()
    query = f"""
        SELECT p.prescription_id, p.drug_name, p.status, p.created_at,
        DATE_DIFF(CURRENT_DATE(), DATE(p.created_at), DAY) as days_passed
        FROM `{PROJECT_ID}.{DATASET_ID}.prescriptions` p
        WHERE CAST(p.tc_no AS STRING) = @tc_no 
        AND CAST(p.doctor_tc_no AS STRING) = @doctor_tc
        ORDER BY p.created_at DESC
    """
    params = [
        bigquery.ScalarQueryParameter("tc_no", "STRING", clean_pat),
        bigquery.ScalarQueryParameter("doctor_tc", "STRING", clean_doc)
    ]
    rx_rows = execute_bq_query(query, params)
    
    history_records = []
    for row in rx_rows:
        days = row.days_passed
        if days == 0:
            time_label = "Bugün"
        elif days == 1:
            time_label = "Dün"
        elif days < 7:
            time_label = f"{days} gün önce"
        elif days < 30:
            time_label = f"{days // 7} hafta önce"
        else:
            time_label = f"{days} gün önce"
            
        history_records.append({
            "prescription_id": row.prescription_id,
            "drug_name": row.drug_name,
            "status": row.status,
            "time_label": time_label,
            "created_at": str(row.created_at)
        })

    return {"filtered_prescriptions": history_records}


@router.post("/approve-side-effect")
def approve_side_effect(request: ApproveSideEffectRequest):
    try:
        # Çakışma kontrolü: Aynı alerji daha önce eklenmiş mi?
        check_query = f"""
            SELECT 1 FROM `{PROJECT_ID}.{DATASET_ID}.patient_allergies`
            WHERE CAST(tc_no AS STRING) = @tc_no AND LOWER(allergen_name) = LOWER(@allergen_name)
            LIMIT 1
        """
        check_params = [
            bigquery.ScalarQueryParameter("tc_no", "STRING", request.tc_no.strip()),
            bigquery.ScalarQueryParameter("allergen_name", "STRING", request.allergen_name.strip())
        ]
        existing = execute_bq_query(check_query, check_params)
        if existing:
            raise HTTPException(status_code=409, detail="Bu alerji kaydı hastanın profilinde zaten mevcut.")

        # DÜZELTME: Doğru kolon adı olan verification_status kullanıldı
        update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.side_effect_reports` 
            SET verification_status = 'APPROVED' 
            WHERE report_id = @report_id
        """
        execute_bq_query(update_query, [bigquery.ScalarQueryParameter("report_id", "STRING", request.report_id.strip())])

        insert_allergy_query = f"""
            INSERT INTO `{PROJECT_ID}.{DATASET_ID}.patient_allergies` (tc_no, allergen_name, severity, source)
            VALUES (@tc_no, @allergen_name, @severity, 'Doktor Onaylı Bildirim')
        """
        allergy_params = [
            bigquery.ScalarQueryParameter("tc_no", "STRING", request.tc_no.strip()),
            bigquery.ScalarQueryParameter("allergen_name", "STRING", request.allergen_name.strip()),
            bigquery.ScalarQueryParameter("severity", "STRING", request.severity),
        ]
        execute_bq_query(insert_allergy_query, allergy_params)

        return {"status": "success", "message": "Bildirim onaylandı ve hastanın resmi alerji listesine eklendi."}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Alerji onaylanırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail="İşlem başarısız oldu.")


@router.post("/add-allergy")
def add_patient_allergy(request: AddAllergyRequest):
    try:
        check_query = f"""
            SELECT 1 FROM `{PROJECT_ID}.{DATASET_ID}.patient_allergies`
            WHERE CAST(tc_no AS STRING) = @tc_no AND LOWER(allergen_name) = LOWER(@allergen_name)
            LIMIT 1
        """
        check_params = [
            bigquery.ScalarQueryParameter("tc_no", "STRING", request.tc_no.strip()),
            bigquery.ScalarQueryParameter("allergen_name", "STRING", request.allergen_name.strip())
        ]
        existing = execute_bq_query(check_query, check_params)
        if existing:
            raise HTTPException(status_code=409, detail="Bu alerji kaydı hastanın profilinde zaten mevcut.")

        query = f"""
            INSERT INTO `{PROJECT_ID}.{DATASET_ID}.patient_allergies` (tc_no, allergen_name, severity, source)
            VALUES (@tc_no, @allergen_name, @severity, @source)
        """
        params = [
            bigquery.ScalarQueryParameter("tc_no", "STRING", request.tc_no.strip()),
            bigquery.ScalarQueryParameter("allergen_name", "STRING", request.allergen_name.strip()),
            bigquery.ScalarQueryParameter("severity", "STRING", request.severity),
            bigquery.ScalarQueryParameter("source", "STRING", f"Doktor Girişi (TC: {request.doctor_tc.strip()})"),
        ]
        execute_bq_query(query, params)

        return {"status": "success", "message": f"{request.allergen_name} alerjisi hastanın profiline başarıyla eklendi."}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Doktor tarafından alerji eklenirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail="Alerji eklenirken bir hata oluştu.")