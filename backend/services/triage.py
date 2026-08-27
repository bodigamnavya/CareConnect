import re

# Red-flag emergency symptoms and indicators
EMERGENCY_KEYWORDS = [
    r"\bchest pain\b",
    r"\bheart attack\b",
    r"\bsevere shortness of breath\b",
    r"\bcan't breathe\b",
    r"\bcannot breathe\b",
    r"\bsudden weakness\b",
    r"\bfacial drooping\b",
    r"\bslurred speech\b",
    r"\bstroke\b",
    r"\bsevere bleeding\b",
    r"\bhemorrhage\b",
    r"\bcoughed up blood\b",
    r"\bvomiting blood\b",
    r"\bloss of consciousness\b",
    r"\bpassed out\b",
    r"\bseizure\b",
    r"\bconvulsion\b",
    r"\banaphylaxis\b",
    r"\bthroat swelling\b",
    r"\bsuicide\b",
    r"\bself harm\b",
    r"\bunbearable head pain\b",
    r"\bworst headache of my life\b"
]

MODERATE_KEYWORDS = [
    r"\bfever\b",
    r"\bchills\b",
    r"\bpersistent cough\b",
    r"\bwheezing\b",
    r"\bvomi(t|ting)\b",
    r"\bdiarrhea\b",
    r"\bdehydration\b",
    r"\bmoderate pain\b",
    r"\brash with fever\b",
    r"\bdizziness\b",
    r"\bsprain\b",
    r"\bear infection\b",
    r"\burinary pain\b",
    r"\bblood in urine\b",
    r"\bunexplained weight loss\b"
]

def check_emergency(text: str) -> tuple[bool, str]:
    """
    Checks if text contains life-threatening or red-flag emergency symptoms.
    Returns (is_emergency, emergency_message)
    """
    if not text:
        return False, ""
    
    text_lower = text.lower()
    for pattern in EMERGENCY_KEYWORDS:
        if re.search(pattern, text_lower):
            return True, "🚨 EMERGENCY ALERT: Your message contains indicators of a potentially life-threatening medical situation. Please call 911 (or your local emergency services) immediately or proceed to the nearest emergency department without delay. Do not wait for an AI response."
    
    return False, ""

def evaluate_triage(symptoms: list[str] | str, duration: str = "", severity: str = "moderate") -> dict:
    """
    Classifies health risk into LOW, MODERATE, or URGENT with actionable guidance.
    """
    text_combined = f"{symptoms} {duration} {severity}".lower()
    
    # 1. Emergency / URGENT check
    is_emergency, emergency_msg = check_emergency(text_combined)
    if is_emergency or severity.lower() in ["severe", "critical", "urgent", "unbearable"]:
        return {
            "level": "URGENT",
            "badge_color": "danger",
            "title": "Immediate Medical Evaluation Required",
            "summary": "The symptoms reported include critical red-flag indicators that require urgent, professional in-person medical attention.",
            "action_required": "Seek emergency medical care immediately at your nearest emergency department or call your local emergency hotline (e.g. 911 / 112 / 999).",
            "warning": "Do not attempt home remedies or delay seeking emergency assistance.",
            "is_emergency": True
        }
    
    # 2. MODERATE check
    for pattern in MODERATE_KEYWORDS:
        if re.search(pattern, text_combined):
            return {
                "level": "MODERATE",
                "badge_color": "warning",
                "title": "Moderate Priority – Healthcare Consultation Recommended",
                "summary": "The symptoms described suggest an active health issue that warrants evaluation by a primary care doctor, urgent care clinic, or specialist within 24 to 48 hours.",
                "action_required": "Schedule an appointment with your healthcare provider. Keep a log of your symptoms, temperature, and medication response.",
                "warning": "If symptoms rapidly worsen, you develop high unremitting fever, severe pain, or difficulty breathing, escalate to emergency care.",
                "is_emergency": False
            }
            
    # 3. LOW check
    return {
        "level": "LOW",
        "badge_color": "success",
        "title": "Low Priority – Routine Self-Care & Monitoring",
        "summary": "The symptoms reported appear mild and consistent with self-limiting conditions that can generally be managed with basic supportive care and hydration.",
        "action_required": "Ensure plenty of rest, balanced hydration, and monitor your symptoms over the next 48-72 hours. Consult a pharmacist or general physician if symptoms persist.",
        "warning": "Seek professional medical review if symptoms do not improve after 3-5 days or if new concerning signs emerge.",
        "is_emergency": False
    }
