// =====================================================
// CARECONNECT - GLOBAL SCRIPT (script.js)
// =====================================================

function getApiBaseUrl() {
    if (window.CareConnectConfig && typeof window.CareConnectConfig.getApiBaseUrl === "function") {
        return window.CareConnectConfig.getApiBaseUrl();
    }
    if (typeof window !== "undefined" && window.location && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") {
        return window.location.origin;
    }
    return "http://127.0.0.1:5000";
}

// =====================================================
// REGISTER (Fallback support if auth.js is not loaded)
// =====================================================
const registerForm = document.getElementById("registerForm");
if (registerForm && !window.__auth_registered) {
    window.__auth_registered = true;
}

// =====================================================
// DASHBOARD AUTHENTICATION & GREETING
// =====================================================
const userName = document.getElementById("userName");
const userEmail = document.getElementById("userEmail");
const welcomeMessage = document.getElementById("welcomeMessage");
const userGreeting = document.getElementById("userGreeting");

if (userName || userEmail || welcomeMessage || userGreeting) {
    const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
    const userData = localStorage.getItem("careconnect_user") || localStorage.getItem("user");

    if (userData) {
        try {
            const user = JSON.parse(userData);
            if (userName) userName.textContent = user.name || "User";
            if (userEmail) userEmail.textContent = user.email || "";
            if (welcomeMessage) welcomeMessage.textContent = `Hello ${user.name || "User"}! Welcome back to CareConnect.`;
            if (userGreeting) userGreeting.textContent = `Welcome back, ${user.name || "User"}`;
        } catch (error) {
            console.error("Dashboard user data error:", error);
        }
    }
}

// =====================================================
// LOGOUT
// =====================================================
const logoutBtn = document.getElementById("logoutButton");
if (logoutBtn) {
    logoutBtn.addEventListener("click", function (event) {
        event.preventDefault();
        if (window.CareConnectConfig && typeof window.CareConnectConfig.clearSession === "function") {
            window.CareConnectConfig.clearSession();
        } else {
            localStorage.removeItem("careconnect_token");
            localStorage.removeItem("careconnect_user");
            localStorage.removeItem("token");
            localStorage.removeItem("user");
        }
        window.location.href = "login.html";
    });
}

// =====================================================
// MEDICAL PROFILE
// =====================================================
const medicalProfileForm = document.getElementById("medicalProfileForm");
if (medicalProfileForm) {
    // Populate existing profile data if available
    (async function loadExistingMedicalProfile() {
        const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
        if (!token) return;
        try {
            const response = await fetch(`${getApiBaseUrl()}/api/profile`, {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + token
                }
            });
            const data = await response.json();
            if (response.ok && data.success && data.profile) {
                const p = data.profile;
                if (document.getElementById("bloodGroup") && p.blood_group) document.getElementById("bloodGroup").value = p.blood_group;
                if (document.getElementById("phone") && (p.emergency_phone || p.phone)) document.getElementById("phone").value = p.emergency_phone || p.phone;
                if (document.getElementById("allergies") && p.allergies) document.getElementById("allergies").value = p.allergies;
                if (document.getElementById("medications") && p.medications) document.getElementById("medications").value = p.medications;
                if (document.getElementById("conditions") && p.conditions) document.getElementById("conditions").value = p.conditions;
                if (document.getElementById("emergencyContact") && p.emergency_contact) document.getElementById("emergencyContact").value = p.emergency_contact;
            }
        } catch (err) {
            console.warn("Could not pre-fetch medical profile:", err);
        }
    })();

    medicalProfileForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
        const message = document.getElementById("medicalMessage");

        if (!token) {
            window.location.href = "login.html";
            return;
        }

        const bloodGroup = document.getElementById("bloodGroup") ? document.getElementById("bloodGroup").value : "";
        const phone = document.getElementById("phone") ? document.getElementById("phone").value.trim() : "";
        const allergies = document.getElementById("allergies") ? document.getElementById("allergies").value.trim() : "";
        const medications = document.getElementById("medications") ? document.getElementById("medications").value.trim() : "";
        const conditions = document.getElementById("conditions") ? document.getElementById("conditions").value.trim() : "";
        const emergencyContact = document.getElementById("emergencyContact") ? document.getElementById("emergencyContact").value.trim() : "";

        if (message) {
            message.textContent = "Saving medical profile...";
            message.style.color = "#2563eb";
        }

        try {
            const response = await fetch(`${getApiBaseUrl()}/api/medical-profile`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token
                },
                body: JSON.stringify({
                    blood_group: bloodGroup,
                    phone: phone,
                    allergies: allergies,
                    medications: medications,
                    conditions: conditions,
                    emergency_contact: emergencyContact
                })
            });

            const data = await response.json();
            if (response.ok && data.success) {
                if (message) {
                    message.textContent = "Medical profile saved successfully.";
                    message.style.color = "#166534";
                }
            } else {
                if (message) {
                    message.textContent = data.message || "Unable to save medical profile.";
                    message.style.color = "#991b1b";
                }
            }
        } catch (error) {
            console.error("Medical profile error:", error);
            if (message) {
                message.textContent = "Cannot connect to CareConnect server. Please check that the backend is running.";
                message.style.color = "#991b1b";
            }
        }
    });
}

// =====================================================
// MEDICAL QR PASSPORT
// =====================================================
const generateQRButton = document.getElementById("generateQRButton");
if (generateQRButton) {
    generateQRButton.addEventListener("click", async function () {
        const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
        const qrMessage = document.getElementById("qrMessage");
        const qrContainer = document.getElementById("qrContainer");

        if (!token) {
            window.location.href = "login.html";
            return;
        }

        if (qrMessage) {
            qrMessage.textContent = "Generating QR code...";
            qrMessage.style.color = "#2563eb";
        }
        if (qrContainer) qrContainer.innerHTML = "";

        try {
            const response = await fetch(`${getApiBaseUrl()}/api/generate-qr`, {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + token
                }
            });

            const data = await response.json();
            if (response.ok && data.success) {
                if (qrMessage) {
                    qrMessage.textContent = data.message || "QR generated successfully.";
                    qrMessage.style.color = "#166534";
                }
                if (data.qr_code && qrContainer) {
                    const image = document.createElement("img");
                    image.src = "data:image/png;base64," + data.qr_code;
                    image.alt = "CareConnect Medical QR";
                    image.style.width = "250px";
                    image.style.height = "250px";
                    image.style.borderRadius = "12px";
                    image.style.boxShadow = "0 4px 15px rgba(0,0,0,0.1)";
                    image.style.marginTop = "15px";
                    qrContainer.appendChild(image);
                }
            } else {
                if (qrMessage) {
                    qrMessage.textContent = data.message || "Unable to generate QR. Please ensure your medical profile is filled.";
                    qrMessage.style.color = "#991b1b";
                }
            }
        } catch (error) {
            console.error("QR error:", error);
            if (qrMessage) {
                qrMessage.textContent = "Cannot connect to CareConnect server. Please check that the backend is running.";
                qrMessage.style.color = "#991b1b";
            }
        }
    });
}

// =====================================================
// EMERGENCY SOS
// =====================================================
const sosButton = document.getElementById("sosButton");
if (sosButton) {
    sosButton.addEventListener("click", async function () {
        const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
        const sosMessage = document.getElementById("sosMessage");

        if (!token) {
            window.location.href = "login.html";
            return;
        }

        sosButton.disabled = true;
        if (sosMessage) {
            sosMessage.textContent = "Getting your location...";
            sosMessage.style.color = "#2563eb";
        }

        async function triggerSOS(latitude = null, longitude = null) {
            if (sosMessage) sosMessage.textContent = "Activating Emergency SOS...";

            try {
                const response = await fetch(`${getApiBaseUrl()}/api/sos`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + token
                    },
                    body: JSON.stringify({
                        latitude: latitude,
                        longitude: longitude,
                        message: "Emergency! I need medical assistance."
                    })
                });

                const data = await response.json();
                if (response.ok && data.success) {
                    if (sosMessage) {
                        sosMessage.textContent = "🚨 Emergency SOS activated successfully! Emergency broadcast logged.";
                        sosMessage.style.color = "#166534";
                    }
                } else {
                    if (sosMessage) {
                        sosMessage.textContent = data.message || "SOS activation failed.";
                        sosMessage.style.color = "#991b1b";
                    }
                }
            } catch (error) {
                console.error("SOS error:", error);
                if (sosMessage) {
                    sosMessage.textContent = "Cannot connect to CareConnect server.";
                    sosMessage.style.color = "#991b1b";
                }
            } finally {
                sosButton.disabled = false;
            }
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    triggerSOS(position.coords.latitude, position.coords.longitude);
                },
                function (error) {
                    console.warn("Location error:", error);
                    triggerSOS(null, null);
                },
                { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
            );
        } else {
            triggerSOS(null, null);
        }
    });
}

// =====================================================
// SOS HISTORY
// =====================================================
const historyContainer = document.getElementById("historyContainer");
if (historyContainer) {
    const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
    if (!token) {
        window.location.href = "login.html";
    } else {
        async function loadSOSHistory() {
            historyContainer.innerHTML = "<p>Loading SOS history...</p>";
            try {
                const response = await fetch(`${getApiBaseUrl()}/api/sos/history`, {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + token
                    }
                });

                const data = await response.json();
                if (response.ok && data.success) {
                    if (!data.events || data.events.length === 0) {
                        historyContainer.innerHTML = "<p style='color:#64748b;'>No SOS emergency events recorded yet.</p>";
                        return;
                    }

                    historyContainer.innerHTML = "";
                    data.events.forEach(function (event) {
                        const item = document.createElement("div");
                        item.className = "sos-history-item";
                        item.style.background = "#ffffff";
                        item.style.padding = "20px";
                        item.style.borderRadius = "12px";
                        item.style.boxShadow = "0 2px 10px rgba(0,0,0,0.06)";
                        item.style.marginBottom = "15px";

                        const createdAt = event.created_at ? new Date(event.created_at).toLocaleString() : "N/A";

                        item.innerHTML = `
                            <h3 style="margin:0 0 10px 0; color:#dc2626;">🚨 Emergency SOS Trigger</h3>
                            <p style="margin:4px 0;"><strong>Status:</strong> <span style="color:#16a34a; font-weight:600;">${event.status || "ACTIVE"}</span></p>
                            <p style="margin:4px 0;"><strong>Message:</strong> ${event.message || "Emergency assistance requested."}</p>
                            <p style="margin:4px 0;"><strong>Coordinates:</strong> ${event.latitude ?? "N/A"}, ${event.longitude ?? "N/A"}</p>
                            <p style="margin:4px 0; font-size:13px; color:#64748b;"><strong>Timestamp:</strong> ${createdAt}</p>
                        `;
                        historyContainer.appendChild(item);
                    });
                } else {
                    historyContainer.innerHTML = `<p style='color:#991b1b;'>${data.message || "Unable to load SOS history."}</p>`;
                }
            } catch (error) {
                console.error("SOS history error:", error);
                historyContainer.innerHTML = "<p style='color:#991b1b;'>Cannot connect to CareConnect server.</p>";
            }
        }
        loadSOSHistory();
    }
}