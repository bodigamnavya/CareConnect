// =====================================================
// SCAN HISTORY & MANAGEMENT
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const historyContainer = document.getElementById("historyGrid");
    const searchInput = document.getElementById("historySearch");
    const typeFilter = document.getElementById("historyTypeFilter");
    const emptyState = document.getElementById("historyEmptyState");

    async function loadScans() {
        const queryParams = new URLSearchParams();
        if (searchInput && searchInput.value.trim()) queryParams.set("search", searchInput.value.trim());
        if (typeFilter && typeFilter.value !== "all") queryParams.set("type", typeFilter.value);

        try {
            const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/scans?${queryParams.toString()}`, {
                headers: CareConnectConfig.getAuthHeaders()
            });

            const data = await res.json();
            if (res.ok && data.success) {
                renderHistory(data.scans || []);
            } else {
                CareConnectConfig.showToast(data.message || "Failed to load scan history.", "error");
            }
        } catch (err) {
            console.error("History fetch error:", err);
            CareConnectConfig.showToast("Error connecting to server.", "error");
        }
    }

    function renderHistory(scans) {
        if (!historyContainer) return;
        historyContainer.innerHTML = "";

        if (scans.length === 0) {
            if (emptyState) emptyState.style.display = "block";
            return;
        }

        if (emptyState) emptyState.style.display = "none";

        scans.forEach(scan => {
            const card = document.createElement("div");
            card.className = "card record-card";
            const dateStr = scan.created_at ? new Date(scan.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';
            const imgUrl = scan.image_url ? (scan.image_url.startsWith("http") ? scan.image_url : `${CareConnectConfig.getApiBaseUrl()}${scan.image_url}`) : '';

            card.innerHTML = `
                <div class="record-header">
                    <div>
                        <span class="badge badge-primary">${scan.scan_type}</span>
                        <h4 class="record-title" style="margin-top: 8px;">${scan.result}</h4>
                        <span style="font-size: 12px; color: var(--text-dim);">${dateStr} • ID: ${scan.id.slice(0, 12)}...</span>
                    </div>
                    <span class="badge badge-success">${scan.confidence}% Match</span>
                </div>
                ${imgUrl ? `<div style="height: 140px; border-radius: 8px; overflow: hidden; margin-bottom: 14px; background: #000; display: flex; align-items: center; justify-content: center;"><img src="${imgUrl}" alt="Scan Image" style="max-height: 100%; max-width: 100%; object-fit: contain;"></div>` : ''}
                <p class="record-details">${scan.explanation ? scan.explanation.slice(0, 120) + '...' : ''}</p>
                <div class="record-actions">
                    <a href="scan-result.html?id=${scan.id}" class="btn btn-secondary btn-sm">View Result</a>
                    <button class="btn btn-danger btn-sm delete-scan-btn" data-id="${scan.id}">Delete</button>
                </div>
            `;

            historyContainer.appendChild(card);
        });

        // Bind delete buttons
        document.querySelectorAll(".delete-scan-btn").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const scanId = e.currentTarget.getAttribute("data-id");
                if (confirm("Are you sure you want to delete this scan record?")) {
                    try {
                        const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/scans/${scanId}`, {
                            method: "DELETE",
                            headers: CareConnectConfig.getAuthHeaders()
                        });
                        const data = await res.json();
                        if (res.ok && data.success) {
                            CareConnectConfig.showToast("Scan record deleted.", "success");
                            loadScans();
                        } else {
                            CareConnectConfig.showToast(data.message || "Failed to delete.", "error");
                        }
                    } catch (err) {
                        CareConnectConfig.showToast("Error deleting scan.", "error");
                    }
                }
            });
        });
    }

    if (searchInput) searchInput.addEventListener("input", () => loadScans());
    if (typeFilter) typeFilter.addEventListener("change", () => loadScans());

    loadScans();
});
