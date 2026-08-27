// =====================================================
// DASHBOARD LOGIC
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const userGreeting = document.getElementById("userGreeting");
    const userInitials = document.getElementById("userInitials");
    const statTotalScans = document.getElementById("statTotalScans");
    const statHealthRecords = document.getElementById("statHealthRecords");
    const statRecentScan = document.getElementById("statRecentScan");
    const statReports = document.getElementById("statReports");
    const activityList = document.getElementById("activityList");

    // 1. Load User Profile Info
    const storedUserStr = localStorage.getItem("careconnect_user");
    if (storedUserStr) {
        try {
            const user = JSON.parse(storedUserStr);
            if (userGreeting) userGreeting.textContent = `Welcome back, ${user.name || 'Patient'}`;
            if (userInitials && user.name) userInitials.textContent = user.name.charAt(0).toUpperCase();
        } catch (e) {}
    }

    // 2. Fetch User Metrics and Recent Activity
    try {
        const [scansRes, recordsRes, reportsRes] = await Promise.all([
            fetch(`${CareConnectConfig.getApiBaseUrl()}/api/scans`, { headers: CareConnectConfig.getAuthHeaders() }),
            fetch(`${CareConnectConfig.getApiBaseUrl()}/api/health-records`, { headers: CareConnectConfig.getAuthHeaders() }),
            fetch(`${CareConnectConfig.getApiBaseUrl()}/api/reports`, { headers: CareConnectConfig.getAuthHeaders() })
        ]);

        const scansData = await scansRes.json();
        const recordsData = await recordsRes.json();
        const reportsData = await reportsRes.json();

        // Update Stat Cards
        if (scansData.success && statTotalScans) {
            statTotalScans.textContent = scansData.scans ? scansData.scans.length : 0;
            if (scansData.scans && scansData.scans.length > 0 && statRecentScan) {
                const latest = scansData.scans[0];
                statRecentScan.textContent = `${latest.scan_type} (${latest.confidence}%)`;
            }
        }

        if (recordsData.success && statHealthRecords) {
            statHealthRecords.textContent = recordsData.records ? recordsData.records.length : 0;
        }

        if (reportsData.success && statReports) {
            statReports.textContent = reportsData.reports ? reportsData.reports.length : 0;
        }

        // Render Recent Activity Timeline
        if (activityList) {
            activityList.innerHTML = "";
            const allActivities = [];

            if (scansData.scans) {
                scansData.scans.forEach(s => {
                    allActivities.push({
                        title: `Medical Scan: ${s.scan_type}`,
                        detail: `Detected result: ${s.result}`,
                        time: s.created_at,
                        icon: "🔬",
                        url: `scan-result.html?id=${s.id}`
                    });
                });
            }

            if (recordsData.records) {
                recordsData.records.forEach(r => {
                    allActivities.push({
                        title: `Health Record: ${r.title}`,
                        detail: `${r.category} (${r.severity || 'Recorded'})`,
                        time: r.created_at,
                        icon: "📋",
                        url: "health-records.html"
                    });
                });
            }

            if (allActivities.length === 0) {
                activityList.innerHTML = `<p style="color: var(--text-muted); font-size: 14px; text-align: center; padding: 20px;">No recent health activity. Start by uploading a medical scan or recording your health profile.</p>`;
            } else {
                allActivities.slice(0, 5).forEach(act => {
                    const item = document.createElement("div");
                    item.className = "activity-item";
                    const timeStr = act.time ? new Date(act.time).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recently';
                    
                    item.innerHTML = `
                        <div class="activity-meta">
                            <span class="activity-icon">${act.icon}</span>
                            <div>
                                <div class="activity-title">${act.title}</div>
                                <div class="activity-time">${act.detail} • ${timeStr}</div>
                            </div>
                        </div>
                        <a href="${act.url}" class="btn btn-secondary btn-sm">View</a>
                    `;
                    activityList.appendChild(item);
                });
            }
        }
    } catch (err) {
        console.error("Dashboard data load error:", err);
    }
});
