import io
import json
import sys
from PIL import Image, ImageDraw
from app import create_app

# Set utf-8 stdout if possible
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def create_sample_test_image():
    """Generates an in-memory sample medical test image."""
    img = Image.new("RGB", (256, 256), color=(40, 45, 55))
    draw = ImageDraw.Draw(img)
    # Draw simulated anatomical structure / bone opacity
    draw.ellipse([60, 60, 196, 196], fill=(120, 130, 145), outline=(180, 190, 210), width=3)
    draw.line([128, 50, 128, 206], fill=(200, 210, 220), width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def run_all_tests():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    print("\n" + "="*70)
    print("CARECONNECT AUTOMATED END-TO-END VERIFICATION TEST SUITE")
    print("="*70)

    # TEST 1: /
    res = client.get("/")
    assert res.status_code == 200, f"Root check failed: {res.data}"
    print("[PASS] TEST 1: GET / -> Service status online")

    # TEST 2: /health
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.data}"
    print("[PASS] TEST 2: GET /health -> Service healthy")

    # TEST 3: /db-health
    res = client.get("/db-health")
    assert res.status_code == 200, f"DB Health check failed: {res.data}"
    print("[PASS] TEST 3: GET /db-health -> Database connection active")

    # TEST 4: User Registration
    test_email = "alex.mercer.md@careconnect.test"
    res = client.post("/api/register", json={
        "name": "Dr. Alex Mercer",
        "email": test_email,
        "password": "SecurePassword2026!"
    })
    if res.status_code == 409:
        print("[INFO] User already registered, proceeding to login...")
    else:
        assert res.status_code == 201, f"Registration failed: {res.data}"
        print("[PASS] TEST 4: POST /api/register -> User registered & JWT issued")

    # TEST 5: User Login
    res = client.post("/api/login", json={
        "email": test_email,
        "password": "SecurePassword2026!"
    })
    assert res.status_code == 200, f"Login failed: {res.data}"
    login_data = json.loads(res.data)
    token = login_data["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] TEST 5: POST /api/login -> User authenticated successfully")

    # TEST 6: Unauthorized Access Blocked
    res = client.get("/api/scans")
    assert res.status_code == 401, "Unauthorized access was not blocked!"
    print("[PASS] TEST 6: Unauthorized Route Guard -> Blocked with 401")

    # TEST 7: Profile Retrieval & Update
    res = client.get("/api/profile", headers=auth_headers)
    assert res.status_code == 200
    res = client.put("/api/profile", headers=auth_headers, json={
        "name": "Dr. Alex Mercer",
        "blood_group": "O+",
        "emergency_contact": "Sarah Mercer (Spouse)",
        "emergency_phone": "+1 555-019-2834"
    })
    assert res.status_code == 200
    print("[PASS] TEST 7: GET & PUT /api/profile -> Profile & emergency contact updated")

    # TEST 8: Medical Profile Endpoint
    res = client.post("/api/medical-profile", headers=auth_headers, json={
        "blood_group": "O+",
        "phone": "+1 555-019-2834",
        "allergies": "Penicillin, Latex",
        "medications": "Aspirin 81mg",
        "conditions": "Hypertension",
        "emergency_contact": "Sarah Mercer"
    })
    assert res.status_code == 200
    print("[PASS] TEST 8: POST /api/medical-profile -> Medical profile saved")

    # TEST 9: Medical QR Passport Generation & View
    res = client.get("/api/generate-qr", headers=auth_headers)
    assert res.status_code == 200
    qr_data = json.loads(res.data)
    assert "qr_code" in qr_data
    qr_token = qr_data["token"]
    res = client.get(f"/api/qr/view/{qr_token}")
    assert res.status_code == 200
    view_data = json.loads(res.data)
    assert view_data["medical_profile"]["blood_group"] == "O+"
    print(f"[PASS] TEST 9: GET /api/generate-qr & /api/qr/view -> QR token verified ({qr_token[:8]}...)")

    # TEST 10: Ambulance Emergency Request
    res = client.post("/api/ambulance/request", headers=auth_headers, json={
        "patient_name": "Dr. Alex Mercer",
        "contact_number": "+1 555-019-2834",
        "emergency_type": "Cardiac Emergency",
        "current_location": "742 Evergreen Terrace",
        "additional_details": "Chest discomfort reported"
    })
    assert res.status_code == 201
    amb_data = json.loads(res.data)
    assert amb_data["status"] == "REQUESTED"
    print(f"[PASS] TEST 10: POST /api/ambulance/request -> Ambulance request created (ID: {amb_data['request_id']})")

    # TEST 11: Emergency SOS & History
    res = client.post("/api/sos", headers=auth_headers, json={
        "latitude": 37.7749,
        "longitude": -122.4194,
        "message": "Emergency SOS broadcast"
    })
    assert res.status_code == 201
    res = client.get("/api/sos/history", headers=auth_headers)
    assert res.status_code == 200
    assert len(json.loads(res.data)["events"]) > 0
    print("[PASS] TEST 11: POST /api/sos & GET /api/sos/history -> SOS logged and retrieved")

    # TEST 12: Medical Image Scanning
    img_buf = create_sample_test_image()
    res = client.post(
        "/api/scan",
        headers=auth_headers,
        data={
            "image": (img_buf, "chest_xray_test.png"),
            "scan_type": "Chest X-Ray"
        },
        content_type="multipart/form-data"
    )
    assert res.status_code == 201, f"Scan failed: {res.data}"
    scan_data = json.loads(res.data)
    scan_id = scan_data["scan_id"]
    assert "result" in scan_data["scan"]
    assert "confidence" in scan_data["scan"]
    assert "disclaimer" in scan_data["scan"]
    print(f"[PASS] TEST 12: POST /api/scan -> Result: '{scan_data['scan']['result']}' ({scan_data['scan']['confidence']}%)")

    # TEST 13: Scan History & Single Scan Fetch
    res = client.get("/api/scans", headers=auth_headers)
    assert res.status_code == 200
    history_data = json.loads(res.data)
    assert history_data["count"] > 0
    res = client.get(f"/api/scans/{scan_id}", headers=auth_headers)
    assert res.status_code == 200
    print(f"[PASS] TEST 13: GET /api/scans & /api/scans/{scan_id} -> Retrieved {history_data['count']} scans")

    # TEST 14: AI Health Chat Assistant
    res = client.post("/api/ai/chat", headers=auth_headers, json={
        "message": "What does a high fever usually indicate and how can I stay hydrated?"
    })
    assert res.status_code == 200
    chat_data = json.loads(res.data)
    assert chat_data["success"] is True
    assert len(chat_data["response"]) > 20
    conv_id = chat_data["conversation_id"]
    print("[PASS] TEST 14: POST /api/ai/chat -> Health educational answer rendered")

    # TEST 15: AI Emergency Detection
    res = client.post("/api/ai/chat", headers=auth_headers, json={
        "message": "I have severe crushing chest pain radiating to left arm and cannot breathe!",
        "conversation_id": conv_id
    })
    assert res.status_code == 200
    emerg_data = json.loads(res.data)
    assert emerg_data["is_emergency"] is True
    assert emerg_data["triage_level"] == "URGENT"
    print("[PASS] TEST 15: AI Emergency Detection -> Immediate URGENT emergency alert triggered")

    # TEST 16: Symptom Checker
    res = client.post("/api/ai/symptoms", headers=auth_headers, json={
        "symptoms": ["fever", "cough", "fatigue"],
        "duration": "3 days",
        "notes": "Mild body aches"
    })
    assert res.status_code == 200
    symptom_data = json.loads(res.data)
    assert symptom_data["success"] is True
    assert len(symptom_data["possible_associations"]) > 0
    assert "disclaimer" in symptom_data
    print("[PASS] TEST 16: POST /api/ai/symptoms -> Symptom patterns & self-care evaluated")

    # TEST 17: Health Risk Triage
    res = client.post("/api/ai/triage", headers=auth_headers, json={
        "symptoms": "Mild headache after working on computer",
        "duration": "2 hours",
        "severity": "mild"
    })
    assert res.status_code == 200
    triage_data = json.loads(res.data)
    assert triage_data["triage"]["level"] == "LOW"
    print("[PASS] TEST 17: POST /api/ai/triage -> LOW risk triage classified")

    # TEST 18: Medical Report Explainer
    res = client.post("/api/ai/explain-report", headers=auth_headers, json={
        "report_text": "CBC: WBC 11.2 x10^3/uL (Elevated), Hemoglobin 13.8 g/dL, Platelets 260, Glucose 98 mg/dL.",
        "report_type": "Complete Blood Count (CBC)"
    })
    assert res.status_code == 200
    report_expl_data = json.loads(res.data)
    assert report_expl_data["success"] is True
    assert len(report_expl_data["important_terms"]) > 0
    print("[PASS] TEST 18: POST /api/ai/explain-report -> Lab report terms & questions generated")

    # TEST 19: Health Records CRUD
    res = client.post("/api/health-records", headers=auth_headers, json={
        "category": "Allergy",
        "title": "Penicillin",
        "details": "Causes skin rash and hives",
        "severity": "Severe",
        "start_date": "2020-04-15"
    })
    assert res.status_code == 201
    rec_data = json.loads(res.data)
    rec_id = rec_data["record"]["id"]

    res = client.get("/api/health-records", headers=auth_headers)
    assert res.status_code == 200
    records_list = json.loads(res.data)["records"]
    assert len(records_list) > 0
    print(f"[PASS] TEST 19: Health Records CRUD -> Saved and retrieved record ID: {rec_id}")

    # TEST 20: AI Health Summary
    res = client.post("/api/ai/health-summary", headers=auth_headers)
    assert res.status_code == 200
    summary_data = json.loads(res.data)
    assert summary_data["success"] is True
    assert summary_data["total_scans"] >= 1
    assert summary_data["total_records"] >= 1
    print("[PASS] TEST 20: POST /api/ai/health-summary -> Synthesized patient health summary")

    # TEST 21: Downloadable Scan Report Generation
    res = client.post("/api/reports/generate", headers=auth_headers, json={
        "scan_id": scan_id
    })
    assert res.status_code == 201
    rep_gen_data = json.loads(res.data)
    assert "download_url" in rep_gen_data
    print(f"[PASS] TEST 21: POST /api/reports/generate -> Report document created: {rep_gen_data['download_url']}")

    # TEST 22: Reports List
    res = client.get("/api/reports", headers=auth_headers)
    assert res.status_code == 200
    print("[PASS] TEST 22: GET /api/reports -> Reports listed successfully")

    # TEST 23: Scan Record Deletion
    res = client.delete(f"/api/scans/{scan_id}", headers=auth_headers)
    assert res.status_code == 200
    print("[PASS] TEST 23: DELETE /api/scans/<id> -> Deleted scan record cleanly")

    # TEST 24: User Logout
    res = client.post("/api/logout", headers=auth_headers)
    assert res.status_code == 200
    print("[PASS] TEST 24: POST /api/logout -> User logged out")

    print("="*70)
    print("ALL 24 END-TO-END AUTOMATED TESTS PASSED WITH ZERO ERRORS!")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_all_tests()
