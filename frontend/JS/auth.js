document.addEventListener("DOMContentLoaded", function () {

const registerForm = document.getElementById("registerForm");
const loginForm = document.getElementById("loginForm");
const logoutButton = document.getElementById("logoutButton");

// ============================================
// API URL
// ============================================

function getApiBaseUrl() {

    if (
        typeof CareConnectConfig !== "undefined" &&
        typeof CareConnectConfig.getApiBaseUrl === "function"
    ) {
        return CareConnectConfig.getApiBaseUrl();
    }

    return "http://127.0.0.1:5000";
}


// ============================================
// MESSAGE
// ============================================

function showMessage(elementId, message, type) {

    const element = document.getElementById(elementId);

    if (!element) return;

    element.textContent = message;

    element.style.marginTop = "15px";
    element.style.padding = "12px";
    element.style.borderRadius = "8px";
    element.style.textAlign = "center";

    if (type === "success") {

        element.style.background = "#dcfce7";
        element.style.color = "#166534";

    } else {

        element.style.background = "#fee2e2";
        element.style.color = "#991b1b";

    }
}


// ============================================
// REGISTER
// ============================================

if (registerForm) {

    registerForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name = document
            .getElementById("name")
            .value
            .trim();

        const email = document
            .getElementById("email")
            .value
            .trim();

        const password = document
            .getElementById("password")
            .value;

        const confirmPassword = document
            .getElementById("confirmPassword")
            .value;

        const button =
            registerForm.querySelector(
                "button[type='submit']"
            );


        // ----------------------------------------
        // VALIDATION
        // ----------------------------------------

        if (!name) {

            showMessage(
                "registerMessage",
                "Please enter your full name.",
                "error"
            );

            return;
        }


        if (!email) {

            showMessage(
                "registerMessage",
                "Please enter your email address.",
                "error"
            );

            return;
        }


        if (password.length < 6) {

            showMessage(
                "registerMessage",
                "Password must contain at least 6 characters.",
                "error"
            );

            return;
        }


        if (password !== confirmPassword) {

            showMessage(
                "registerMessage",
                "Passwords do not match.",
                "error"
            );

            return;
        }


        // ----------------------------------------
        // BUTTON
        // ----------------------------------------

        if (button) {

            button.disabled = true;
            button.textContent = "Creating Account...";

        }


        try {

            const response = await fetch(
                getApiBaseUrl() + "/api/register",
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


            console.log(
                "REGISTER RESPONSE:",
                response.status,
                data
            );


            if (
                response.ok &&
                data.success === true
            ) {

                showMessage(
                    "registerMessage",
                    "Account created successfully! Redirecting to login...",
                    "success"
                );


                if (data.user) {

                    localStorage.setItem(
                        "careconnect_user",
                        JSON.stringify(data.user)
                    );

                }


                if (data.token) {

                    localStorage.setItem(
                        "careconnect_token",
                        data.token
                    );

                }


                setTimeout(function () {

                    window.location.href =
                        "login.html";

                }, 1500);


            } else {

                showMessage(
                    "registerMessage",
                    data.message ||
                    data.error ||
                    "Unable to create account.",
                    "error"
                );

            }


        } catch (error) {

            console.error(
                "REGISTER ERROR:",
                error
            );


            showMessage(
                "registerMessage",
                "Cannot connect to CareConnect server. Please make sure the backend is running.",
                "error"
            );


        } finally {

            if (button) {

                button.disabled = false;
                button.textContent = "Create Account";

            }

        }

    });

}


// ============================================
// LOGIN
// ============================================

if (loginForm) {

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();


        const email =
            document
                .getElementById("loginEmail")
                .value
                .trim();


        const password =
            document
                .getElementById("loginPassword")
                .value;


        const button =
            loginForm.querySelector(
                "button[type='submit']"
            );


        if (!email || !password) {

            showMessage(
                "loginMessage",
                "Please enter your email and password.",
                "error"
            );

            return;
        }


        if (button) {

            button.disabled = true;
            button.textContent = "Signing In...";

        }


        try {

            const response = await fetch(
                getApiBaseUrl() + "/api/login",
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


            const data = await response.json();


            console.log(
                "LOGIN RESPONSE:",
                response.status,
                data
            );


            if (
                response.ok &&
                data.success === true
            ) {

                if (data.token) {

                    localStorage.setItem(
                        "careconnect_token",
                        data.token
                    );

                }


                if (data.user) {

                    localStorage.setItem(
                        "careconnect_user",
                        JSON.stringify(data.user)
                    );

                }


                showMessage(
                    "loginMessage",
                    "Login successful! Opening dashboard...",
                    "success"
                );


                setTimeout(function () {

                    window.location.href =
                        "dashboard.html";

                }, 1000);


            } else {

                showMessage(
                    "loginMessage",
                    data.message ||
                    data.error ||
                    "Invalid email or password.",
                    "error"
                );

            }


        } catch (error) {

            console.error(
                "LOGIN ERROR:",
                error
            );


            showMessage(
                "loginMessage",
                "Cannot connect to CareConnect server.",
                "error"
            );


        } finally {

            if (button) {

                button.disabled = false;
                button.textContent = "Sign In";

            }

        }

    });

}


// ============================================
// LOGOUT
// ============================================

if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        async function (event) {

            event.preventDefault();


            try {

                await fetch(
                    getApiBaseUrl() + "/api/logout",
                    {
                        method: "POST",

                        headers:
                            typeof CareConnectConfig !== "undefined" &&
                            CareConnectConfig.getAuthHeaders
                                ? CareConnectConfig.getAuthHeaders()
                                : {}
                    }
                );

            } catch (error) {

                console.warn(
                    "Logout request failed:",
                    error
                );

            }


            localStorage.removeItem(
                "careconnect_token"
            );

            localStorage.removeItem(
                "careconnect_user"
            );

            localStorage.removeItem("token");
            localStorage.removeItem("user");


            window.location.href =
                "login.html";

        }
    );

}

});
