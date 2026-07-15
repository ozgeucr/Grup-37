from fastapi import APIRouter, HTTPException
from google.cloud import bigquery
from ..database import bq_client
from ..models import PatientProfile, AllergyRecord, MedicationRecord

router = APIRouter()


@router.get("/profile/{tc_no}", response_model=PatientProfile)
def get_patient_profile(tc_no: str):
    if bq_client is None:
        raise HTTPException(
            status_code=500,
            detail="BigQuery bağlantısı kurulamadı."
        )

    # 1. Hasta bilgisi
    patient_query = f"""
    SELECT *
    FROM `{bq_client.project}.drugsense_dataset.patients`
    WHERE tc_no = @tc_no
    LIMIT 1
    """

    patient_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "tc_no",
                "STRING",
                tc_no
            )
        ]
    )

    patient_rows = list(
        bq_client.query(
            patient_query,
            job_config=patient_config
        ).result()
    )

    if not patient_rows:
        raise HTTPException(
            status_code=404,
            detail="Hasta bulunamadı."
        )

    patient = patient_rows[0]

    # 2. Alerjiler
    allergy_query = f"""
    SELECT allergen_name, severity, source
    FROM `{bq_client.project}.drugsense_dataset.patient_allergies`
    WHERE tc_no = @tc_no
    """

    allergy_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "tc_no",
                "STRING",
                tc_no
            )
        ]
    )

    allergy_rows = bq_client.query(
        allergy_query,
        job_config=allergy_config
    ).result()

    allergies = [
        AllergyRecord(
            allergen_name=row.allergen_name,
            severity=row.severity,
            source=row.source
        )
        for row in allergy_rows
    ]

    # 3. Aktif ve Geçmiş İlaçlar
    medication_query = f"""
    SELECT *
    FROM `{bq_client.project}.drugsense_dataset.patient_medications`
    WHERE tc_no = @tc_no
    """

    medication_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "tc_no",
                "STRING",
                tc_no
            )
        ]
    )

    medication_rows = bq_client.query(
        medication_query,
        job_config=medication_config
    ).result()

    active_medications = []
    past_medications = []

    for row in medication_rows:
        medication = MedicationRecord(
            drug_name=row.drug_name,
            status=row.status,
            prescribed_date=str(row.prescribed_date),
            prescribing_doctor=row.prescribing_doctor
        )

        if row.status.lower() == "aktif":
            active_medications.append(medication)
        else:
            past_medications.append(medication)

    return PatientProfile(
        tc_no=str(patient.tc_no),
        full_name=patient.full_name,
        age=patient.age,
        blood_type=patient.blood_type,
        allergies=allergies,
        active_medications=active_medications,
        past_medications=past_medications
    )