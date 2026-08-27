// =====================================================
// USER PROFILE & ACCOUNT MANAGEMENT
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const profileForm = document.getElementById("profileForm");
    const profileName = document.getElementById("profileName");
    const profileEmail = document.getElementById("profileEmail");
    const profilePhone = document.getElementById("profilePhone");
    const profileBloodGroup = document.getElementById("profileBloodGroup");
    const profileEmergencyContact = document.getElementById("profileEmergencyContact");
    const profileEmergencyPhone = document.getElementById("profileEmergencyPhone");
    const profileNewPassword = document.getElementById("profileNewPassword");
    const saveProfileBtn = document.getElementById("saveProfileBtn");

    async function loadProfile() {
        try {
            const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/profile`, {
                headers: CareConnectConfig.getAuthHeaders()
            });
            const data = await res.json();
            if (res.ok && data.success && data.profile) {
                const p = data.profile;
                if (profileName) profileName.value = p.name || "";
                if (profileEmail) profileEmail.value = p.email || "";
                if (profilePhone) profilePhone.value = p.phone || "";
                if (profileBloodGroup) profileBloodGroup.value = p.blood_group || "";
                if (profileEmergencyContact) profileEmergencyContact.value = p.emergency_contact || "";
                if (profileEmergencyPhone) profileEmergencyPhone.value = p.emergency_phone || "";
            }
        } catch (err) {
            console.error("Load profile error:", err);
        }
    }

    if (profileForm) {
        profileForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = profileName ? profileName.value.trim() : "";
            const phone = profilePhone ? profilePhone.value.trim() : "";
            const blood_group = profileBloodGroup ? profileBloodGroup.value : "";
            const emergency_contact = profileEmergencyContact ? profileEmergencyContact.value.trim() : "";
            const emergency_phone = profileEmergencyPhone ? profileEmergencyPhone.value.trim() : "";
            const new_password = profileNewPassword ? profileNewPassword.value : "";

            if (!name) {
                CareConnectConfig.showToast("Name is required.", "error");
                return;
            }

            saveProfileBtn.disabled = true;
            saveProfileBtn.innerHTML = `<span class="spinner"></span> Saving Profile...`;

            try {
                const payload = { name, phone, blood_group, emergency_contact, emergency_phone };
                if (new_password) payload.new_password = new_password;

                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/profile`, {
                    method: "PUT",
                    headers: CareConnectConfig.getAuthHeaders(),
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    CareConnectConfig.showToast("Profile updated successfully!", "success");
                    if (data.profile) {
                        localStorage.setItem("careconnect_user", JSON.stringify(data.profile));
                    }
                    if (profileNewPassword) profileNewPassword.value = "";
                } else {
                    CareConnectConfig.showToast(data.message || "Failed to update profile.", "error");
                }
            } catch (err) {
                console.error("Save profile error:", err);
                CareConnectConfig.showToast("Error updating profile.", "error");
            } finally {
                saveProfileBtn.disabled = false;
                saveProfileBtn.innerHTML = `Save Changes`;
            }
        });
    }

    loadProfile();
});
