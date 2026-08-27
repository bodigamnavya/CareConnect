# 🚑 CareConnect – Complete AI-Powered Healthcare Platform

CareConnect is a production-ready, AI-powered healthcare assistance platform providing medical image scanning, multi-turn clinical dialogue, symptom checking with risk triage, medical report translation, health records management, AI health summaries, and downloadable medical scan reports.

---

## 🌟 Key Features

1. **Medical Image Scanner (`/scan.html`)**
   - Upload or capture medical images via device camera.
   - Supports Chest X-Ray, Skin Lesions / Dermatology, Retinal / Fundus examination, and General Scans.
   - Structured visual feature explanation, confidence scoring, clinical indications, recommendations, and emergency warning signs.
2. **AI Health Assistant (`/ai-assistant.html`)**
   - Multi-turn interactive healthcare dialogue with database conversation context.
   - Red-flag emergency symptom detection with immediate triage warnings.
   - General medication, wellness, and physiology educational assistance.
3. **Symptom Checker & Health Risk Triage (`/symptom-checker.html`)**
   - Evaluates multi-symptom inputs, durations, and severity levels.
   - Categorizes risk priority into `LOW`, `MODERATE`, or `URGENT`.
   - Actionable self-care recommendations, warning signs, and doctor advice.
4. **Medical Report Explainer (`/report-explainer.html`)**
   - Analyzes uploaded medical documents (PDF/TXT/Images) or pasted lab text.
   - Explains complex clinical terms and reference ranges in plain language.
   - Formulates tailored questions for patients to ask their healthcare provider.
5. **Personal Health Vault (`/health-records.html`)**
   - Encrypted storage for allergies, chronic conditions, active medications, and surgical histories.
   - Category filtering and CRUD operations.
6. **Holistic AI Health Summary (`/health-summary.html`)**
   - Synthesizes user's authenticated scans, records, and clinical trends into one personalized overview.
7. **Downloadable Clinical Reports (`/scan-result.html`)**
   - On-demand generation of formatted, printable patient scan reports.
8. **Personal Health Dashboard (`/dashboard.html`)**
   - Real-time scan metrics, recent activity feed, quick actions, and profile status.

---

## 🏗️ Project Structure

```
CareConnect/
├── database/
│   └── careconnect.sql               # PostgreSQL Production Schema
├── backend/
│   ├── app.py                        # Central Flask app factory & blueprints
│   ├── config.py                     # Configuration layer
│   ├── requirements.txt              # Production dependencies
│   ├── test_suite.py                 # Automated end-to-end test suite
│   ├── .env.example                  # Environment template
│   ├── .env                          # Local environment settings
│   ├── models/
│   │   ├── user.py
│   │   ├── scan.py
│   │   ├── report.py
│   │   ├── health_record.py
│   │   └── conversation.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── scan.py
│   │   ├── ai.py
│   │   ├── history.py
│   │   ├── health_records.py
│   │   ├── reports.py
│   │   └── profile.py
│   ├── services/
│   │   ├── ai_model.py
│   │   ├── ai_chat.py
│   │   ├── scanner.py
│   │   ├── symptom_analyzer.py
│   │   ├── report_explainer.py
│   │   ├── triage.py
│   │   ├── health_summary.py
│   │   └── report_generator.py
│   ├── utils/
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── validators.py
│   │   └── file_security.py
│   └── uploads/                      # Secure file storage
├── frontend/
│   ├── index.html                    # Landing page
│   ├── login.html                    # Login page
│   ├── register.html                 # Registration page
│   ├── dashboard.html                # Main health dashboard
│   ├── scan.html                     # Medical image scanner
│   ├── scan-result.html              # AI Scan result presentation
│   ├── history.html                  # Scan history & filtering
│   ├── ai-assistant.html             # AI Health Chat Assistant
│   ├── symptom-checker.html          # Symptom checker & triage
│   ├── report-explainer.html         # Lab report explainer
│   ├── health-records.html           # Personal medical records
│   ├── health-summary.html           # AI Health summary
│   ├── profile.html                  # Profile & emergency contacts
│   ├── CSS/                          # Modular design system CSS
│   └── JS/                           # Modular frontend JS scripts
└── README.md
```

---

## 🗄️ Database Tables (`careconnect.sql`)

- `users` (id, name, email, password_hash, phone, blood_group, emergency_contact, emergency_phone, timestamps)
- `scans` (id, user_id, scan_type, image_path, image_url, result, confidence, explanation, possible_meaning, recommendation, warning_signs, disclaimer, status, created_at)
- `reports` (id, user_id, scan_id, report_type, title, file_path, content_json, summary_text, created_at)
- `health_records` (id, user_id, category, title, details, severity, start_date, is_active, timestamps)
- `conversations` (id, user_id, title, timestamps)
- `conversation_messages` (id, conversation_id, sender, message, triage_level, created_at)

---

## 🚀 API Endpoints

### Authentication & Profile
- `POST /api/register` – Register new user and receive JWT
- `POST /api/login` – Login user and receive JWT
- `POST /api/logout` – Logout
- `GET /api/profile` – Fetch current user profile (Protected)
- `PUT /api/profile` – Update profile & emergency contacts (Protected)

### Medical Scanning & History
- `POST /api/scan` – Upload medical image and perform AI analysis (Protected)
- `GET /api/scans` – List user scans with search & filter (Protected)
- `GET /api/scans/<id>` – Retrieve single scan details (Protected)
- `DELETE /api/scans/<id>` – Delete a scan record (Protected)

### AI Clinical Assistance
- `POST /api/ai/chat` – Conversational AI assistant with memory & emergency detection (Protected)
- `POST /api/ai/symptoms` – Symptom analysis & self-care recommendations (Protected)
- `POST /api/ai/triage` – Risk triage evaluation (LOW, MODERATE, URGENT) (Protected)
- `POST /api/ai/explain-report` – Medical report and lab value explainer (Protected)
- `POST /api/ai/health-summary` – Grounded patient health summary (Protected)

### Health Records & Reports
- `GET /api/health-records` – List health records by category (Protected)
- `POST /api/health-records` – Create health record (Protected)
- `PUT /api/health-records/<id>` – Update health record (Protected)
- `DELETE /api/health-records/<id>` – Delete health record (Protected)
- `POST /api/reports/generate` – Generate downloadable HTML/PDF report (Protected)
- `GET /api/reports` – List generated reports (Protected)

### System Health
- `GET /health` – Service status (`{"status": "ok", "service": "CareConnect"}`)
- `GET /db-health` – Database connectivity check

---

## ⚙️ Environment Variables (`.env`)

```ini
SECRET_KEY=CareConnect_Super_Secret_Production_Key_2026
JWT_SECRET=CareConnect_Secure_JWT_2026_Production_Key_987654
JWT_EXPIRATION_HOURS=48

# Database URL: Leave empty for SQLite local storage, or provide PostgreSQL URL for Render/Supabase
DATABASE_URL=postgresql://user:password@host:5432/careconnect

# External AI Provider (Optional: Google Gemini or OpenAI API Key)
# If left empty, CareConnect uses its built-in clinical vision & diagnostic heuristics engine
AI_API_KEY=
AI_MODEL=gemini-1.5-flash

# CORS Allowed Origin
FRONTEND_URL=*
PORT=5000
```

---

## 🏃 Local Run Commands

1. **Activate Virtual Environment & Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run Backend Server:**
   ```bash
   python app.py
   ```
   The backend will start at `http://127.0.0.1:5000`.

3. **Run Automated Test Suite:**
   ```bash
   python test_suite.py
   ```

4. **Open Frontend:**
   Open `frontend/index.html` in your browser or run any static server (e.g., Live Server or serve directly via Flask at `http://127.0.0.1:5000/`).

---

## 🌐 Production Deployment

- **Backend (Render):**
  - Build Command: `pip install -r backend/requirements.txt`
  - Start Command: `gunicorn --chdir backend app:app -b 0.0.0.0:$PORT`
  - Environment Variables: Add `DATABASE_URL` (PostgreSQL), `JWT_SECRET`, `AI_API_KEY` (optional).
- **Frontend (Vercel / Netlify):**
  - Set root directory to `frontend`.
  - In `frontend/JS/config.js`, `getApiBaseUrl()` automatically resolves to your deployed backend origin.

---

## ⚖️ Medical Disclaimer
*All AI-generated healthcare information and image scan findings are provided for preliminary educational and informational assistance only. CareConnect is not a medical device and does not provide formal medical diagnoses. Users must always seek the advice of a qualified healthcare professional regarding any medical condition.*
