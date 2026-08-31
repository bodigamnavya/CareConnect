import os
import uuid
from datetime import datetime, timezone
import requests
from config import Config
from services.triage import check_emergency, evaluate_triage
from utils.database import (
    get_conversations_collection,
    get_conversation_messages_collection
)

# Medical Knowledge System Prompt for AI Chat
SYSTEM_PROMPT = """
You are CareConnect AI, an intelligent, empathetic, and professional healthcare educational assistant.
Your goal is to provide concise, accurate, evidence-informed healthcare education, general guidance, and reassurance.

CRITICAL CLINICAL RULES:
1. Always state clearly that your output is educational assistance, NEVER a definitive medical diagnosis.
2. If the user mentions emergency red flags (e.g., crushing chest pain, severe shortness of breath, sudden facial drooping or weakness, uncontrolled bleeding), immediately prioritize advising them to contact emergency services (911/112).
3. If the user asks about medications or prescriptions, provide general usage, typical side effects, precautions, and questions to ask a doctor/pharmacist. NEVER alter dosage or recommend stopping prescribed drugs.
4. Keep responses structured, concise, easy to read, and polite.
5. Always remind the user to consult their healthcare provider.
"""

def generate_chat_response_external_api(messages: list[dict], api_key: str) -> str:
    """Generate response via external LLM API (Google Gemini)."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{Config.AI_MODEL}:generateContent?key={api_key}"
        
        gemini_contents = []
        for msg in messages:
            role = "user" if msg.get("sender") == "user" else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg.get("message", "")}]
            })
            
        payload = {
            "contents": gemini_contents,
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 800
            }
        }
        
        resp = requests.post(url, json=payload, timeout=25)
        if resp.ok:
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[AI Chat] External API Error: {e}. Falling back to internal engine.")
    return ""

def generate_chat_response_internal(user_message: str, history: list[dict]) -> str:
    """Built-in clinical intelligence dialogue engine."""
    msg = user_message.lower()
    
    # 1. Emergency Check
    is_emergency, emergency_msg = check_emergency(msg)
    if is_emergency:
        return emergency_msg

    # 2. Medication / Prescription Inquiry
    if any(k in msg for k in ["medicine", "prescription", "dosage", "pill", "tablet", "antibiotic", "side effect", "paracetamol", "ibuprofen", "aspirin", "amoxicillin"]):
        return (
            "Here is general educational information regarding medications and prescriptions:\n\n"
            "• **Purpose & Usage:** Medicines are prescribed by clinicians to manage symptoms, treat infections, or regulate physiological functions according to strict individualized dosing.\n"
            "• **Safety & Adherence:** Always take prescribed medicines exactly as directed by your prescribing doctor or pharmacist. Never adjust your dosage or discontinue a regimen without consulting them.\n"
            "• **Common Side Effects:** Many medications can occasionally cause mild nausea, drowsiness, or digestive changes. If you experience severe rashes, swelling, or dizziness, notify your clinician immediately.\n"
            "• **Questions to ask your Pharmacist:** 'Are there food interactions with this medication?' 'What should I do if I miss a dose?'\n\n"
            "⚠️ *Reminder: CareConnect provides educational information and does not prescribe or alter medications. Always adhere to your doctor's instructions.*"
        )
    
    # 3. Fever & Infection
    if "fever" in msg or "temperature" in msg:
        return (
            "A fever is a natural physiological response where the body's immune system raises internal temperature to help fight off viral or bacterial infections.\n\n"
            "**General Self-Care Steps:**\n"
            "• Stay well-hydrated with water, warm broths, or electrolyte solutions.\n"
            "• Get ample rest to conserve metabolic energy for recovery.\n"
            "• Wear lightweight, breathable clothing.\n\n"
            "**When to see a Doctor:**\n"
            "• If the fever exceeds 103°F (39.4°C) or lasts longer than 3 continuous days.\n"
            "• If accompanied by a stiff neck, unusual rash, confusion, or difficulty breathing."
        )
        
    # 4. Blood Pressure / Hypertension
    if "blood pressure" in msg or "hypertension" in msg:
        return (
            "Blood pressure measures the hydrostatic force of blood pushing against artery walls during heart contractions.\n\n"
            "**Key Guidelines:**\n"
            "• **Normal Baseline:** Typically under 120/80 mmHg in healthy adults at rest.\n"
            "• **Lifestyle Support:** A balanced diet rich in leafy greens, low in excess sodium, combined with 30 minutes of regular moderate exercise promotes cardiovascular elasticity.\n"
            "• **When to Seek Care:** If systolic pressure exceeds 180 mmHg or diastolic exceeds 120 mmHg, especially with chest pain or headache, seek immediate medical attention."
        )
        
    # 5. Diet & Nutrition
    if any(k in msg for k in ["diet", "food", "nutrition", "vitamins"]):
        return (
            "Balanced nutrition plays an essential role in immune defense, cellular repair, and steady daily energy levels.\n\n"
            "**Core Principles:**\n"
            "• Prioritize whole foods: vegetables, fruits, lean proteins, whole grains, and healthy fats (such as olive oil and nuts).\n"
            "• Aim for 2 to 3 liters of water daily to maintain cellular hydration.\n"
            "• Minimize ultra-processed foods, refined sugars, and excessive sodium."
        )
        
    # Default educational response
    return (
        f"Thank you for sharing your healthcare inquiry. Regarding your question on '{user_message}':\n\n"
        "1. **Understanding the Topic:** Health symptoms and biological responses often reflect the body's natural adaptation to stress, lifestyle habits, or environmental triggers.\n"
        "2. **Helpful Next Steps:** Monitoring your daily symptoms, maintaining proper hydration, getting 7-9 hours of restful sleep, and eating nutritious foods support overall physiological balance.\n"
        "3. **Clinical Recommendation:** We encourage discussing specific symptoms or prolonged concerns directly with a qualified doctor for personalized diagnostic testing.\n\n"
        "Is there a specific symptom or timeline you would like more educational details on?"
    )

def handle_chat_message(user_id: str, message_text: str, conversation_id: str = "") -> dict:
    """
    Handles user chat message, maintains MongoDB thread context,
    checks emergency triage, and returns structured AI response.
    """
    clean_message = str(message_text).strip()
    if not clean_message:
        return {"success": False, "message": "Message cannot be empty."}

    now_utc = datetime.now(timezone.utc)
    conv_col = get_conversations_collection()
    msg_col = get_conversation_messages_collection()

    # 1. Create or retrieve conversation
    if not conversation_id:
        conversation_id = f"conv_{uuid.uuid4().hex[:16]}"
        if conv_col is not None:
            try:
                conv_col.insert_one({
                    "_id": conversation_id,
                    "id": conversation_id,
                    "user_id": user_id,
                    "title": clean_message[:40],
                    "created_at": now_utc,
                    "updated_at": now_utc
                })
            except Exception as e:
                print(f"[AI Chat conv insert note]: {e}")
    else:
        # Verify conversation belongs to user
        if conv_col is not None:
            try:
                conv = conv_col.find_one({"$or": [{"_id": conversation_id}, {"id": conversation_id}], "user_id": user_id})
                if not conv:
                    conversation_id = f"conv_{uuid.uuid4().hex[:16]}"
                    conv_col.insert_one({
                        "_id": conversation_id,
                        "id": conversation_id,
                        "user_id": user_id,
                        "title": clean_message[:40],
                        "created_at": now_utc,
                        "updated_at": now_utc
                    })
                else:
                    conv_col.update_one(
                        {"$or": [{"_id": conversation_id}, {"id": conversation_id}]},
                        {"$set": {"updated_at": now_utc}}
                    )
            except Exception:
                pass

    # 2. Check Emergency Safety
    is_emergency, emergency_text = check_emergency(clean_message)
    triage_level = "URGENT" if is_emergency else "LOW"

    # Save user message in MongoDB
    user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    if msg_col is not None:
        try:
            msg_col.insert_one({
                "_id": user_msg_id,
                "id": user_msg_id,
                "conversation_id": conversation_id,
                "sender": "user",
                "message": clean_message,
                "triage_level": triage_level,
                "created_at": now_utc
            })
        except Exception as e:
            print(f"[AI Chat user message insert note]: {e}")

    # 3. Retrieve conversation history for context (last 6 messages)
    history_rows = []
    if msg_col is not None:
        try:
            history_docs = list(msg_col.find({"conversation_id": conversation_id}).sort("created_at", 1).limit(6))
            for h in history_docs:
                history_rows.append({
                    "sender": h.get("sender", "user"),
                    "message": h.get("message", "")
                })
        except Exception:
            history_rows = [{"sender": "user", "message": clean_message}]
    else:
        history_rows = [{"sender": "user", "message": clean_message}]

    # 4. Generate AI response
    if is_emergency:
        ai_response_text = emergency_text
    else:
        ai_response_text = ""
        if Config.AI_API_KEY:
            ai_response_text = generate_chat_response_external_api(history_rows, Config.AI_API_KEY)
        if not ai_response_text:
            ai_response_text = generate_chat_response_internal(clean_message, history_rows)

    # 5. Save assistant response in MongoDB
    ai_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    if msg_col is not None:
        try:
            msg_col.insert_one({
                "_id": ai_msg_id,
                "id": ai_msg_id,
                "conversation_id": conversation_id,
                "sender": "assistant",
                "message": ai_response_text,
                "triage_level": triage_level,
                "created_at": datetime.now(timezone.utc)
            })
        except Exception as e:
            print(f"[AI Chat assistant message insert note]: {e}")

    return {
        "success": True,
        "response": ai_response_text,
        "conversation_id": conversation_id,
        "is_emergency": is_emergency,
        "triage_level": triage_level,
        "disclaimer": Config.MEDICAL_DISCLAIMER
    }
