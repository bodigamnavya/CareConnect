// =====================================================
// CARECONNECT - FRONTEND SCRIPT
// =====================================================

// LIVE RENDER BACKEND
const API_BASE_URL = "https://careconnect-back-qf7e.onrender.com";


// =====================================================
// REGISTER
// =====================================================

const registerForm = document.getElementById("registerForm");

if (registerForm) {

    registerForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword =
            document.getElementById("confirmPassword").value;

        const message =
            document.getElementById("registerMessage");

        message.textContent = "Creating account...";

        if (!name || !email || !password || !confirmPassword) {

            message.textContent =
                "Please fill all fields.";

            return;
        }

        if (password.length < 6) {

            message.textContent =
                "Password must contain at least 6 characters.";

            return;
        }

        if (password !== confirmPassword) {

            message.textContent =
                "Passwords do not match.";

            return;
        }

        try {

            const response = await fetch(
                `${API_BASE_URL}/api/register`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        name: name,
                        email: email,
                        password: password
                    })
                }
            );

            const data = await response.json();

            console.log("Register response:", data);

            if (response.ok && data.success) {

                message.textContent =
                    "Registration successful! Redirecting to login...";

                registerForm.reset();

                setTimeout(function () {

                    window.location.href = "login.html";

                }, 1000);

            } else {

                message.textContent =
                    data.message || "Registration failed.";

            }

        } catch (error) {

            console.error("Registration error:", error);

            message.textContent =
                "Unable to connect to server.";

        }

    });

}


// =====================================================
// LOGIN
// =====================================================

const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const email =
            document.getElementById("loginEmail").value.trim();

        const password =
            document.getElementById("loginPassword").value;

        const message =
            document.getElementById("loginMessage");

        if (!email || !password) {

            message.textContent =
                "Please enter email and password.";

            return;
        }

        message.textContent = "Logging in...";

        try {

            console.log("Login request started");

            const response = await fetch(
                `${API_BASE_URL}/api/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                }
            );

            console.log("Login status:", response.status);

            const data = await response.json();

            console.log("Login response:", data);

            if (response.ok && data.success) {

                // Save JWT token
                localStorage.setItem(
                    "token",
                    data.token
                );

                // Save user information
                localStorage.setItem(
                    "user",
                    JSON.stringify(data.user)
                );

                message.textContent =
                    "Login successful! Opening dashboard...";

                console.log(
                    "Token saved:",
                    localStorage.getItem("token")
                );

                setTimeout(function () {

                    window.location.href = "./dashboard.html";

                }, 800);

            } else {

                message.textContent =
                    data.message || "Invalid email or password.";

            }

        } catch (error) {

            console.error("Login error:", error);

            message.textContent =
                "Unable to connect to server.";

        }

    });

}


// =====================================================
// DASHBOARD AUTHENTICATION
// =====================================================

const userName =
    document.getElementById("userName");

const userEmail =
    document.getElementById("userEmail");

const welcomeMessage =
    document.getElementById("welcomeMessage");

if (userName || userEmail || welcomeMessage) {

    const token =
        localStorage.getItem("token");

    const userData =
        localStorage.getItem("user");

    if (!token || !userData) {

        window.location.href = "./login.html";

    } else {

        try {

            const user =
                JSON.parse(userData);

            if (userName) {

                userName.textContent =
                    user.name || "User";

            }

            if (userEmail) {

                userEmail.textContent =
                    user.email || "";

            }

            if (welcomeMessage) {

                welcomeMessage.textContent =
                    `Hello ${user.name || "User"}! Welcome back to CareConnect.`;

            }

        } catch (error) {

            console.error(
                "Dashboard user data error:",
                error
            );

            localStorage.removeItem("token");
            localStorage.removeItem("user");

            window.location.href = "./login.html";

        }

    }

}


// =====================================================
// LOGOUT
// =====================================================

const logoutButton =
    document.getElementById("logoutButton");

if (logoutButton) {

    logoutButton.addEventListener("click", function (event) {

        event.preventDefault();

        localStorage.removeItem("token");
        localStorage.removeItem("user");

        window.location.href = "./login.html";

    });

}


// =====================================================
// MEDICAL PROFILE
// =====================================================

const medicalProfileForm =
    document.getElementById("medicalProfileForm");

if (medicalProfileForm) {

    medicalProfileForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const token =
                localStorage.getItem("token");

            const message =
                document.getElementById("medicalMessage");

            if (!token) {

                window.location.href = "./login.html";

                return;
            }

            const bloodGroup =
                document.getElementById("bloodGroup").value;

            const phone =
                document.getElementById("phone").value.trim();

            const allergies =
                document.getElementById("allergies").value.trim();

            const medications =
                document.getElementById("medications").value.trim();

            const conditions =
                document.getElementById("conditions").value.trim();

            const emergencyContact =
                document.getElementById("emergencyContact")
                    .value
                    .trim();

            message.textContent =
                "Saving medical profile...";

            try {

                const response = await fetch(
                    `${API_BASE_URL}/api/medical-profile`,
                    {
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

                            emergency_contact:
                                emergencyContact

                        })
                    }
                );

                const data =
                    await response.json();

                console.log(
                    "Medical profile response:",
                    data
                );

                if (response.ok && data.success) {

                    message.textContent =
                        "Medical profile saved successfully.";

                } else {

                    message.textContent =
                        data.message ||
                        "Unable to save medical profile.";

                }

            } catch (error) {

                console.error(
                    "Medical profile error:",
                    error
                );

                message.textContent =
                    "Unable to connect to server.";

            }

        }
    );

}


// =====================================================
// MEDICAL QR PASSPORT
// =====================================================

const generateQRButton =
    document.getElementById("generateQRButton");

if (generateQRButton) {

    generateQRButton.addEventListener(
        "click",
        async function () {

            const token =
                localStorage.getItem("token");

            const qrMessage =
                document.getElementById("qrMessage");

            const qrContainer =
                document.getElementById("qrContainer");

            if (!token) {

                window.location.href = "./login.html";

                return;
            }

            qrMessage.textContent =
                "Generating QR code...";

            qrContainer.innerHTML = "";

            try {

                const response = await fetch(
                    `${API_BASE_URL}/api/generate-qr`,
                    {
                        method: "GET",

                        headers: {
                            "Authorization":
                                "Bearer " + token
                        }
                    }
                );

                const data =
                    await response.json();

                console.log(
                    "QR response:",
                    data
                );

                if (response.ok && data.success) {

                    qrMessage.textContent =
                        data.message ||
                        "QR generated successfully.";

                    if (data.qr_code) {

                        const image =
                            document.createElement("img");

                        image.src =
                            "data:image/png;base64," +
                            data.qr_code;

                        image.alt =
                            "CareConnect Medical QR";

                        image.style.width = "250px";
                        image.style.height = "250px";

                        qrContainer.appendChild(image);

                    } else {

                        qrMessage.textContent =
                            "QR code was not returned by server.";

                    }

                } else {

                    qrMessage.textContent =
                        data.message ||
                        "Unable to generate QR.";

                }

            } catch (error) {

                console.error(
                    "QR error:",
                    error
                );

                qrMessage.textContent =
                    "Unable to connect to server.";

            }

        }
    );

}


// =====================================================
// EMERGENCY SOS
// =====================================================

const sosButton =
    document.getElementById("sosButton");

if (sosButton) {

    sosButton.addEventListener(
        "click",
        async function () {

            const token =
                localStorage.getItem("token");

            const sosMessage =
                document.getElementById("sosMessage");

            if (!token) {

                window.location.href = "./login.html";

                return;
            }

            if (!navigator.geolocation) {

                sosMessage.textContent =
                    "Geolocation is not supported.";

                return;
            }

            sosButton.disabled = true;

            sosMessage.textContent =
                "Getting your location...";

            navigator.geolocation.getCurrentPosition(

                async function (position) {

                    try {

                        const latitude =
                            position.coords.latitude;

                        const longitude =
                            position.coords.longitude;

                        sosMessage.textContent =
                            "Activating Emergency SOS...";

                        const response = await fetch(
                            `${API_BASE_URL}/api/sos`,
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json",

                                    "Authorization":
                                        "Bearer " + token
                                },

                                body: JSON.stringify({

                                    latitude: latitude,

                                    longitude: longitude,

                                    message:
                                        "Emergency! I need medical assistance."

                                })
                            }
                        );

                        const data =
                            await response.json();

                        console.log(
                            "SOS response:",
                            data
                        );

                        if (response.ok && data.success) {

                            sosMessage.textContent =
                                "🚨 Emergency SOS activated successfully!";

                        } else {

                            sosMessage.textContent =
                                data.message ||
                                "SOS activation failed.";

                        }

                    } catch (error) {

                        console.error(
                            "SOS error:",
                            error
                        );

                        sosMessage.textContent =
                            "Unable to connect to server.";

                    } finally {

                        sosButton.disabled = false;

                    }

                },

                function (error) {

                    console.error(
                        "Location error:",
                        error
                    );

                    if (error.code === 1) {

                        sosMessage.textContent =
                            "Please allow location access.";

                    } else {

                        sosMessage.textContent =
                            "Unable to get your location.";

                    }

                    sosButton.disabled = false;

                },

                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }

            );

        }
    );

}


// =====================================================
// SOS HISTORY
// =====================================================

const historyContainer =
    document.getElementById("historyContainer");

if (historyContainer) {

    const token =
        localStorage.getItem("token");

    if (!token) {

        window.location.href = "./login.html";

    } else {

        async function loadSOSHistory() {

            historyContainer.innerHTML =
                "<p>Loading SOS history...</p>";

            try {

                const response = await fetch(
                    `${API_BASE_URL}/api/sos/history`,
                    {
                        method: "GET",

                        headers: {
                            "Authorization":
                                "Bearer " + token
                        }
                    }
                );

                const data =
                    await response.json();

                console.log(
                    "SOS history response:",
                    data
                );

                if (response.ok && data.success) {

                    if (
                        !data.events ||
                        data.events.length === 0
                    ) {

                        historyContainer.innerHTML =
                            "<p>No SOS history found.</p>";

                        return;
                    }

                    historyContainer.innerHTML = "";

                    data.events.forEach(function (event) {

                        const item =
                            document.createElement("div");

                        item.className =
                            "sos-history-item";

                        const createdAt =
                            event.created_at
                                ? new Date(
                                    event.created_at
                                ).toLocaleString()
                                : "N/A";

                        item.innerHTML = `

                            <h3>
                                🚨 Emergency SOS
                            </h3>

                            <p>
                                <strong>Status:</strong>
                                ${event.status || "N/A"}
                            </p>

                            <p>
                                <strong>Message:</strong>
                                ${event.message || "N/A"}
                            </p>

                            <p>
                                <strong>Latitude:</strong>
                                ${event.latitude ?? "N/A"}
                            </p>

                            <p>
                                <strong>Longitude:</strong>
                                ${event.longitude ?? "N/A"}
                            </p>

                            <p>
                                <strong>Date:</strong>
                                ${createdAt}
                            </p>

                        `;

                        historyContainer.appendChild(item);

                    });

                } else {

                    historyContainer.innerHTML =
                        `<p>${
                            data.message ||
                            "Unable to load SOS history."
                        }</p>`;

                }

            } catch (error) {

                console.error(
                    "SOS history error:",
                    error
                );

                historyContainer.innerHTML =
                    "<p>Unable to connect to server.</p>";

            }

        }

        loadSOSHistory();

    }

}