// =====================================================
// CARECONNECT - AUTHENTICATION LOGIC (auth.js)
// =====================================================

document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.getElementById("registerForm");
    const loginForm = document.getElementById("loginForm");
    const logoutButton = document.getElementById("logoutButton");

    // ============================================
    // API URL RESOLVER
    // ============================================
    function getApiBaseUrl() {
        if (window.CareConnectConfig && typeof window.CareConnectConfig.getApiBaseUrl === "function") {
            return window.CareConnectConfig.getApiBaseUrl();
        }
        if (typeof window !== "undefined" && window.location && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") {
            return window.location.origin;
        }
        return "http://127.0.0.1:5000";
    }

    // ============================================
    // UI MESSAGE DISPLAY HELPER
    // ============================================
    function showMessage(elementId, message, type) {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.textContent = message;
        element.style.marginTop = "15px";
        element.style.padding = "12px";
        element.style.borderRadius = "8px";
        element.style.textAlign = "center";
        element.style.fontSize = "14px";
        element.style.fontWeight = "500";

        if (type === "success") {
            element.style.background = "#dcfce7";
            element.style.color = "#166534";
            element.style.border = "1px solid #bbf7d0";
        } else {
            element.style.background = "#fee2e2";
            element.style.color = "#991b1b";
            element.style.border = "1px solid #fecaca";
        }
    }

    // ============================================
    // REGISTRATION HANDLER
    // ============================================
    if (registerForm) {
        registerForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const nameElement = document.getElementById("name");
            const emailElement = document.getElementById("email");
            const passwordElement = document.getElementById("password");
            const confirmPasswordElement = document.getElementById("confirmPassword");

            if (!nameElement || !emailElement || !passwordElement || !confirmPasswordElement) {
                showMessage("registerMessage", "Registration form fields are missing.", "error");
                return;
            }

            const name = nameElement.value.trim();
            const email = emailElement.value.trim();
            const password = passwordElement.value;
            const confirmPassword = confirmPasswordElement.value;
            const submitBtn = registerForm.querySelector("button[type='submit']");

            // Form validation
            if (!name) {
                showMessage("registerMessage", "Please enter your full name.", "error");
                return;
            }

            if (!email) {
                showMessage("registerMessage", "Please enter your email address.", "error");
                return;
            }

            if (password.length < 6) {
                showMessage("registerMessage", "Password must contain at least 6 characters.", "error");
                return;
            }

            if (password !== confirmPassword) {
                showMessage("registerMessage", "Passwords do not match.", "error");
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "Creating Account...";
            }

            try {
                const apiUrl = `${getApiBaseUrl()}/api/register`;
                console.log("REGISTER API Request:", apiUrl);

                const response = await fetch(apiUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        name: name,
                        email: email,
                        password: password
                    })
                });

                const data = await response.json();
                console.log("REGISTER Response:", response.status, data);

                if (response.ok && data.success) {
                    showMessage(
                        "registerMessage",
                        "Account created successfully! Redirecting to login...",
                        "success"
                    );

                    if (window.CareConnectConfig && typeof window.CareConnectConfig.setSession === "function") {
                        window.CareConnectConfig.setSession(data.token, data.user);
                    } else {
                        if (data.token) {
                            localStorage.setItem("careconnect_token", data.token);
                            localStorage.setItem("token", data.token);
                        }
                        if (data.user) {
                            localStorage.setItem("careconnect_user", JSON.stringify(data.user));
                            localStorage.setItem("user", JSON.stringify(data.user));
                        }
                    }

                    setTimeout(function () {
                        window.location.href = "login.html";
                    }, 1200);
                } else {
                    showMessage(
                        "registerMessage",
                        data.message || data.error || "Unable to create account.",
                        "error"
                    );
                }
            } catch (error) {
                console.error("REGISTER ERROR:", error);
                showMessage(
                    "registerMessage",
                    "Cannot connect to CareConnect server. Please check that the backend is running.",
                    "error"
                );
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Create Account";
                }
            }
        });
    }

    // ============================================
    // LOGIN HANDLER
    // ============================================
    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const emailElement = document.getElementById("loginEmail") || document.getElementById("email");
            const passwordElement = document.getElementById("loginPassword") || document.getElementById("password");

            if (!emailElement || !passwordElement) {
                showMessage("loginMessage", "Login form fields are missing.", "error");
                return;
            }

            const email = emailElement.value.trim();
            const password = passwordElement.value;
            const submitBtn = loginForm.querySelector("button[type='submit']");

            if (!email || !password) {
                showMessage("loginMessage", "Please enter your email and password.", "error");
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "Signing In...";
            }

            try {
                const apiUrl = `${getApiBaseUrl()}/api/login`;
                console.log("LOGIN API Request:", apiUrl);

                const response = await fetch(apiUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });

                const data = await response.json();
                console.log("LOGIN Response:", response.status, data);

                if (response.ok && data.success) {
                    if (window.CareConnectConfig && typeof window.CareConnectConfig.setSession === "function") {
                        window.CareConnectConfig.setSession(data.token, data.user);
                    } else {
                        if (data.token) {
                            localStorage.setItem("careconnect_token", data.token);
                            localStorage.setItem("token", data.token);
                        }
                        if (data.user) {
                            localStorage.setItem("careconnect_user", JSON.stringify(data.user));
                            localStorage.setItem("user", JSON.stringify(data.user));
                        }
                    }

                    showMessage(
                        "loginMessage",
                        "Login successful! Opening dashboard...",
                        "success"
                    );

                    setTimeout(function () {
                        window.location.href = "dashboard.html";
                    }, 800);
                } else {
                    showMessage(
                        "loginMessage",
                        data.message || data.error || "Invalid email or password.",
                        "error"
                    );
                }
            } catch (error) {
                console.error("LOGIN ERROR:", error);
                showMessage(
                    "loginMessage",
                    "Cannot connect to CareConnect server. Please check that the backend is running.",
                    "error"
                );
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Sign In";
                }
            }
        });
    }

    // ============================================
    // LOGOUT HANDLER
    // ============================================
    if (logoutButton) {
        logoutButton.addEventListener("click", async function (event) {
            event.preventDefault();

            try {
                const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
                const headers = { "Content-Type": "application/json" };
                if (token) {
                    headers["Authorization"] = "Bearer " + token;
                }

                await fetch(`${getApiBaseUrl()}/api/logout`, {
                    method: "POST",
                    headers: headers
                });
            } catch (error) {
                console.warn("Logout request failed:", error);
            }

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
});
