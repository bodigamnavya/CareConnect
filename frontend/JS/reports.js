// =====================================================
// MEDICAL REPORT EXPLAINER LOGIC
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const reportForm = document.getElementById("reportForm");
    const reportFileInput = document.getElementById("reportFileInput");
    const reportTextInput = document.getElementById("reportTextInput");
    const reportTypeSelect = document.getElementById("reportTypeSelect");
    const explainBtn = document.getElementById("explainReportBtn");
    const explanationContainer = document.getElementById("reportExplanationResult");

    if (reportForm) {
        reportForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const text = reportTextInput ? reportTextInput.value.trim() : "";
            const file = reportFileInput && reportFileInput.files ? reportFileInput.files[0] : null;
            const reportType = reportTypeSelect ? reportTypeSelect.value : "Lab Report";

            if (!text && !file) {
                CareConnectConfig.showToast("Please paste report text or upload a medical document file.", "error");
                return;
            }

            explainBtn.disabled = true;
            explainBtn.innerHTML = `<span class="spinner"></span> Analyzing Report...`;

            try {
                let res;
                if (file) {
                    const formData = new FormData();
                    formData.append("report_file", file);
                    formData.append("report_text", text);
                    formData.append("report_type", reportType);

                    res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/ai/explain-report`, {
                        method: "POST",
                        headers: CareConnectConfig.getAuthHeaders(false),
                        body: formData
                    });
                } else {
                    res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/ai/explain-report`, {
                        method: "POST",
                        headers: CareConnectConfig.getAuthHeaders(true),
                        body: JSON.stringify({
                            report_text: text,
                            report_type: reportType
                        })
                    });
                }

                const data = await res.json();
                if (res.ok && data.success) {
                    renderExplanation(data);
                } else {
                    CareConnectConfig.showToast(data.message || "Report analysis failed.", "error");
                }
            } catch (err) {
                console.error("Report explain error:", err);
                CareConnectConfig.showToast("Error communicating with report analyzer.", "error");
            } finally {
                explainBtn.disabled = false;
                explainBtn.innerHTML = `<span>🧠</span> Explain Medical Report`;
            }
        });
    }

    function renderExplanation(data) {
        if (!explanationContainer) return;
        explanationContainer.style.display = "block";

        let html = `
            <div class="card" style="margin-top: 24px; border-top: 4px solid var(--primary);">
                <h3 style="margin-bottom: 14px;">Simplified Medical Report Breakdown</h3>
                <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 20px;">${data.summary}</p>

                <div class="result-section">
                    <h4><span>📖</span> Key Medical Terms Explained</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-top: 10px;">
                        ${(data.important_terms || []).map(t => `
                            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-color);">
                                <strong style="color: var(--primary);">${t.term}</strong>
                                <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">${t.explanation}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="result-section" style="margin-top: 20px;">
                    <h4><span>🔍</span> Noteworthy Values / Sections to Discuss</h4>
                    <ul style="padding-left: 20px; color: var(--text-muted); font-size: 14px;">
                        ${(data.flagged_sections || []).map(f => `<li style="margin-bottom: 4px;">${f}</li>`).join('')}
                    </ul>
                </div>

                <div class="result-section" style="margin-top: 20px;">
                    <h4><span>❓</span> Suggested Questions to Ask Your Doctor</h4>
                    <ul style="padding-left: 20px; color: var(--accent); font-size: 14px;">
                        ${(data.suggested_questions || []).map(q => `<li style="margin-bottom: 6px;"><strong>${q}</strong></li>`).join('')}
                    </ul>
                </div>

                <div class="disclaimer-banner" style="margin-top: 20px;">
                    <span class="icon">ℹ️</span>
                    <div><strong>Clinical Disclaimer:</strong> ${data.disclaimer}</div>
                </div>
            </div>
        `;

        explanationContainer.innerHTML = html;
        explanationContainer.scrollIntoView({ behavior: "smooth" });
    }
});
