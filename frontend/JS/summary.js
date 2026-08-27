// =====================================================
// AI HEALTH SUMMARY GENERATION & DISPLAY
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const patientNameEl = document.getElementById("summaryPatientName");
    const bloodGroupEl = document.getElementById("summaryBloodGroup");
    const emergencyContactEl = document.getElementById("summaryEmergencyContact");
    const scansCountEl = document.getElementById("summaryScansCount");
    const recordsCountEl = document.getElementById("summaryRecordsCount");
    const summaryTextEl = document.getElementById("summaryOverviewText");
    const allergiesListEl = document.getElementById("summaryAllergiesList");
    const conditionsListEl = document.getElementById("summaryConditionsList");
    const medicationsListEl = document.getElementById("summaryMedicationsList");
    const guidanceListEl = document.getElementById("summaryGuidanceList");
    const refreshBtn = document.getElementById("refreshSummaryBtn");

    async function loadHealthSummary() {
        if (summaryTextEl) summaryTextEl.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; margin-right: 8px;"></span> Synthesizing your personal health summary...`;

        try {
            const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/ai/health-summary`, {
                headers: CareConnectConfig.getAuthHeaders()
            });

            const data = await res.json();
            if (res.ok && data.success) {
                if (patientNameEl) patientNameEl.textContent = data.patient_name;
                if (bloodGroupEl) bloodGroupEl.textContent = data.blood_group;
                if (emergencyContactEl) emergencyContactEl.textContent = data.emergency_contact;
                if (scansCountEl) scansCountEl.textContent = data.total_scans;
                if (recordsCountEl) recordsCountEl.textContent = data.total_records;
                if (summaryTextEl) summaryTextEl.textContent = data.summary_text;

                // Allergies
                if (allergiesListEl) {
                    allergiesListEl.innerHTML = data.allergies && data.allergies.length > 0
                        ? data.allergies.map(a => `<span class="badge badge-danger" style="margin-right: 6px; margin-bottom: 6px;">${a}</span>`).join('')
                        : '<span style="color: var(--text-dim); font-size: 13px;">None recorded</span>';
                }

                // Conditions
                if (conditionsListEl) {
                    conditionsListEl.innerHTML = data.conditions && data.conditions.length > 0
                        ? data.conditions.map(c => `<span class="badge badge-warning" style="margin-right: 6px; margin-bottom: 6px;">${c}</span>`).join('')
                        : '<span style="color: var(--text-dim); font-size: 13px;">None recorded</span>';
                }

                // Medications
                if (medicationsListEl) {
                    medicationsListEl.innerHTML = data.medications && data.medications.length > 0
                        ? data.medications.map(m => `<span class="badge badge-success" style="margin-right: 6px; margin-bottom: 6px;">${m}</span>`).join('')
                        : '<span style="color: var(--text-dim); font-size: 13px;">None recorded</span>';
                }

                // Guidance
                if (guidanceListEl && data.guidance) {
                    guidanceListEl.innerHTML = data.guidance.map(g => `<li style="margin-bottom: 6px;">${g}</li>`).join('');
                }
            } else {
                CareConnectConfig.showToast(data.message || "Failed to load summary.", "error");
            }
        } catch (err) {
            console.error("Summary error:", err);
            CareConnectConfig.showToast("Error loading health summary.", "error");
        }
    }

    if (refreshBtn) refreshBtn.addEventListener("click", loadHealthSummary);
    loadHealthSummary();
});
