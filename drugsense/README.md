# DrugSense - Clinical Decision Support System (CDSS)

DrugSense is a **cloud-based Clinical Decision Support System (CDSS)** developed using **FastAPI** and **Google BigQuery**. The system is designed to support physicians and pharmacists throughout the medication prescribing and dispensing process by performing automated clinical safety checks.

DrugSense integrates multiple clinical knowledge sources into a single platform, including:

- Drug–Drug Interaction Analysis (DDInter)
- Drug–Food Interaction Detection
- Patient Allergy Screening
- Pediatric and Geriatric Risk Assessment
- Chronic Disease Contraindication Analysis
- Therapeutic Duplication Detection
- TİTCK-Approved Medication Database

The primary goal of the project is to reduce medication errors, improve patient safety, and provide a reliable clinical decision support system.

---

# 📂 Project Structure

```text
Grup-37/
├── drugsense/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── doctor.py          # Prescription workflow & safety engine
│   │   ├── pharmacist.py      # Medication dispensing validation
│   │   ├── patient.py         # Patient profile & adverse events
│   │   ├── drugs.py           # Drug search & alternative recommendations
│   │   └── emergency.py       # Break-glass authorization
│   │
│   ├── tests/
│   │   ├── test_doctor.py
│   │   ├── test_patient.py
│   │   ├── test_pharmacist.py
│   │   ├── test_safety_rules.py
│   │   └── test_scenarios.py
│   │
│   ├── data/
│   │   ├── drug_foods.csv
│   │   ├── drug_diseases.csv
│   │   ├── ddinter_data.csv
│   │   ├── interactions.csv
│   │   ├── titck_drugs.csv
│   │   ├── titck_ingredients.csv
│   │   ├── patients.csv
│   │   └── ...
│   │
│   ├── scripts/
│   │   ├── setup_bigquery.py
│   │   ├── upload_to_bq.py
│   │   ├── upload_drug_foods.py
│   │   └── download_all_data.py
│   │
│   ├── database.py
│   └── main.py
│
├── gcp_key.json
└── README.md
```

---

# 🗄️ Database Schema

DrugSense stores its clinical data inside the **Google BigQuery** dataset named **`drugsense_dataset`**.

## 1. drugs

Stores basic information about medications.

| Column | Type | Description |
|----------|--------|--------------------------------|
| drug_id | STRING | Unique drug identifier |
| drug_name | STRING | Commercial drug name |
| source | STRING | Data source (e.g. TİTCK) |
| active_ingredient | STRING | Active pharmaceutical ingredient |
| atc_code | STRING | ATC Classification Code |

---

## 2. ingredients

Contains inactive ingredients (excipients) for each medication.

| Column | Type | Description |
|----------|--------|--------------------------------|
| drug_id | STRING | Drug identifier |
| ingredient_name | STRING | Excipient name |

---

## 3. interactions

Contains clinically significant drug-drug interaction records.

| Column | Type | Description |
|----------|--------|--------------------------------|
| ingredient_1 | STRING | First active ingredient |
| ingredient_2 | STRING | Second active ingredient |
| risk_level | STRING | Major / Moderate / Minor |
| mechanism_description | STRING | Clinical mechanism |
| source | STRING | DDInter or custom clinical rules |

---

## 4. patient_allergies

Stores patient allergy information.

| Column | Type | Description |
|----------|--------|--------------------------------|
| patient_id | STRING | Patient identifier |
| allergen_name | STRING | Allergic substance |

---

## 5. patient_medications

Stores medications currently prescribed to patients.

| Column | Type | Description |
|----------|--------|--------------------------------|
| patient_id | STRING | Patient identifier |
| drug_id | STRING | Drug identifier |

---

# 🔍 Clinical Safety Checks

DrugSense automatically evaluates prescriptions using multiple safety rules.

- Drug–Drug Interaction Analysis
- Drug–Food Interaction Detection
- Allergy Screening
- Pediatric Risk Analysis
- Geriatric Risk Analysis
- Chronic Disease Contraindication Checks
- Therapeutic Duplication Detection
- Alternative Drug Recommendation

---

# 🚀 Installation

## 1. Install Required Packages

```bash
pip install fastapi uvicorn google-cloud-bigquery pandas pyarrow db-dtypes
```

---

## 2. Configure Google Cloud Credentials

Place your Google Cloud service account key inside the project root.

```
gcp_key.json
```

> **Note:** This file should be excluded using `.gitignore`.

---

## 3. Create the BigQuery Dataset

```bash
python scripts/setup_bigquery.py
```

---

## 4. Upload Clinical Data

Load medications, ingredients, drug interactions, and food interaction datasets into BigQuery.

```bash
python -m drugsense.scripts.setup_bigquery

python -m drugsense.scripts.upload_to_bq

python -m drugsense.scripts.upload_drug_foods
```

The upload scripts automatically prevent duplicate records.

---

## 5. Run the API

```bash
uvicorn main:app --reload
```

Open Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## 6. Run Unit Tests

```bash
python -m pytest drugsense/tests/test_safety_rules.py -v
```

---

# 📡 API Modules

| Module | Description |
|----------|--------------------------------|
| doctor.py | Prescription creation and clinical validation |
| pharmacist.py | Medication dispensing safety checks |
| patient.py | Patient profile and adverse event management |
| drugs.py | Drug search and alternative recommendation |
| emergency.py | Emergency ("Break Glass") authorization |

---

# 🛠️ Technology Stack

| Technology | Purpose |
|------------|------------------------------|
| FastAPI | REST API Framework |
| Google BigQuery | Cloud Database |
| Google Cloud Python SDK | BigQuery Client |
| Pandas | Data Processing |
| PyArrow | CSV Upload Support |
| DDInter | Drug Interaction Dataset |
| TİTCK | Turkish Approved Drug Database |
| Pytest | Unit Testing |

---

