// ===============================
// REGISTER
// ===============================

const registerForm = document.getElementById("registerForm");

if (registerForm) {

    registerForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name =
            document.getElementById("name").value.trim();

        const email =
            document.getElementById("email").value.trim();

        const password =
            document.getElementById("password").value;

        const confirmPassword =
            document.getElementById("confirmPassword").value;

        const message =
            document.getElementById("registerMessage");

        message.textContent = "";

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

            message.textContent =
                "Creating account...";

            const response = await fetch(
                "http://127.0.0.1:5000/api/register",
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

            if (response.ok && data.success) {

                message.textContent =
                    "Registration successful!";

                registerForm.reset();

            } else {

                message.textContent =
                    data.message ||
                    "Registration failed.";
            }

        } catch (error) {

            console.error(
                "Registration error:",
                error
            );

            message.textContent =
                "Unable to connect to the server.";
        }
    });
}


// ===============================
// LOGIN
// ===============================

const loginForm =
    document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const email =
                document.getElementById("loginEmail")
                    .value
                    .trim();

            const password =
                document.getElementById("loginPassword")
                    .value;

            const message =
                document.getElementById("loginMessage");

            message.textContent =
                "Logging in...";

            try {

                console.log(
                    "Sending login request..."
                );

                const response = await fetch(
                    "http://127.0.0.1:5000/api/login",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email: email,
                            password: password
                        })
                    }
                );

                console.log(
                    "Login status:",
                    response.status
                );

                const data =
                    await response.json();

                console.log(
                    "Login response:",
                    data
                );

                if (
                    response.ok &&
                    data.success
                ) {

                    localStorage.setItem(
                        "token",
                        data.token
                    );

                    localStorage.setItem(
                        "user",
                        JSON.stringify(data.user)
                    );

                    message.textContent =
                        "Login successful!";

                    // Redirect to dashboard
                    setTimeout(function () {

                        window.location.href =
                            "dashboard.html";

                    }, 500);

                } else {

                    message.textContent =
                        data.message ||
                        "Login failed.";
                }

            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );

                message.textContent =
                    "Unable to connect to the server.";
            }
        }
    );
}


// ===============================
// DASHBOARD
// ===============================

const userName =
    document.getElementById("userName");

const userEmail =
    document.getElementById("userEmail");

const welcomeMessage =
    document.getElementById("welcomeMessage");

if (userName && userEmail) {

    const token =
        localStorage.getItem("token");

    const userData =
        localStorage.getItem("user");

    if (!token || !userData) {

        window.location.href =
            "login.html";

    } else {

        try {

            const user =
                JSON.parse(userData);

            userName.textContent =
                user.name;

            userEmail.textContent =
                user.email;

            if (welcomeMessage) {

                welcomeMessage.textContent =
                    `Hello ${user.name}! Welcome back to CareConnect.`;
            }

        } catch (error) {

            console.error(
                "User data error:",
                error
            );

            localStorage.removeItem("token");
            localStorage.removeItem("user");

            window.location.href =
                "login.html";
        }
    }
}


// ===============================
// LOGOUT
// ===============================

const logoutButton =
    document.getElementById("logoutButton");

if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        function () {

            localStorage.removeItem("token");

            localStorage.removeItem("user");

            window.location.href =
                "login.html";
        }
    );
}


// ===============================
// MEDICAL PROFILE
// ===============================

const medicalProfileForm =
    document.getElementById("medicalProfileForm");

if (medicalProfileForm) {

    medicalProfileForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const token =
                localStorage.getItem("token");

            const medicalMessage =
                document.getElementById(
                    "medicalMessage"
                );

            if (!token) {

                window.location.href =
                    "login.html";

                return;
            }

            const bloodGroup =
                document.getElementById(
                    "bloodGroup"
                ).value.trim();

            const phone =
                document.getElementById(
                    "phone"
                ).value.trim();

            const allergies =
                document.getElementById(
                    "allergies"
                ).value.trim();

            const medications =
                document.getElementById(
                    "medications"
                ).value.trim();

            const conditions =
                document.getElementById(
                    "conditions"
                ).value.trim();

            const emergencyContact =
                document.getElementById(
                    "emergencyContact"
                ).value.trim();

            medicalMessage.textContent =
                "Saving medical profile...";

            try {

                const response = await fetch(
                    "http://127.0.0.1:5000/api/medical-profile",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Authorization":
                                "Bearer " + token
                        },

                        body: JSON.stringify({

                            blood_group:
                                bloodGroup,

                            phone:
                                phone,

                            allergies:
                                allergies,

                            medications:
                                medications,

                            conditions:
                                conditions,

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

                if (
                    response.ok &&
                    data.success
                ) {

                    medicalMessage.textContent =
                        "Medical profile saved successfully.";

                } else {

                    medicalMessage.textContent =
                        data.message ||
                        "Unable to save medical profile.";
                }

            } catch (error) {

                console.error(
                    "Medical profile error:",
                    error
                );

                medicalMessage.textContent =
                    "Unable to connect to the server.";
            }
        }
    );
}


// ===============================
// MEDICAL QR PASSPORT
// ===============================

const generateQRButton =
    document.getElementById(
        "generateQRButton"
    );

if (generateQRButton) {

    generateQRButton.addEventListener(
        "click",
        async function () {

            const token =
                localStorage.getItem("token");

            const qrMessage =
                document.getElementById(
                    "qrMessage"
                );

            const qrContainer =
                document.getElementById(
                    "qrContainer"
                );

            if (!token) {

                window.location.href =
                    "login.html";

                return;
            }

            try {

                qrMessage.textContent =
                    "Generating QR code...";

                qrContainer.innerHTML = "";

                const response = await fetch(
                    "http://127.0.0.1:5000/api/generate-qr",
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

                if (
                    response.ok &&
                    data.success
                ) {

                    qrMessage.textContent =
                        data.message ||
                        "QR generated successfully.";

                    if (data.qr_code) {

                        const image =
                            document.createElement(
                                "img"
                            );

                        image.src =
                            "data:image/png;base64," +
                            data.qr_code;

                        image.alt =
                            "CareConnect Medical QR";

                        image.style.width =
                            "250px";

                        image.style.height =
                            "250px";

                        image.style.marginTop =
                            "20px";

                        qrContainer.appendChild(
                            image
                        );
                    }

                } else {

                    qrMessage.textContent =
                        data.message ||
                        "Unable to generate QR.";
                }

            } catch (error) {

    console.error("LOGIN ERROR:", error);

    message.textContent =
        "Login error: " + error.message;
}
        }
    );
}
const sosButton = document.getElementById("sosButton");

if (sosButton) {

    sosButton.addEventListener("click", async function () {

        const token = localStorage.getItem("token");
        const sosMessage = document.getElementById("sosMessage");

        if (!token) {
            window.location.href = "login.html";
            return;
        }

        sosButton.disabled = true;
        sosMessage.textContent = "Activating Emergency SOS...";

        try {

            navigator.geolocation.getCurrentPosition(

                async function (position) {

                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;

                    const response = await fetch(
                        "http://127.0.0.1:5000/api/sos",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type": "application/json",
                                "Authorization": "Bearer " + token
                            },

                            body: JSON.stringify({
                                latitude: latitude,
                                longitude: longitude
                            })
                        }
                    );

                    const data = await response.json();

                    console.log("SOS response:", data);

                    if (response.ok && data.success) {

                        sosMessage.textContent =
                            "🚨 Emergency SOS activated successfully!";

                    } else {

                        sosMessage.textContent =
                            data.message || "SOS activation failed.";

                    }

                    sosButton.disabled = false;
                },

                function (error) {

                    console.error("Location error:", error);

                    sosMessage.textContent =
                        "Please allow location access.";

                    sosButton.disabled = false;
                }
            );

        } catch (error) {

            console.error("SOS error:", error);

            sosMessage.textContent =
                "Unable to connect to server.";

            sosButton.disabled = false;
        }

    });

}