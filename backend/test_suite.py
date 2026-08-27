import io
import json
import sys
from PIL import Image, ImageDraw
from app import create_app

# Set utf-8 stdout if possible
if sys.stdout.encoding != "utf-8":
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

    # TEST 1: /health
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.data}"
    print("[PASS] TEST 1: GET /health -> Service healthy")

    # TEST 2: /db-health
    res = client.get("/db-health")
    assert res.status_code == 200, f"DB Health check failed: {res.data}"
    print("[PASS] TEST 2: GET /db-health -> Database connection active")

    # TEST 3: User Registration
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
        print("[PASS] TEST 3: POST /api/register -> User registered & JWT issued")

    # TEST 4: User Login
    res = client.post("/api/login", json={
        "email": test_email,
        "password": "SecurePassword2026!"
    })
    assert res.status_code == 200, f"Login failed: {res.data}"
    login_data = json.loads(res.data)
    token = login_data["token"]
    user_id = login_data["user"]["id"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] TEST 4: POST /api/login -> User authenticated successfully")

    # TEST 5: Unauthorized Access Blocked
    res = client.get("/api/scans")
    assert res.status_code == 401, "Unauthorized access was not blocked!"
    print("[PASS] TEST 5: Unauthorized Route Guard -> Blocked with 401")

    # TEST 6: Profile Retrieval & Update
    res = client.get("/api/profile", headers=auth_headers)
    assert res.status_code == 200
    res = client.put("/api/profile", headers=auth_headers, json={
        "name": "Dr. Alex Mercer",
        "blood_group": "O+",
        "emergency_contact": "Sarah Mercer (Spouse)",
        "emergency_phone": "+1 555-019-2834"
    })
    assert res.status_code == 200
    print("[PASS] TEST 6: GET & PUT /api/profile -> Profile & emergency contact updated")

    # TEST 7: Medical Image Scanning
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
    print(f"[PASS] TEST 7: POST /api/scan -> Result: '{scan_data['scan']['result']}' ({scan_data['scan']['confidence']}%)")

    # TEST 8: Scan History & Single Scan Fetch
    res = client.get("/api/scans", headers=auth_headers)
    assert res.status_code == 200
    history_data = json.loads(res.data)
    assert history_data["count"] > 0
    res = client.get(f"/api/scans/{scan_id}", headers=auth_headers)
    assert res.status_code == 200
    print(f"[PASS] TEST 8: GET /api/scans & /api/scans/{scan_id} -> Retrieved {history_data['count']} scans")

    # TEST 9: AI Health Chat Assistant
    res = client.post("/api/ai/chat", headers=auth_headers, json={
        "message": "What does a high fever usually indicate and how can I stay hydrated?"
    })
    assert res.status_code == 200
    chat_data = json.loads(res.data)
    assert chat_data["success"] is True
    assert len(chat_data["response"]) > 20
    conv_id = chat_data["conversation_id"]
    print("[PASS] TEST 9: POST /api/ai/chat -> Health educational answer rendered")

    # TEST 10: AI Emergency Detection
    res = client.post("/api/ai/chat", headers=auth_headers, json={
        "message": "I have severe crushing chest pain radiating to left arm and cannot breathe!",
        "conversation_id": conv_id
    })
    assert res.status_code == 200
    emerg_data = json.loads(res.data)
    assert emerg_data["is_emergency"] is True
    assert emerg_data["triage_level"] == "URGENT"
    print("[PASS] TEST 10: AI Emergency Detection -> Immediate URGENT emergency alert triggered")

    # TEST 11: Symptom Checker
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
    print("[PASS] TEST 11: POST /api/ai/symptoms -> Symptom patterns & self-care evaluated")

    # TEST 12: Health Risk Triage
    res = client.post("/api/ai/triage", headers=auth_headers, json={
        "symptoms": "Mild headache after working on computer",
        "duration": "2 hours",
        "severity": "mild"
    })
    assert res.status_code == 200
    triage_data = json.loads(res.data)
    assert triage_data["triage"]["level"] == "LOW"
    print("[PASS] TEST 12: POST /api/ai/triage -> LOW risk triage classified")

    # TEST 13: Medical Report Explainer
    res = client.post("/api/ai/explain-report", headers=auth_headers, json={
        "report_text": "CBC: WBC 11.2 x10^3/uL (Elevated), Hemoglobin 13.8 g/dL, Platelets 260, Glucose 98 mg/dL.",
        "report_type": "Complete Blood Count (CBC)"
    })
    assert res.status_code == 200
    report_expl_data = json.loads(res.data)
    assert report_expl_data["success"] is True
    assert len(report_expl_data["important_terms"]) > 0
    print("[PASS] TEST 13: POST /api/ai/explain-report -> Lab report terms & questions generated")

    # TEST 14: Health Records CRUD
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
    print(f"[PASS] TEST 14: Health Records CRUD -> Saved and retrieved record ID: {rec_id}")

    # TEST 15: AI Health Summary
    res = client.post("/api/ai/health-summary", headers=auth_headers)
    assert res.status_code == 200
    summary_data = json.loads(res.data)
    assert summary_data["success"] is True
    assert summary_data["total_scans"] >= 1
    assert summary_data["total_records"] >= 1
    print("[PASS] TEST 15: POST /api/ai/health-summary -> Synthesized patient health summary")

    # TEST 16: Downloadable Scan Report Generation
    res = client.post("/api/reports/generate", headers=auth_headers, json={
        "scan_id": scan_id
    })
    assert res.status_code == 201
    rep_gen_data = json.loads(res.data)
    assert "download_url" in rep_gen_data
    print(f"[PASS] TEST 16: POST /api/reports/generate -> Report document created: {rep_gen_data['download_url']}")

    # TEST 17: Reports List
    res = client.get("/api/reports", headers=auth_headers)
    assert res.status_code == 200
    print("[PASS] TEST 17: GET /api/reports -> Reports listed successfully")

    # TEST 18: Scan Record Deletion
    res = client.delete(f"/api/scans/{scan_id}", headers=auth_headers)
    assert res.status_code == 200
    print("[PASS] TEST 18: DELETE /api/scans/<id> -> Deleted scan record cleanly")

    # TEST 19: User Logout
    res = client.post("/api/logout", headers=auth_headers)
    assert res.status_code == 200
    print("[PASS] TEST 19: POST /api/logout -> User logged out")

    print("="*70)
    print("ALL 19 END-TO-END AUTOMATED TESTS PASSED WITH ZERO ERRORS!")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_all_tests()
