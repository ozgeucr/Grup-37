import joblib
import numpy as np
import os

# Model dosyalarının yolu
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model")

# Modeli ve encoder'ları yükle
model = joblib.load(os.path.join(MODEL_DIR, "drugsense_final_model.pkl"))
le_a = joblib.load(os.path.join(MODEL_DIR, "le_drug_a.pkl"))
le_b = joblib.load(os.path.join(MODEL_DIR, "le_drug_b.pkl"))
le_level = joblib.load(os.path.join(MODEL_DIR, "le_level.pkl"))
le_atc = joblib.load(os.path.join(MODEL_DIR, "le_atc.pkl"))
atc_map = joblib.load(os.path.join(MODEL_DIR, "atc_map.pkl"))
drug_interaction_count = joblib.load(os.path.join(MODEL_DIR, "drug_interaction_count.pkl"))
drug_major_count = joblib.load(os.path.join(MODEL_DIR, "drug_major_count.pkl"))
interaction_rules = joblib.load(os.path.join(MODEL_DIR, "interaction_rules.pkl"))

SUFFIXES = ["azole","mab","statin","pril","sartan","mycin",
            "cillin","pam","lam","pine","olol","ide"]

def predict_interaction(drug_a: str, drug_b: str) -> dict:
    """
    İki ilaç arasındaki etkileşim riskini tahmin eder.

    Parametreler:
        drug_a (str): Birinci ilacın etken madde adı (İngilizce)
        drug_b (str): İkinci ilacın etken madde adı (İngilizce)

    Döndürür:
        dict: {
            "drug_a": str,
            "drug_b": str,
            "risk_level": "Major" | "Moderate" | "Minor",
            "confidence": str,
            "mechanism": str,
            "atc_a": str,
            "atc_b": str,
            "method": "Kural Tabanlı" | "ML Model",
            "color": "red" | "orange" | "green"
        }

    Kullanım:
        from predict import predict_interaction
        result = predict_interaction("Ibuprofen", "Warfarin")
        print(result["risk_level"])  # "Major"
    """
    color_map = {"Major": "red", "Moderate": "orange", "Minor": "green"}

    # 1. Önce kural tablosuna bak
    for key in [(drug_a, drug_b), (drug_b, drug_a)]:
        if key in interaction_rules:
            rule = interaction_rules[key]
            return {
                "drug_a": drug_a,
                "drug_b": drug_b,
                "risk_level": rule["risk_level"],
                "confidence": "100%",
                "mechanism": rule["mechanism"],
                "atc_a": atc_map.get(drug_a, "Bulunamadı"),
                "atc_b": atc_map.get(drug_b, "Bulunamadı"),
                "method": "Kural Tabanlı",
                "color": color_map.get(rule["risk_level"], "gray")
            }

    # 2. Kural yoksa ML modeli kullan
    try:
        a_enc = le_a.transform([drug_a])[0]
    except:
        a_enc = 0
    try:
        b_enc = le_b.transform([drug_b])[0]
    except:
        b_enc = 0

    degree_a = drug_interaction_count.get(drug_a, 0)
    degree_b = drug_interaction_count.get(drug_b, 0)
    major_rate_a = drug_major_count.get(drug_a, 0) / degree_a if degree_a > 0 else 0
    major_rate_b = drug_major_count.get(drug_b, 0) / degree_b if degree_b > 0 else 0

    id_a = int("".join(filter(str.isdigit, drug_a)) or 0)
    id_b = int("".join(filter(str.isdigit, drug_b)) or 0)

    atc_a = atc_map.get(drug_a)
    atc_b = atc_map.get(drug_b)
    atc_a_cat = atc_a[0] if atc_a else "Unknown"
    atc_b_cat = atc_b[0] if atc_b else "Unknown"

    try:
        atc_a_enc = le_atc.transform([atc_a_cat])[0]
    except:
        atc_a_enc = 0
    try:
        atc_b_enc = le_atc.transform([atc_b_cat])[0]
    except:
        atc_b_enc = 0

    features = [a_enc, b_enc, id_a, id_b,
                degree_a, degree_b, major_rate_a, major_rate_b,
                atc_a_enc, atc_b_enc]

    for s in SUFFIXES:
        features.append(int(drug_a.lower().endswith(s)))
    for s in SUFFIXES:
        features.append(int(drug_b.lower().endswith(s)))

    features_array = np.array(features).reshape(1, -1)
    prediction = model.predict(features_array)[0]
    probabilities = model.predict_proba(features_array)[0]
    risk = le_level.inverse_transform([prediction])[0]
    confidence = max(probabilities)

    return {
        "drug_a": drug_a,
        "drug_b": drug_b,
        "risk_level": risk,
        "confidence": f"{confidence:.1%}",
        "mechanism": "DDInter veritabanından ML modeli ile tahmin edildi.",
        "atc_a": atc_a or "Bulunamadı",
        "atc_b": atc_b or "Bulunamadı",
        "method": "ML Model",
        "color": color_map.get(risk, "gray")
    }
