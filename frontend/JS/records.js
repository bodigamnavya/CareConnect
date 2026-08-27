// =====================================================
// HEALTH RECORDS MANAGEMENT
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const recordsGrid = document.getElementById("recordsGrid");
    const recordForm = document.getElementById("recordForm");
    const categoryTags = document.querySelectorAll(".category-tag");
    const emptyState = document.getElementById("recordsEmptyState");

    let currentFilter = "all";

    async function loadRecords() {
        try {
            const url = currentFilter === "all" 
                ? `${CareConnectConfig.getApiBaseUrl()}/api/health-records`
                : `${CareConnectConfig.getApiBaseUrl()}/api/health-records?category=${encodeURIComponent(currentFilter)}`;

            const res = await fetch(url, { headers: CareConnectConfig.getAuthHeaders() });
            const data = await res.json();
            if (res.ok && data.success) {
                renderRecords(data.records || []);
            }
        } catch (err) {
            console.error("Fetch records error:", err);
        }
    }

    function renderRecords(records) {
        if (!recordsGrid) return;
        recordsGrid.innerHTML = "";

        if (records.length === 0) {
            if (emptyState) emptyState.style.display = "block";
            return;
        }

        if (emptyState) emptyState.style.display = "none";

        records.forEach(rec => {
            const card = document.createElement("div");
            card.className = "record-card";
            
            let badgeClass = "badge-primary";
            if (rec.category.toLowerCase() === "allergy") badgeClass = "badge-danger";
            if (rec.category.toLowerCase() === "condition") badgeClass = "badge-warning";
            if (rec.category.toLowerCase() === "medication") badgeClass = "badge-success";

            card.innerHTML = `
                <div>
                    <div class="record-header">
                        <span class="badge ${badgeClass}">${rec.category}</span>
                        <span style="font-size: 12px; color: var(--text-dim);">${rec.severity || 'Moderate'}</span>
                    </div>
                    <h4 class="record-title">${rec.title}</h4>
                    <p class="record-details">${rec.details || 'No additional notes provided.'}</p>
                    ${rec.start_date ? `<p style="font-size: 12px; color: var(--text-dim); margin-bottom: 12px;">Recorded since: ${rec.start_date}</p>` : ''}
                </div>
                <div class="record-actions">
                    <button class="btn btn-danger btn-sm delete-rec-btn" data-id="${rec.id}">Delete</button>
                </div>
            `;
            recordsGrid.appendChild(card);
        });

        document.querySelectorAll(".delete-rec-btn").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const recId = e.currentTarget.getAttribute("data-id");
                if (confirm("Delete this health record?")) {
                    try {
                        const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/health-records/${recId}`, {
                            method: "DELETE",
                            headers: CareConnectConfig.getAuthHeaders()
                        });
                        const data = await res.json();
                        if (res.ok && data.success) {
                            CareConnectConfig.showToast("Record removed.", "success");
                            loadRecords();
                        }
                    } catch (err) {
                        CareConnectConfig.showToast("Failed to delete record.", "error");
                    }
                }
            });
        });
    }

    // Category filter tabs
    categoryTags.forEach(tag => {
        tag.addEventListener("click", () => {
            categoryTags.forEach(t => t.classList.remove("active"));
            tag.classList.add("active");
            currentFilter = tag.getAttribute("data-category");
            loadRecords();
        });
    });

    // Form Submission
    if (recordForm) {
        recordForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const category = document.getElementById("recordCategory").value;
            const title = document.getElementById("recordTitle").value.trim();
            const details = document.getElementById("recordDetails").value.trim();
            const severity = document.getElementById("recordSeverity").value;
            const startDate = document.getElementById("recordDate").value;

            if (!title) {
                CareConnectConfig.showToast("Record title is required.", "error");
                return;
            }

            try {
                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/health-records`, {
                    method: "POST",
                    headers: CareConnectConfig.getAuthHeaders(),
                    body: JSON.stringify({
                        category, title, details, severity, start_date: startDate
                    })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    CareConnectConfig.showToast("Health record saved!", "success");
                    recordForm.reset();
                    loadRecords();
                } else {
                    CareConnectConfig.showToast(data.message || "Failed to save record.", "error");
                }
            } catch (err) {
                console.error("Save record error:", err);
                CareConnectConfig.showToast("Server connection error.", "error");
            }
        });
    }

    loadRecords();
});
