// =====================================================
// CARECONNECT - CENTRALIZED CLIENT CONFIGURATION
// =====================================================

const CareConnectConfig = {
    // Dynamic API Base URL resolver:
    // If served directly by backend or production domain, use origin
    // Fallback to http://127.0.0.1:5000 for local frontend development (e.g. Live Server)
    getApiBaseUrl: function () {
        if (typeof window !== "undefined" && window.location && window.location.protocol.startsWith("http")) {
            // If served from Flask port 5000 or custom production host (e.g. Render / Vercel with reverse proxy)
            if (window.location.port === "5000" || (window.location.port === "" && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost")) {
                return window.location.origin;
            }
        }
        return "http://127.0.0.1:5000";
    },

    // Standard Auth Header Helper
    getAuthHeaders: function (isJson = true) {
        const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
        const headers = {};
        if (isJson) {
            headers["Content-Type"] = "application/json";
        }
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    },

    // Get current logged-in user
    getUser: function () {
        try {
            const raw = localStorage.getItem("careconnect_user") || localStorage.getItem("user");
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    },

    // Save session info
    setSession: function (token, user) {
        if (token) {
            localStorage.setItem("careconnect_token", token);
            localStorage.setItem("token", token);
        }
        if (user) {
            const str = typeof user === "string" ? user : JSON.stringify(user);
            localStorage.setItem("careconnect_user", str);
            localStorage.setItem("user", str);
        }
    },

    // Clear session info
    clearSession: function () {
        localStorage.removeItem("careconnect_token");
        localStorage.removeItem("careconnect_user");
        localStorage.removeItem("token");
        localStorage.removeItem("user");
    },

    // Session Management Helper
    checkAuthOrRedirect: function () {
        const token = localStorage.getItem("careconnect_token") || localStorage.getItem("token");
        if (!token) {
            window.location.href = "login.html";
            return false;
        }
        return true;
    },

    // Toast Notification System
    showToast: function (message, type = "info") {
        let container = document.getElementById("toastContainer");
        if (!container) {
            container = document.createElement("div");
            container.id = "toastContainer";
            document.body.appendChild(container);
        }

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        
        let icon = "ℹ️";
        if (type === "success") icon = "✅";
        if (type === "error") icon = "⚠️";
        
        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(100%)";
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
};

window.CareConnectConfig = CareConnectConfig;
