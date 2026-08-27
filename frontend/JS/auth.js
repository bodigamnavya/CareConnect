// =====================================================
// AUTHENTICATION LOGIC (Login, Register, Logout)
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("registerForm");
    const loginForm = document.getElementById("loginForm");
    const logoutButtons = document.querySelectorAll(".logout-btn, #logoutButton");

    // Register Submission
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = registerForm.querySelector("button[type='submit']");
            const name = document.getElementById("name").value.trim();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirmPassword").value;

            if (password !== confirmPassword) {
                CareConnectConfig.showToast("Passwords do not match.", "error");
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner"></span> Creating Account...`;

            try {
                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, email, password })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    localStorage.setItem("careconnect_token", data.token);
                    localStorage.setItem("careconnect_user", JSON.stringify(data.user));
                    CareConnectConfig.showToast("Registration successful! Opening dashboard...", "success");
                    setTimeout(() => { window.location.href = "dashboard.html"; }, 1000);
                } else {
                    CareConnectConfig.showToast(data.message || "Registration failed.", "error");
                }
            } catch (err) {
                console.error("Register Error:", err);
                CareConnectConfig.showToast("Unable to connect to backend server.", "error");
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `Create Account`;
            }
        });
    }

    // Login Submission
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = loginForm.querySelector("button[type='submit']");
            const email = document.getElementById("loginEmail").value.trim();
            const password = document.getElementById("loginPassword").value;

            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner"></span> Signing In...`;

            try {
                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    localStorage.setItem("careconnect_token", data.token);
                    localStorage.setItem("careconnect_user", JSON.stringify(data.user));
                    CareConnectConfig.showToast("Login successful!", "success");
                    setTimeout(() => { window.location.href = "dashboard.html"; }, 800);
                } else {
                    CareConnectConfig.showToast(data.message || "Invalid credentials.", "error");
                }
            } catch (err) {
                console.error("Login Error:", err);
                CareConnectConfig.showToast("Unable to connect to server.", "error");
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `Sign In`;
            }
        });
    }

    // Logout Handlers
    logoutButtons.forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/logout`, {
                    method: "POST",
                    headers: CareConnectConfig.getAuthHeaders()
                });
            } catch (ignore) {}
            localStorage.removeItem("careconnect_token");
            localStorage.removeItem("careconnect_user");
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.location.href = "login.html";
        });
    });
});
