
const API_BASE_URL = "http://127.0.0.1:5000";

async function loadSOSHistory() {

    const container = document.getElementById("historyContainer");
    const token = localStorage.getItem("token");

    if (!token) {
        container.innerHTML = `
            <div class="empty">
                <h3>Login Required</h3>
                <p>Please login to view SOS history.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="loading">
            Loading SOS history...
        </div>
    `;

    try {

        const response = await fetch(
            `${API_BASE_URL}/api/sos/history`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            }
        );

        const data = await response.json();

        if (response.status === 401) {

            localStorage.removeItem("token");

            container.innerHTML = `
                <div class="empty">
                    <h3>Session Expired</h3>
                    <p>Please login again.</p>
                </div>
            `;

            return;
        }

        if (!data.success) {
            throw new Error(data.message || "Failed to load history");
        }

        const events = data.events || [];

        if (events.length === 0) {

            container.innerHTML = `
                <div class="empty">
                    <h3>No SOS History</h3>
                    <p>No emergency SOS alerts found.</p>
                </div>
            `;

            return;
        }

        container.innerHTML = "";

        events.forEach((event, index) => {

            const date = event.created_at
                ? new Date(event.created_at).toLocaleString()
                : "Not available";

            const card = document.createElement("div");

            card.className = "event-card";

            card.innerHTML = `
                <div class="event-header">
                    <h3>Emergency SOS #${events.length - index}</h3>

                    <span class="status">
                        ${event.status || "ACTIVE"}
                    </span>
                </div>

                <div class="event-details">

                    <p>
                        <strong>Message:</strong>
                        ${event.message || "Emergency SOS"}
                    </p>

                    <p>
                        <strong>Date & Time:</strong>
                        ${date}
                    </p>

                    <p>
                        <strong>Latitude:</strong>
                        ${event.latitude ?? "Not available"}
                    </p>

                    <p>
                        <strong>Longitude:</strong>
                        ${event.longitude ?? "Not available"}
                    </p>

                </div>
            `;

            container.appendChild(card);
        });

    } catch (error) {

        console.error("SOS History Error:", error);

        container.innerHTML = `
            <div class="empty">
                <h3>Unable to load SOS history</h3>
                <p>Please make sure the backend is running.</p>
            </div>
        `;
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadSOSHistory
);
```
