document.addEventListener("DOMContentLoaded", function () {

    console.log("AMBULANCE JS LOADED");

    var locationButton =
        document.getElementById("locationButton");

    var refreshButton =
        document.getElementById("refreshLocationButton");

    var openMapButton =
        document.getElementById("openMapButton");

    var directionsButton =
        document.getElementById("directionsButton");

    var retryButton =
        document.getElementById("retryButton");

    var findAmbulanceButton =
        document.getElementById("findAmbulanceButton");

    var emergencyAmbulanceButton =
        document.getElementById("emergencyAmbulanceButton");


    var latitude = null;
    var longitude = null;


    /* =====================================================
       GET CURRENT LOCATION
       ===================================================== */

    function getLocation() {

        console.log("GET LOCATION");

        if (!navigator.geolocation) {

            alert(
                "Your browser does not support location."
            );

            return;
        }


        if (locationButton) {

            locationButton.disabled = true;

            locationButton.innerText =
                "📍 Detecting Location...";

        }


        var status =
            document.getElementById("locationStatus");


        if (status) {

            status.innerText =
                "📍 Detecting Location...";

        }


        navigator.geolocation.getCurrentPosition(

            function (position) {

                latitude =
                    position.coords.latitude;

                longitude =
                    position.coords.longitude;


                console.log(
                    "LATITUDE:",
                    latitude
                );

                console.log(
                    "LONGITUDE:",
                    longitude
                );


                if (locationButton) {

                    locationButton.disabled = false;

                    locationButton.innerText =
                        "🔄 Update My Location";

                }


                if (status) {

                    status.innerText =
                        "📍 Location Detected";

                }


                var message =
                    document.getElementById(
                        "locationMessage"
                    );


                if (message) {

                    message.innerText =
                        "✅ Your current location has been detected successfully.";

                }


                var mapSection =
                    document.getElementById(
                        "mapSection"
                    );


                if (mapSection) {

                    mapSection.style.display =
                        "block";

                }


                var results =
                    document.getElementById(
                        "ambulanceResults"
                    );


                if (results) {

                    results.style.display =
                        "block";

                }


                /* MAP */

                var map =
                    document.getElementById(
                        "ambulanceMap"
                    );


                if (map) {

                    map.src =
                        "https://www.google.com/maps?q=ambulance+near+" +
                        latitude +
                        "," +
                        longitude +
                        "&z=14&output=embed";

                }


                /* ADDRESS */

                var address =
                    document.getElementById(
                        "mapAddress"
                    );


                if (address) {

                    address.innerText =
                        "📍 Your current location: " +
                        latitude.toFixed(6) +
                        ", " +
                        longitude.toFixed(6);

                }


                /* SHOW FIND BUTTON */

                showFindAmbulanceButton();

            },


            function (error) {

                console.error(
                    "LOCATION ERROR:",
                    error
                );


                if (locationButton) {

                    locationButton.disabled =
                        false;

                    locationButton.innerText =
                        "📍 Use My Current Location";

                }


                if (status) {

                    status.innerText =
                        "📍 Location Not Detected";

                }


                if (error.code === 1) {

                    alert(
                        "Location permission denied. Please allow location access in your browser."
                    );

                }

                else if (error.code === 2) {

                    alert(
                        "Location unavailable. Please turn ON Windows Location."
                    );

                }

                else if (error.code === 3) {

                    alert(
                        "Location request timed out. Please try again."
                    );

                }

                else {

                    alert(
                        "Unable to detect your location."
                    );

                }

            },


            {

                enableHighAccuracy: true,

                timeout: 30000,

                maximumAge: 0

            }

        );

    }



    /* =====================================================
       SHOW FIND AMBULANCE BUTTON
       ===================================================== */

    function showFindAmbulanceButton() {

        var list =
            document.getElementById(
                "ambulanceList"
            );


        if (!list) {

            return;

        }


        list.innerHTML = `

            <div class="ambulance-result-card">

                <h3>
                    🚑 Nearby Ambulance Services
                </h3>

                <p>
                    Your location has been detected.
                    Click below to search for ambulance
                    services near you.
                </p>

                <div class="ambulance-result-actions">

                    <button
                        type="button"
                        id="findAmbulanceNow"
                        class="btn btn-primary">

                        🚑 Find Ambulances Near Me

                    </button>

                </div>

            </div>

        `;


        var button =
            document.getElementById(
                "findAmbulanceNow"
            );


        if (button) {

            button.addEventListener(
                "click",
                openAmbulanceSearch
            );

        }

    }



    /* =====================================================
       FIND NEARBY AMBULANCES
       ===================================================== */

    function openAmbulanceSearch() {

        console.log(
            "FIND AMBULANCES CLICKED"
        );


        if (
            latitude === null ||
            longitude === null
        ) {

            alert(
                "Please select your current location first."
            );

            return;

        }


        var url =
            "https://www.google.com/maps/search/?api=1" +
            "&query=" +
            encodeURIComponent(
                "ambulance near " +
                latitude +
                "," +
                longitude
            );


        window.open(
            url,
            "_blank"
        );


        showAmbulanceDirectionCard();

    }



    /* =====================================================
       AMBULANCE DIRECTION CARD
       ===================================================== */

    function showAmbulanceDirectionCard() {

        var list =
            document.getElementById(
                "ambulanceList"
            );


        if (!list) {

            return;

        }


        list.innerHTML = `

            <div class="ambulance-result-card">

                <h3>
                    🚑 Ambulance Search
                </h3>

                <p>
                    Google Maps has opened nearby ambulance
                    services based on your current location.
                </p>

                <p>
                    Select the ambulance service you want
                    to visit, then use Google Maps directions.
                </p>

                <div class="ambulance-result-actions">

                    <button
                        type="button"
                        id="startDirectionButton"
                        class="btn btn-primary">

                        🧭 Start Direction

                    </button>

                    <button
                        type="button"
                        id="searchAgainButton"
                        class="btn btn-secondary">

                        🔄 Search Again

                    </button>

                </div>

            </div>

        `;


        var directionButton =
            document.getElementById(
                "startDirectionButton"
            );


        if (directionButton) {

            directionButton.addEventListener(
                "click",
                startDirection
            );

        }


        var searchAgainButton =
            document.getElementById(
                "searchAgainButton"
            );


        if (searchAgainButton) {

            searchAgainButton.addEventListener(
                "click",
                openAmbulanceSearch
            );

        }

    }



    /* =====================================================
       START DIRECTIONS
       ===================================================== */

    function startDirection() {

        console.log(
            "START DIRECTION"
        );


        if (
            latitude === null ||
            longitude === null
        ) {

            alert(
                "Please detect your current location first."
            );

            return;

        }


        var destination =
            prompt(
                "Enter the ambulance hospital/service name selected in Google Maps:"
            );


        if (
            !destination ||
            destination.trim() === ""
        ) {

            alert(
                "Please enter the ambulance or hospital name."
            );

            return;

        }


        var url =
            "https://www.google.com/maps/dir/?api=1" +
            "&origin=" +
            encodeURIComponent(
                latitude + "," + longitude
            ) +
            "&destination=" +
            encodeURIComponent(
                destination
            ) +
            "&travelmode=driving";


        window.open(
            url,
            "_blank"
        );

    }



    /* =====================================================
       OPEN FULL MAP
       ===================================================== */

    function openFullMap() {

        if (
            latitude === null ||
            longitude === null
        ) {

            alert(
                "Please select your current location first."
            );

            return;

        }


        var url =
            "https://www.google.com/maps/search/?api=1" +
            "&query=" +
            encodeURIComponent(
                "ambulance near " +
                latitude +
                "," +
                longitude
            );


        window.open(
            url,
            "_blank"
        );

    }



    /* =====================================================
       DIRECTIONS BUTTON
       ===================================================== */

    function directions() {

        if (
            latitude === null ||
            longitude === null
        ) {

            alert(
                "Please detect your current location first."
            );

            return;

        }


        var destination =
            prompt(
                "Enter ambulance or hospital name:"
            );


        if (
            !destination ||
            destination.trim() === ""
        ) {

            return;

        }


        var url =
            "https://www.google.com/maps/dir/?api=1" +
            "&origin=" +
            encodeURIComponent(
                latitude + "," + longitude
            ) +
            "&destination=" +
            encodeURIComponent(
                destination
            ) +
            "&travelmode=driving";


        window.open(
            url,
            "_blank"
        );

    }



    /* =====================================================
       LOCATION BUTTON
       ===================================================== */

    if (locationButton) {

        locationButton.addEventListener(
            "click",
            getLocation
        );

    }



    /* =====================================================
       REFRESH LOCATION
       ===================================================== */

    if (refreshButton) {

        refreshButton.addEventListener(
            "click",
            getLocation
        );

    }



    /* =====================================================
       OPEN FULL MAP BUTTON
       ===================================================== */

    if (openMapButton) {

        openMapButton.addEventListener(
            "click",
            openFullMap
        );

    }



    /* =====================================================
       DIRECTIONS BUTTON
       ===================================================== */

    if (directionsButton) {

        directionsButton.addEventListener(
            "click",
            directions
        );

    }



    /* =====================================================
       INITIAL FIND BUTTON
       ===================================================== */

    if (findAmbulanceButton) {

        findAmbulanceButton.addEventListener(
            "click",
            function () {

                if (
                    latitude === null ||
                    longitude === null
                ) {

                    getLocation();

                }

                else {

                    openAmbulanceSearch();

                }

            }
        );

    }



    /* =====================================================
       EMERGENCY FIND AMBULANCE
       ===================================================== */

    if (emergencyAmbulanceButton) {

        emergencyAmbulanceButton.addEventListener(
            "click",
            function () {

                if (
                    latitude === null ||
                    longitude === null
                ) {

                    alert(
                        "First select your current location."
                    );

                    getLocation();

                    return;

                }


                openAmbulanceSearch();

            }
        );

    }



    /* =====================================================
       RETRY
       ===================================================== */

    if (retryButton) {

        retryButton.addEventListener(
            "click",
            getLocation
        );

    }


});