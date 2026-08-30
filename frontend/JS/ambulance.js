// =====================================================
// CARECONNECT - AMBULANCE MODULE LOGIC (ambulance.js)
// =====================================================

document.addEventListener("DOMContentLoaded", function () {
    console.log("AMBULANCE JS INITIALIZED");

    function getApiBaseUrl() {
        if (window.CareConnectConfig && typeof window.CareConnectConfig.getApiBaseUrl === "function") {
            return window.CareConnectConfig.getApiBaseUrl();
        }
        return "http://127.0.0.1:5000";
    }

    const locationButton = document.getElementById("locationButton");
    const refreshButton = document.getElementById("refreshLocationButton");
    const openMapButton = document.getElementById("openMapButton");
    const directionsButton = document.getElementById("directionsButton");
    const findAmbulanceButton = document.getElementById("findAmbulanceButton");
    const autoFillLocationBtn = document.getElementById("autoFillLocationBtn");
    const ambulanceRequestForm = document.getElementById("ambulanceRequestForm");

    let latitude = null;
    let longitude = null;

    // Pre-fill patient name/phone from logged in user if available
    const userData = localStorage.getItem("careconnect_user") || localStorage.getItem("user");
    if (userData) {
        try {
            const user = JSON.parse(userData);
            const pName = document.getElementById("patientName");
            const cNumber = document.getElementById("contactNumber");
            if (pName && !pName.value && user.name) pName.value = user.name;
            if (cNumber && !cNumber.value && (user.phone || user.emergency_phone)) cNumber.value = user.phone || user.emergency_phone;
        } catch (e) {
            console.warn("Could not pre-fill user info in ambulance form:", e);
        }
    }

    // =====================================================
    // 1. AMBULANCE REQUEST FORM SUBMIT
    // =====================================================
    if (ambulanceRequestForm) {
        ambulanceRequestForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const patientName = (document.getElementById("patientName")?.value || "").trim();
            const contactNumber = (document.getElementById("contactNumber")?.value || "").trim();
            const emergencyType = (document.getElementById("emergencyType")?.value || "General Medical Emergency").trim();
            const currentLocation = (document.getElementById("currentLocation")?.value || "").trim();
            const additionalDetails = (document.getElementById("additionalDetails")?.value || "").trim();
            const submitBtn = document.getElementById("requestAmbulanceBtn");
            const msgContainer = document.getElementById("ambulanceRequestMessage");

            if (!patientName || !contactNumber || !currentLocation) {
                if (msgContainer) {
                    msgContainer.style.display = "block";
                    msgContainer.style.padding = "14px";
                    msgContainer.style.borderRadius = "8px";
                    msgContainer.style.background = "#fee2e2";
                    msgContainer.style.color = "#991b1b";
                    msgContainer.textContent = "Please fill in all required fields (Patient Name, Contact Number, Location).";
                }
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "Submitting Emergency Request...";
            }

            try {
                const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
                const headers = { "Content-Type": "application/json" };
                if (token) {
                    headers["Authorization"] = "Bearer " + token;
                }

                const response = await fetch(`${getApiBaseUrl()}/api/ambulance/request`, {
                    method: "POST",
                    headers: headers,
                    body: JSON.stringify({
                        patient_name: patientName,
                        contact_number: contactNumber,
                        emergency_type: emergencyType,
                        current_location: currentLocation,
                        additional_details: additionalDetails
                    })
                });

                const data = await response.json();
                if (msgContainer) {
                    msgContainer.style.display = "block";
                    msgContainer.style.padding = "16px";
                    msgContainer.style.borderRadius = "8px";

                    if (response.ok && data.success) {
                        msgContainer.style.background = "#dcfce7";
                        msgContainer.style.color = "#166534";
                        msgContainer.style.border = "1px solid #bbf7d0";
                        msgContainer.innerHTML = `
                            <strong>✅ Ambulance request submitted successfully.</strong><br>
                            <span style="font-size:14px;">${data.message}</span><br>
                            <span style="font-size:13px; color:#15803d; margin-top:6px; display:inline-block;">Dispatch Tracking ID: <code>${data.request_id}</code> (Status: ${data.status})</span>
                        `;
                        ambulanceRequestForm.reset();
                    } else {
                        msgContainer.style.background = "#fee2e2";
                        msgContainer.style.color = "#991b1b";
                        msgContainer.style.border = "1px solid #fecaca";
                        msgContainer.textContent = data.message || "Failed to submit ambulance request.";
                    }
                }
            } catch (error) {
                console.error("Ambulance request error:", error);
                if (msgContainer) {
                    msgContainer.style.display = "block";
                    msgContainer.style.padding = "14px";
                    msgContainer.style.borderRadius = "8px";
                    msgContainer.style.background = "#fee2e2";
                    msgContainer.style.color = "#991b1b";
                    msgContainer.textContent = "Cannot connect to CareConnect server. Please dial 112 / 911 for immediate emergency assistance.";
                }
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "🚑 Request Ambulance";
                }
            }
        });
    }

    // =====================================================
    // 2. GEOLOCATION RADAR
    // =====================================================
    function getLocation() {
        const status = document.getElementById("locationStatus");
        const address = document.getElementById("mapAddress");
        const locationMessage = document.getElementById("locationMessage");
        const map = document.getElementById("ambulanceMap");

        if (!navigator.geolocation) {
            alert("Your browser does not support geolocation.");
            return;
        }

        if (locationButton) {
            locationButton.disabled = true;
            locationButton.textContent = "📍 Detecting Location...";
        }
        if (status) status.textContent = "📍 Detecting Location...";

        navigator.geolocation.getCurrentPosition(
            function (position) {
                latitude = position.coords.latitude;
                longitude = position.coords.longitude;

                console.log("GPS Detected:", latitude, longitude);

                if (locationButton) {
                    locationButton.disabled = false;
                    locationButton.textContent = "🔄 Update My Location";
                }
                if (status) {
                    status.textContent = "✅ Location Detected";
                    status.style.background = "#dcfce7";
                    status.style.color = "#166534";
                }
                if (address) {
                    address.textContent = `📍 Coordinates: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
                }
                if (locationMessage) {
                    locationMessage.textContent = "✅ Real-time coordinates synced with ambulance radar.";
                }

                // Update location input field if empty
                const locInput = document.getElementById("currentLocation");
                if (locInput && !locInput.value) {
                    locInput.value = `Lat ${latitude.toFixed(5)}, Lng ${longitude.toFixed(5)}`;
                }

                // Update Google Maps embed
                if (map) {
                    map.src = `https://www.google.com/maps?q=ambulance+hospital+near+${latitude},${longitude}&z=14&output=embed`;
                }
            },
            function (error) {
                console.warn("Location error:", error);
                if (locationButton) {
                    locationButton.disabled = false;
                    locationButton.textContent = "📍 Use My Current Location";
                }
                if (status) {
                    status.textContent = "⚠️ Location Unavailable";
                    status.style.background = "#fff7ed";
                    status.style.color = "#c2410c";
                }
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }

    if (locationButton) locationButton.addEventListener("click", getLocation);
    if (refreshButton) refreshButton.addEventListener("click", getLocation);
    if (autoFillLocationBtn) autoFillLocationBtn.addEventListener("click", getLocation);

    // =====================================================
    // 3. MAP ACTIONS
    // =====================================================
    function openAmbulanceSearch() {
        const query = (latitude !== null && longitude !== null)
            ? `ambulance+near+${latitude},${longitude}`
            : "ambulance+near+me";
        window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`, "_blank");
    }

    function startDirections() {
        const origin = (latitude !== null && longitude !== null) ? `${latitude},${longitude}` : "current+location";
        const destination = prompt("Enter hospital or ambulance service name:") || "nearest hospital emergency";
        if (destination.trim()) {
            window.open(`https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&travelmode=driving`, "_blank");
        }
    }

    if (openMapButton) openMapButton.addEventListener("click", openAmbulanceSearch);
    if (findAmbulanceButton) findAmbulanceButton.addEventListener("click", openAmbulanceSearch);
    if (directionsButton) directionsButton.addEventListener("click", startDirections);

    // Auto-detect location on load if permission is already granted
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                latitude = pos.coords.latitude;
                longitude = pos.coords.longitude;
                const map = document.getElementById("ambulanceMap");
                if (map) map.src = `https://www.google.com/maps?q=ambulance+hospital+near+${latitude},${longitude}&z=14&output=embed`;
                const address = document.getElementById("mapAddress");
                if (address) address.textContent = `📍 Coordinates: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
            },
            () => {},
            { timeout: 3000 }
        );
    }
});