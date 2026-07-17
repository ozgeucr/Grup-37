from pydantic import BaseModel
from typing import Optional, List


class DrugInfo(BaseModel):
    drug_id: str
    drug_name: str
    active_ingredient: str
    act_code: str
    excipients: List[str]


class MuadilResponse(BaseModel):
    original_drug: str
    active_ingredient: str
    alternative_drugs: List[str]


class AllergyRecord(BaseModel):
    allergen_name: str
    severity: str
    source: Optional[str] = "Sistem Kaydı"


class MedicationRecord(BaseModel):
    drug_name: str
    status: str
    prescribed_date: str
    prescribing_doctor: Optional[str] = "Bilinmiyor"


class PatientProfile(BaseModel):
    tc_no: str
    full_name: str
    age: int
    blood_type: Optional[str] = "Bilinmiyor"
    allergies: List[AllergyRecord] = []
    active_medications: List[MedicationRecord] = []
    past_medications: List[MedicationRecord] = []