let currentRoom = null;

document.addEventListener("DOMContentLoaded", function () {

    const startButton = document.getElementById("startCallButton");
    const copyButton = document.getElementById("copyRoomButton");
    const leaveButton = document.getElementById("leaveCallButton");

    if (startButton) {
        startButton.addEventListener("click", startVideoCall);
    }

    if (copyButton) {
        copyButton.addEventListener("click", copyRoomName);
    }

    if (leaveButton) {
        leaveButton.addEventListener("click", leaveVideoCall);
    }
});


function startVideoCall() {

    const input = document.getElementById("meetingName");

    if (!input) {
        alert("Meeting input not found.");
        return;
    }

    const meetingName = input.value.trim();

    if (!meetingName) {
        alert("Please enter a meeting name.");
        return;
    }

    if (meetingName.length < 3) {
        alert("Meeting name must contain at least 3 characters.");
        return;
    }

    currentRoom = createRoomName(meetingName);

    const jitsiUrl =
        "https://meet.jit.si/" +
        encodeURIComponent(currentRoom);

    /*
     * Open Jitsi as a real full-screen browser tab.
     */

    const meetingWindow =
        window.open(
            jitsiUrl,
            "_blank"
        );

    if (!meetingWindow) {

        alert(
            "Please allow pop-ups for CareConnect to start the video call."
        );

        return;
    }

    updateStatus("Video Call Opened");
}


function createRoomName(name) {

    const safeName =
        name
            .replace(/[^a-zA-Z0-9-_]/g, "-")
            .replace(/-+/g, "-")
            .replace(/^-|-$/g, "");

    return "CareConnect-" + safeName;
}


async function copyRoomName() {

    if (!currentRoom) {

        alert(
            "Start a video call first."
        );

        return;
    }

    try {

        await navigator.clipboard.writeText(
            currentRoom
        );

        updateStatus(
            "Room Name Copied"
        );

    } catch (error) {

        alert(
            "Room Name: " +
            currentRoom
        );
    }
}


function leaveVideoCall() {

    updateStatus(
        "Call window can be closed from the Jitsi tab."
    );
}


function updateStatus(text) {

    const status =
        document.getElementById(
            "connectionStatus"
        );

    if (status) {
        status.textContent = text;
    }
}