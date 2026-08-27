// =====================================================
// SYMPTOM CHECKER & HEALTH RISK TRIAGE
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const symptomForm = document.getElementById("symptomForm");
    const symptomInput = document.getElementById("symptomInput");
    const durationInput = document.getElementById("durationInput");
    const severityInput = document.getElementById("severityInput");
    const notesInput = document.getElementById("notesInput");
    const checkBtn = document.getElementById("checkSymptomsBtn");
    const resultsContainer = document.getElementById("symptomResults");
    const quickTags = document.querySelectorAll(".symptom-tag-btn");

    // Quick tag selector
    quickTags.forEach(btn => {
        btn.addEventListener("click", () => {
            const sym = btn.getAttribute("data-symptom");
            let current = symptomInput.value.trim();
            if (current) {
                if (!current.toLowerCase().includes(sym.toLowerCase())) {
                    symptomInput.value = `${current}, ${sym}`;
                }
            } else {
                symptomInput.value = sym;
            }
        });
    });

    if (symptomForm) {
        symptomForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const symptomsText = symptomInput.value.trim();
            if (!symptomsText) {
                CareConnectConfig.showToast("Please enter or select at least one symptom.", "error");
                return;
            }

            const symptomsList = symptomsText.split(",").map(s => s.trim()).filter(Boolean);
            const duration = durationInput ? durationInput.value.trim() : "";
            const notes = notesInput ? notesInput.value.trim() : "";

            checkBtn.disabled = true;
            checkBtn.innerHTML = `<span class="spinner"></span> Analyzing Symptoms...`;

            try {
                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/ai/symptoms`, {
                    method: "POST",
                    headers: CareConnectConfig.getAuthHeaders(),
                    body: JSON.stringify({
                        symptoms: symptomsList,
                        duration: duration,
                        notes: notes
                    })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    renderSymptomResults(data);
                } else {
                    CareConnectConfig.showToast(data.message || "Symptom check failed.", "error");
                }
            } catch (err) {
                console.error("Symptom check error:", err);
                CareConnectConfig.showToast("Error connecting to symptom analysis service.", "error");
            } finally {
                checkBtn.disabled = false;
                checkBtn.innerHTML = `<span>🔍</span> Analyze Symptoms`;
            }
        });
    }

    function renderSymptomResults(data) {
        if (!resultsContainer) return;
        resultsContainer.style.display = "block";

        const triage = data.triage || {};
        let badgeClass = "badge-primary";
        if (triage.level === "URGENT") badgeClass = "badge-danger";
        if (triage.level === "MODERATE") badgeClass = "badge-warning";
        if (triage.level === "LOW") badgeClass = "badge-success";

        let html = `
            <div class="card" style="border-top: 4px solid var(--${triage.level === 'URGENT' ? 'danger' : (triage.level === 'MODERATE' ? 'warning' : 'accent')}); margin-top: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
                    <h3>Symptom Evaluation Results</h3>
                    <span class="badge ${badgeClass}">${triage.level || 'TRIAGE'} PRIORITY</span>
                </div>

                ${triage.is_emergency ? `
                <div class="emergency-banner">
                    <span class="icon">🚨</span>
                    <div>
                        <h4>Urgent Medical Attention Required</h4>
                        <p>${triage.action_required}</p>
                    </div>
                </div>` : ''}

                <div class="result-section">
                    <h4><span>🩺</span> Possible Associated Categories & Patterns</h4>
                    <p style="margin-bottom: 8px; font-style: italic; color: var(--text-dim); font-size: 13px;">${data.wording_disclaimer || ''}</p>
                    <ul style="padding-left: 20px; color: var(--text-muted); font-size: 14px;">
                        ${(data.possible_associations || []).map(c => `<li style="margin-bottom: 4px;"><strong>${c}</strong></li>`).join('')}
                    </ul>
                </div>

                <div class="result-detail-grid" style="margin-top: 20px;">
                    <div class="result-section">
                        <h4><span>💡</span> General Self-Care Guidance</h4>
                        <ul style="padding-left: 20px; color: var(--text-muted); font-size: 14px;">
                            ${(data.general_self_care || []).map(s => `<li style="margin-bottom: 4px;">${s}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="result-section">
                        <h4><span>⚠️</span> Red-Flag Warning Signs</h4>
                        <ul style="padding-left: 20px; color: #FCA5A5; font-size: 13px;">
                            ${(data.warning_signs || []).map(w => `<li style="margin-bottom: 4px;">${w}</li>`).join('')}
                        </ul>
                    </div>
                </div>

                <div class="result-section" style="margin-top: 14px;">
                    <h4><span>👨‍⚕️</span> Clinical Recommendation</h4>
                    <p style="color: var(--text-main); font-weight: 500;">${data.recommendation || ''}</p>
                </div>

                <div class="disclaimer-banner" style="margin-top: 20px;">
                    <span class="icon">ℹ️</span>
                    <div><strong>Notice:</strong> ${data.disclaimer}</div>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = html;
        resultsContainer.scrollIntoView({ behavior: "smooth" });
    }
});
