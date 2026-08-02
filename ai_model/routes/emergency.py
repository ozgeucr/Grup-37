from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from google.cloud import bigquery
from datetime import datetime
import logging
import uuid

from ..database import bq_client

router = APIRouter(tags=["Emergency Access"])

PROJECT_ID = bq_client.project
DATASET_ID = "drugsense_dataset"

logger = logging.getLogger(__name__)


class BreakGlassRequest(BaseModel):
    paramedic_tc: str
    patient_tc: str
    reason: str = "Acil Müdahale"


# -------------------------------------------------------
# ORTAK QUERY FONKSİYONU
# -------------------------------------------------------

def execute_query(query: str, params: list):
    job = bigquery.QueryJobConfig(query_parameters=params)
    return list(bq_client.query(query, job_config=job).result())


# -------------------------------------------------------
# AUDIT LOG
# -------------------------------------------------------

def log_emergency_action(actor_tc: str, patient_tc: str, details: str):

    try:

        query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.audit_logs`
        (
            log_id,
            actor_tc_no,
            action_type,
            target_tc_no,
            timestamp,
            details
        )

        VALUES
        (
            @log_id,
            @actor,
            'EMERGENCY_ACCESS',
            @patient,
            CURRENT_TIMESTAMP(),
            @details
        )
        """

        execute_query(
            query,
            [
                bigquery.ScalarQueryParameter(
                    "log_id",
                    "STRING",
                    f"EMG-{uuid.uuid4().hex[:8].upper()}",
                ),
                bigquery.ScalarQueryParameter(
                    "actor",
                    "STRING",
                    actor_tc,
                ),
                bigquery.ScalarQueryParameter(
                    "patient",
                    "STRING",
                    patient_tc,
                ),
                bigquery.ScalarQueryParameter(
                    "details",
                    "STRING",
                    details,
                ),
            ],
        )

        logger.info(f"Emergency log oluşturuldu -> {actor_tc}")

    except Exception as e:
        logger.error(f"Audit Log Hatası : {e}")


# -------------------------------------------------------
# BREAK GLASS
# -------------------------------------------------------

@router.post("/break-glass")
def emergency_break_glass(
    request: BreakGlassRequest,
    background_tasks: BackgroundTasks,
):

    print("=== BREAK GLASS ===")
    print(request)

    # ---------------------------------------------------
    # PARAMEDİK KONTROLÜ
    # ---------------------------------------------------

    paramedic = execute_query(
        f"""
        SELECT full_name, role
        FROM `{PROJECT_ID}.{DATASET_ID}.users`
        WHERE CAST(tc_no AS STRING)=@tc
        LIMIT 1
        """,
        [
            bigquery.ScalarQueryParameter(
                "tc",
                "STRING",
                request.paramedic_tc,
            )
        ],
    )

    if not paramedic:
        raise HTTPException(
            status_code=404,
            detail="Paramedik bulunamadı."
        )

    if paramedic[0].role.upper() != "PARAMEDIC":
        raise HTTPException(
            status_code=403,
            detail="Bu işlem yalnızca paramedikler tarafından yapılabilir."
        )

    paramedic_name = paramedic[0].full_name

    # ---------------------------------------------------
    # HASTA KONTROLÜ
    # ---------------------------------------------------

    patient = execute_query(
        f"""
        SELECT
            full_name,
            age,
            gender,
            blood_type,
            phone
        FROM `{PROJECT_ID}.{DATASET_ID}.patients`
        WHERE CAST(tc_no AS STRING)=@tc
        LIMIT 1
        """,
        [
            bigquery.ScalarQueryParameter(
                "tc",
                "STRING",
                request.patient_tc,
            )
        ],
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Hasta bulunamadı."
        )

    # ---------------------------------------------------
    # KRONİK HASTALIKLAR
    # ---------------------------------------------------

    diseases = execute_query(
        f"""
        SELECT
            disease_name,
            diagnosed_date
        FROM `{PROJECT_ID}.{DATASET_ID}.patient_diseases`
        WHERE CAST(tc_no AS STRING)=@tc
        """,
        [
            bigquery.ScalarQueryParameter(
                "tc",
                "STRING",
                request.patient_tc,
            )
        ],
    )

    # ---------------------------------------------------
    # ALERJİLER
    # ---------------------------------------------------

    allergies = execute_query(
        f"""
        SELECT
            allergen_name,
            severity
        FROM `{PROJECT_ID}.{DATASET_ID}.patient_allergies`
        WHERE CAST(tc_no AS STRING)=@tc
        """,
        [
            bigquery.ScalarQueryParameter(
                "tc",
                "STRING",
                request.patient_tc,
            )
        ],
    )

    # ---------------------------------------------------
    # AKTİF İLAÇLAR
    # ---------------------------------------------------

    medications = execute_query(
        f"""
        SELECT
            drug_name,
            prescribed_date,
            prescribing_doctor
        FROM `{PROJECT_ID}.{DATASET_ID}.patient_medications`
        WHERE CAST(tc_no AS STRING)=@tc
        AND status='Aktif'
        ORDER BY prescribed_date DESC
        """,
        [
            bigquery.ScalarQueryParameter(
                "tc",
                "STRING",
                request.patient_tc,
            )
        ],
    )

    # ---------------------------------------------------
    # OPERASYONLAR (TABLO YOKSA BOŞ)
    # ---------------------------------------------------

    surgeries = []

    try:

        surgeries = execute_query(
            f"""
            SELECT
                surgery_name,
                surgery_date
            FROM `{PROJECT_ID}.{DATASET_ID}.patient_surgeries`
            WHERE CAST(tc_no AS STRING)=@tc
            """,
            [
                bigquery.ScalarQueryParameter(
                    "tc",
                    "STRING",
                    request.patient_tc,
                )
            ],
        )

    except Exception:
        pass

    # ---------------------------------------------------
    # LOG
    # ---------------------------------------------------

    background_tasks.add_task(
        log_emergency_action,
        request.paramedic_tc,
        request.patient_tc,
        f"{paramedic_name} acil erişim gerçekleştirdi. Sebep: {request.reason}",
    )

    p = patient[0]

    # ---------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------

    return {

        "status": "EMERGENCY_OVERRIDE_ACTIVE",

        "warning": "Bu bilgiler yalnızca acil müdahale amacıyla görüntülenmektedir.",

        "patient": {

            "tc_no": request.patient_tc,
            "full_name": p.full_name,
            "age": p.age,
            "gender": p.gender,
            "blood_type": p.blood_type,
            "phone": p.phone,

        },

        "vital_data": {

            "chronic_diseases": [

                {
                    "disease": d.disease_name,
                    "diagnosed_date": str(d.diagnosed_date)
                }

                for d in diseases

            ],

            "allergies": [

                {
                    "allergen": a.allergen_name,
                    "severity": a.severity
                }

                for a in allergies

            ],

            "active_medications": [

                {
                    "drug": m.drug_name,
                    "prescribed_date": str(m.prescribed_date),
                    "doctor": m.prescribing_doctor
                }

                for m in medications

            ],

            "surgeries": [

                {
                    "surgery": s.surgery_name,
                    "date": str(s.surgery_date)
                }

                for s in surgeries

            ]

        }

    }