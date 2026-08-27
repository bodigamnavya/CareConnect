// =====================================================
// AI SCAN RESULT PRESENTATION
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const urlParams = new URLSearchParams(window.location.search);
    const scanId = urlParams.get("id");

    const scanIdEl = document.getElementById("resultScanId");
    const scanTypeEl = document.getElementById("resultScanType");
    const resultTitleEl = document.getElementById("resultTitle");
    const confidenceBadgeEl = document.getElementById("resultConfidence");
    const resultImageEl = document.getElementById("resultImage");
    const explanationEl = document.getElementById("resultExplanation");
    const possibleMeaningEl = document.getElementById("resultPossibleMeaning");
    const recommendationEl = document.getElementById("resultRecommendation");
    const warningSignsEl = document.getElementById("resultWarningSigns");
    const disclaimerEl = document.getElementById("resultDisclaimer");
    const downloadReportBtn = document.getElementById("downloadReportBtn");
    const askAiBtn = document.getElementById("askAiBtn");

    let currentScan = null;

    // Check session storage first or fetch from backend API
    const cached = sessionStorage.getItem("latest_scan_result");
    if (cached && (!scanId || JSON.parse(cached).id === scanId)) {
        try {
            currentScan = JSON.parse(cached);
            renderResult(currentScan);
        } catch (e) {}
    }

    if (!currentScan && scanId) {
        try {
            const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/scans/${scanId}`, {
                headers: CareConnectConfig.getAuthHeaders()
            });
            const data = await res.json();
            if (res.ok && data.success && data.scan) {
                currentScan = data.scan;
                renderResult(currentScan);
            } else {
                CareConnectConfig.showToast(data.message || "Failed to load scan details.", "error");
            }
        } catch (err) {
            console.error("Fetch scan error:", err);
            CareConnectConfig.showToast("Error connecting to server.", "error");
        }
    }

    function renderResult(scan) {
        if (scanIdEl) scanIdEl.textContent = scan.id;
        if (scanTypeEl) scanTypeEl.textContent = scan.scan_type;
        if (resultTitleEl) resultTitleEl.textContent = scan.result;
        if (confidenceBadgeEl) confidenceBadgeEl.textContent = `${scan.confidence}% Confidence`;
        
        if (resultImageEl && scan.image_url) {
            const baseUrl = CareConnectConfig.getApiBaseUrl();
            resultImageEl.src = scan.image_url.startsWith("http") ? scan.image_url : `${baseUrl}${scan.image_url}`;
        }
        
        if (explanationEl) explanationEl.textContent = scan.explanation;
        if (possibleMeaningEl) possibleMeaningEl.textContent = scan.possible_meaning;
        if (recommendationEl) recommendationEl.textContent = scan.recommendation;
        if (warningSignsEl) warningSignsEl.textContent = scan.warning_signs;
        if (disclaimerEl) disclaimerEl.textContent = scan.disclaimer;
    }

    // Report Generation & Download Action
    if (downloadReportBtn) {
        downloadReportBtn.addEventListener("click", async () => {
            const idToUse = currentScan ? currentScan.id : scanId;
            if (!idToUse) {
                CareConnectConfig.showToast("No scan selected to generate report.", "error");
                return;
            }

            downloadReportBtn.disabled = true;
            downloadReportBtn.innerHTML = `<span class="spinner"></span> Generating Report...`;

            try {
                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/reports/generate`, {
                    method: "POST",
                    headers: CareConnectConfig.getAuthHeaders(),
                    body: JSON.stringify({ scan_id: idToUse })
                });

                const data = await res.json();
                if (res.ok && data.success && data.download_url) {
                    CareConnectConfig.showToast("Report generated! Opening document...", "success");
                    const fullUrl = data.download_url.startsWith("http") ? data.download_url : `${CareConnectConfig.getApiBaseUrl()}${data.download_url}`;
                    window.open(fullUrl, "_blank");
                } else {
                    CareConnectConfig.showToast(data.message || "Failed to generate report.", "error");
                }
            } catch (err) {
                console.error("Report generate error:", err);
                CareConnectConfig.showToast("Error generating clinical report.", "error");
            } finally {
                downloadReportBtn.disabled = false;
                downloadReportBtn.innerHTML = `<span>📄</span> Download Report`;
            }
        });
    }

    if (askAiBtn) {
        askAiBtn.addEventListener("click", () => {
            if (currentScan) {
                sessionStorage.setItem("ai_prompt_context", `I just scanned a ${currentScan.scan_type} and the AI detected: "${currentScan.result}". Could you explain this in more detail?`);
            }
            window.location.href = "ai-assistant.html";
        });
    }
});
