let currentResearchId = null;
function getCSRFToken() {
    let cookieValue = null;
    const name = "csrftoken";
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
async function loadHistory() {
    try {
        const res = await fetch("/api/research/history/");
        if (!res.ok) return;

        const data = await res.json();
        const historyList = document.getElementById("historyList");
        historyList.innerHTML = "";

        data.forEach(item => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.textContent = item.original_query;
            div.onclick = () => loadResearch(item.research_id);
            historyList.appendChild(div);
        });
    } catch (err) {
        console.error("History load failed:", err);
    }
}

async function loadResearch(id) {
    try {
        currentResearchId = id;

        const res = await fetch(`/api/research/${id}/`);
        if (!res.ok) return;

        const data = await res.json();
        const chat = document.getElementById("chatMessages");
        chat.innerHTML = `<div class="message assistant">${data.report}</div>`;
        chat.scrollTop = chat.scrollHeight;
        document.getElementById("detailsContent").innerHTML = `
            <p><strong>Summary:</strong></p>
            <p>${data.summary}</p>

            <p><strong>Reasoning:</strong></p>
            <pre>${JSON.stringify(data.reasoning, null, 2)}</pre>

            <p><strong>Sources:</strong></p>
            <p>${(data.sources || []).join(", ")}</p>

            <p><strong>Cost:</strong> $${data.cost}</p>
            <p><strong>Tokens:</strong> 
                ${data.token_usage.input_tokens} / ${data.token_usage.output_tokens}
            </p>
            <p><strong>Trace ID:</strong> ${data.trace_id}</p>
        `;
    } catch (err) {
        console.error("Load research failed:", err);
    }
}

document.getElementById("newChatBtn").onclick = () => {
    currentResearchId = null;
    document.getElementById("chatMessages").innerHTML = "";
    document.getElementById("detailsContent").innerHTML =
        "<p>New research started</p>";
};

document.getElementById("chatForm").onsubmit = async (e) => {
    e.preventDefault();

    const queryInput = document.getElementById("queryInput");
    const fileInput = document.getElementById("fileInput");
    const query = queryInput.value.trim();

    if (!query) return;

    const formData = new FormData();
    formData.append("query", query);
    for (let f of fileInput.files) {
        formData.append("files", f);
    }
    let url = "/api/research/";
    if (currentResearchId) {
        url = `/api/research/${currentResearchId}/continue/`;
    }

    try {
        const res = await fetch(url, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": getCSRFToken()
            }
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.error || "Request failed");
            return;
        }

        const data = await res.json();
        currentResearchId = data.parent_session_id;

        const chat = document.getElementById("chatMessages");
        chat.innerHTML += `
            <div class="message user">${query}</div>
            <div class="message assistant">${data.report}</div>
        `;
        chat.scrollTop = chat.scrollHeight;

        queryInput.value = "";
        fileInput.value = "";

        loadHistory();
    } catch (err) {
        console.error("Submit failed:", err);
        alert("Server error. Check console.");
    }
};

window.onload = loadHistory;
