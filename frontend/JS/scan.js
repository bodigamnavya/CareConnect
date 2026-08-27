// =====================================================
// MEDICAL IMAGE SCANNER (Upload, Camera & Execution)
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const dropzone = document.getElementById("scanDropzone");
    const fileInput = document.getElementById("imageFileInput");
    const previewContainer = document.getElementById("previewContainer");
    const previewImage = document.getElementById("previewImage");
    const removePreviewBtn = document.getElementById("removePreviewBtn");
    const scanTypeSelect = document.getElementById("scanType");
    const startScanBtn = document.getElementById("startScanBtn");
    const openCameraBtn = document.getElementById("openCameraBtn");
    const cameraModal = document.getElementById("cameraModal");
    const cameraVideo = document.getElementById("cameraVideo");
    const capturePhotoBtn = document.getElementById("capturePhotoBtn");
    const closeCameraBtn = document.getElementById("closeCameraBtn");

    let currentFile = null;
    let cameraStream = null;

    // Trigger file chooser on dropzone click
    if (dropzone && fileInput) {
        dropzone.addEventListener("click", () => fileInput.click());

        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("dragover");
        });

        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                handleSelectedFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files && fileInput.files.length > 0) {
                handleSelectedFile(fileInput.files[0]);
            }
        });
    }

    function handleSelectedFile(file) {
        if (!file.type.startsWith("image/")) {
            CareConnectConfig.showToast("Please select a valid image file (PNG, JPG, JPEG, WEBP).", "error");
            return;
        }
        currentFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            dropzone.style.display = "none";
            previewContainer.style.display = "block";
            startScanBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    if (removePreviewBtn) {
        removePreviewBtn.addEventListener("click", () => {
            currentFile = null;
            if (fileInput) fileInput.value = "";
            previewImage.src = "";
            previewContainer.style.display = "none";
            dropzone.style.display = "flex";
            startScanBtn.disabled = true;
        });
    }

    // Camera Integration
    if (openCameraBtn && cameraModal && cameraVideo) {
        openCameraBtn.addEventListener("click", async () => {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                CareConnectConfig.showToast("Camera access is not supported by your browser.", "error");
                return;
            }
            try {
                cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                cameraVideo.srcObject = cameraStream;
                cameraModal.style.display = "flex";
            } catch (err) {
                console.error("Camera access error:", err);
                CareConnectConfig.showToast("Unable to access device camera. Please check permissions.", "error");
            }
        });

        if (capturePhotoBtn) {
            capturePhotoBtn.addEventListener("click", () => {
                const canvas = document.createElement("canvas");
                canvas.width = cameraVideo.videoWidth || 640;
                canvas.height = cameraVideo.videoHeight || 480;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
                
                canvas.toBlob((blob) => {
                    const capturedFile = new File([blob], "camera_scan.jpg", { type: "image/jpeg" });
                    handleSelectedFile(capturedFile);
                    closeCamera();
                }, "image/jpeg", 0.95);
            });
        }

        if (closeCameraBtn) {
            closeCameraBtn.addEventListener("click", closeCamera);
        }
    }

    function closeCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(t => t.stop());
            cameraStream = null;
        }
        if (cameraModal) cameraModal.style.display = "none";
    }

    // Scan Execution
    if (startScanBtn) {
        startScanBtn.addEventListener("click", async () => {
            if (!currentFile) {
                CareConnectConfig.showToast("Please choose or capture a medical image first.", "error");
                return;
            }

            const scanType = scanTypeSelect ? scanTypeSelect.value : "General Medical Scan";
            const formData = new FormData();
            formData.append("image", currentFile);
            formData.append("scan_type", scanType);

            startScanBtn.disabled = true;
            startScanBtn.innerHTML = `<span class="spinner"></span> Analyzing Image with AI...`;

            try {
                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/scan`, {
                    method: "POST",
                    headers: CareConnectConfig.getAuthHeaders(false),
                    body: formData
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    CareConnectConfig.showToast("Scan completed successfully!", "success");
                    sessionStorage.setItem("latest_scan_result", JSON.stringify(data.scan));
                    setTimeout(() => {
                        window.location.href = `scan-result.html?id=${data.scan_id}`;
                    }, 800);
                } else {
                    CareConnectConfig.showToast(data.message || "Medical scan failed.", "error");
                }
            } catch (err) {
                console.error("Scan submission error:", err);
                CareConnectConfig.showToast("Error connecting to AI analysis server.", "error");
            } finally {
                startScanBtn.disabled = false;
                startScanBtn.innerHTML = `<span>🚀</span> Start AI Scan`;
            }
        });
    }
});
