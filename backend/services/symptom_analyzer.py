from config import Config
from services.triage import evaluate_triage, check_emergency

SYMPTOM_DATABASE = {
    "fever": {
        "conditions": ["Viral Upper Respiratory Infection", "Influenza", "Bacterial Infection", "Systemic Inflammatory Response"],
        "self_care": ["Maintain adequate fluid intake (water, electrolytes)", "Get restful sleep", "Wear lightweight clothing", "Monitor temperature every 4-6 hours"],
        "warning_signs": "Fever persisting over 3 days, temperature exceeding 103°F (39.4°C), stiff neck, confusion, or rash.",
        "doctor_advice": "Consult a healthcare professional if fever is accompanied by productive discolored cough, localized pain, or fails to respond to antipyretics."
    },
    "cough": {
        "conditions": ["Acute Viral Bronchitis", "Post-Nasal Drip", "Allergic Rhinitis / Asthma", "Gastroesophageal Reflux (GERD)"],
        "self_care": ["Warm fluids with honey and lemon", "Use a cool-mist room humidifier", "Avoid tobacco smoke and irritants", "Elevate head during sleep"],
        "warning_signs": "Coughing up blood or rust-colored sputum, severe wheezing, chest tightness, or unremitting night sweats.",
        "doctor_advice": "A cough lingering beyond 2-3 weeks should be professionally evaluated by a doctor for chest auscultation and chest imaging."
    },
    "headache": {
        "conditions": ["Tension-Type Headache", "Migraine Episode", "Sinus Congestion", "Dehydration / Eye Strain"],
        "self_care": ["Rest in a quiet, darkened room", "Apply a cold or warm compress to forehead or neck", "Ensure adequate hydration", "Practice neck and shoulder stretching"],
        "warning_signs": "Sudden explosive 'thunderclap' onset, headache following head trauma, accompanied by fever, stiff neck, or visual changes.",
        "doctor_advice": "Speak with a physician if headaches are increasing in frequency, intensity, or disrupt daily functional routines."
    },
    "fatigue": {
        "conditions": ["Post-Viral Fatigue", "Sleep Disturbance / Insomnia", "Iron Deficiency Anemia", "Thyroid Imbalance / Stress"],
        "self_care": ["Establish a consistent sleep schedule (7-9 hours)", "Engage in gentle daily physical activity", "Eat nutrient-dense whole foods", "Stay properly hydrated"],
        "warning_signs": "Extreme unshakeable exhaustion accompanied by unexplained weight loss, night sweats, swollen lymph nodes, or dark stool.",
        "doctor_advice": "Request routine laboratory blood panels (CBC, Thyroid TSH, Ferritin, Vitamin D) from your primary physician."
    },
    "sore throat": {
        "conditions": ["Viral Pharyngitis", "Streptococcal Pharyngitis (Strep Throat)", "Tonsillitis", "Dry Air Irritation"],
        "self_care": ["Warm saltwater gargles (1/2 tsp salt in warm water)", "Throat lozenges or honey", "Drink soothing herbal teas", "Use a cool-mist vaporizer"],
        "warning_signs": "Difficulty swallowing liquids, inability to open mouth fully (trismus), drooling, or high fever with white tonsillar exudates.",
        "doctor_advice": "A rapid strep throat swab by a doctor is recommended if white spots are visible on the tonsils or if symptoms are severe."
    },
    "stomach pain": {
        "conditions": ["Gastroenteritis (Stomach Bug)", "Dyspepsia / Acid Reflux", "Irritable Bowel Syndrome (IBS)", "Food Intolerance"],
        "self_care": ["Sip clear broths and electrolyte fluids", "Follow the BRAT diet (Bananas, Rice, Applesauce, Toast)", "Avoid fatty, spicy, or dairy foods", "Rest with a warm heating pad"],
        "warning_signs": "Severe focal right lower quadrant pain, rigid abdomen, vomiting blood, black tarry stools, or inability to keep fluids down.",
        "doctor_advice": "Persistent or sharp localized abdominal pain requires direct examination by a healthcare provider."
    }
}

def analyze_symptoms(symptoms_input: list[str] | str, duration: str = "", notes: str = "") -> dict:
    """
    Analyzes multiple symptoms and returns condition possibilities,
    self-care guidance, triage risk level, and medical warnings.
    """
    if isinstance(symptoms_input, str):
        symptom_list = [s.strip().lower() for s in symptoms_input.replace(",", ";").split(";") if s.strip()]
    else:
        symptom_list = [str(s).strip().lower() for s in symptoms_input if s]

    combined_text = " ".join(symptom_list) + " " + duration + " " + notes
    
    # 1. Check Triage
    triage_info = evaluate_triage(symptom_list, duration, "moderate")
    
    # 2. Match knowledge base conditions
    matched_conditions = []
    self_care_steps = set()
    warning_points = []
    doctor_points = []

    for sym in symptom_list:
        for key, data in SYMPTOM_DATABASE.items():
            if key in sym or sym in key:
                matched_conditions.extend(data["conditions"])
                for step in data["self_care"]:
                    self_care_steps.add(step)
                warning_points.append(f"For {key}: {data['warning_signs']}")
                doctor_points.append(data["doctor_advice"])

    # Fallbacks if symptoms are general or not in local dictionary
    if not matched_conditions:
        matched_conditions = ["General Non-Specific Symptom Presentation", "Mild Physiological Strain", "Early Stage Infection / Reaction"]
        self_care_steps.update([
            "Ensure 8 hours of restful sleep",
            "Maintain optimal daily fluid intake (2-3 liters)",
            "Track symptoms daily in a notebook",
            "Avoid strenuous over-exertion"
        ])
        warning_points.append("Sudden severe pain, high fever, shortness of breath, or neurological deficits.")
        doctor_points.append("Consult a doctor for a thorough clinical consultation if symptoms worsen or do not resolve within 48-72 hours.")

    # Deduplicate conditions
    unique_conditions = list(dict.fromkeys(matched_conditions))[:6]

    return {
        "success": True,
        "symptoms_evaluated": symptom_list,
        "triage": triage_info,
        "possible_associations": unique_conditions,
        "wording_disclaimer": "These symptoms can be associated with several conditions. A healthcare professional can determine the exact cause.",
        "general_self_care": list(self_care_steps)[:6],
        "warning_signs": warning_points[:4],
        "recommendation": " ".join(dict.fromkeys(doctor_points)) if doctor_points else "Schedule an appointment with a primary care clinician.",
        "disclaimer": Config.MEDICAL_DISCLAIMER
    }
