// =====================================================
// AI HEALTH ASSISTANT CHAT CLIENT
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    if (!CareConnectConfig.checkAuthOrRedirect()) return;

    const chatMessages = document.getElementById("chatMessages");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const emergencyAlertBanner = document.getElementById("emergencyAlertBanner");

    let currentConversationId = sessionStorage.getItem("active_conversation_id") || "";

    // Check for prefilled context from scan result
    const prefillPrompt = sessionStorage.getItem("ai_prompt_context");
    if (prefillPrompt && chatInput) {
        chatInput.value = prefillPrompt;
        sessionStorage.removeItem("ai_prompt_context");
    }

    function appendMessage(sender, text, isEmergency = false) {
        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${sender}`;

        // Format newlines into paragraphs
        const formatted = text.split("\n\n").map(para => {
            // Replace markdown bold
            let clean = para.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            clean = clean.replace(/\*(.*?)\*/g, '<em>$1</em>');
            clean = clean.replace(/\n/g, '<br>');
            return `<p>${clean}</p>`;
        }).join("");

        bubble.innerHTML = formatted;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (isEmergency && emergencyAlertBanner) {
            emergencyAlertBanner.style.display = "flex";
        }
    }

    if (chatForm && chatInput) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            // Render user bubble
            appendMessage("user", message);
            chatInput.value = "";
            sendBtn.disabled = true;

            // Render typing indicator
            const typingBubble = document.createElement("div");
            typingBubble.className = "message-bubble assistant";
            typingBubble.id = "typingIndicator";
            typingBubble.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; margin-right: 8px;"></span> AI Assistant is thinking...`;
            chatMessages.appendChild(typingBubble);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const res = await fetch(`${CareConnectConfig.getApiBaseUrl()}/api/ai/chat`, {
                    method: "POST",
                    headers: CareConnectConfig.getAuthHeaders(),
                    body: JSON.stringify({
                        message: message,
                        conversation_id: currentConversationId
                    })
                });

                const data = await res.json();
                const indicator = document.getElementById("typingIndicator");
                if (indicator) indicator.remove();

                if (res.ok && data.success) {
                    if (data.conversation_id) {
                        currentConversationId = data.conversation_id;
                        sessionStorage.setItem("active_conversation_id", currentConversationId);
                    }
                    appendMessage("assistant", data.response, data.is_emergency);
                } else {
                    appendMessage("assistant", "I am currently unable to process your request. Please try again in a moment.");
                    CareConnectConfig.showToast(data.message || "Error processing message.", "error");
                }
            } catch (err) {
                console.error("Chat error:", err);
                const indicator = document.getElementById("typingIndicator");
                if (indicator) indicator.remove();
                appendMessage("assistant", "Unable to reach the CareConnect AI service. Please check your network connection.");
            } finally {
                sendBtn.disabled = false;
                chatInput.focus();
            }
        });
    }
});
