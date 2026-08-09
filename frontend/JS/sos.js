```javascript
// ===============================
// EMERGENCY SOS
// ===============================

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

                window.location.href = "login.html";
                return;
            }

            sosButton.disabled = true;

            sosMessage.textContent =
                "Activating Emergency SOS...";

            if (!navigator.geolocation) {

                sosMessage.textContent =
                    "Geolocation is not supported by your browser.";

                sosButton.disabled = false;
                return;
            }

            navigator.geolocation.getCurrentPosition(

                async function (position) {

                    try {

                        const latitude =
                            position.coords.latitude;

                        const longitude =
                            position.coords.longitude;

                        const response = await fetch(
                            "http://127.0.0.1:5000/api/sos",
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
                                    longitude: longitude

                                })
                            }
                        );

                        const data =
                            await response.json();

                        console.log(
                            "SOS response:",
                            data
                        );

                        if (
                            response.ok &&
                            data.success
                        ) {

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

                    sosMessage.textContent =
                        "Please allow location access.";

                    sosButton.disabled = false;
                }
            );
        }
    );
}
```
