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
        const data = await res.json();

        const historyList = document.getElementById("historyList");
        historyList.innerHTML = "";

        data.forEach(item => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerText = item.original_query;
            div.onclick = () => loadResearch(item.research_id);
            historyList.appendChild(div);
        });
    } catch (err) {
        console.error("Error loading history:", err);
    }
}

async function loadResearch(id) {
    try {
        currentResearchId = id;

        const res = await fetch(`/api/research/${id}/`);
        const data = await res.json();

        const chatContainer = document.getElementById("chatMessages");
        chatContainer.innerHTML = `<div class="message assistant">${data.report}</div>`;
        chatContainer.scrollTop = chatContainer.scrollHeight;

        document.getElementById("detailsContent").innerHTML = `
            <p><strong>Summary:</strong> ${data.summary}</p>
            <p><strong>Reasoning:</strong> <pre>${JSON.stringify(data.reasoning, null, 2)}</pre></p>
            <p><strong>Sources:</strong> ${data.sources.join(", ")}</p>
            <p><strong>Cost:</strong> $${data.cost}</p>
            <p><strong>Tokens:</strong> ${data.token_usage.input_tokens} / ${data.token_usage.output_tokens}</p>
            <p><strong>Trace ID:</strong> ${data.trace_id}</p>
        `;
    } catch (err) {
        console.error("Error loading research:", err);
    }
}

document.getElementById("newChatBtn").onclick = () => {
    currentResearchId = null;
    document.getElementById("chatMessages").innerHTML = "";
    document.getElementById("detailsContent").innerHTML = "New research started";
};

document.getElementById("chatForm").onsubmit = async (e) => {
    e.preventDefault();

    const query = document.getElementById("queryInput").value.trim();
    if (!query) return;

    const files = document.getElementById("fileInput").files;
    const formData = new FormData();
    formData.append("query", query);
    for (let f of files) formData.append("files", f);

    let url = "/api/research/start/";
    if (currentResearchId) {
        url = `/api/research/${currentResearchId}/continue/`;
    }

    try {
        const res = await fetch(url, {
            method: "POST",
            body: formData,
            headers: { "X-CSRFToken": getCSRFToken() }
        });

        if (!res.ok) {
            const errorData = await res.json();
            alert(errorData.error || "Failed to submit query");
            return;
        }

        const data = await res.json();
        currentResearchId = data.parent_session_id;

        const chatContainer = document.getElementById("chatMessages");
        chatContainer.innerHTML += `
            <div class="message user">${query}</div>
            <div class="message assistant">${data.report}</div>
        `;
        chatContainer.scrollTop = chatContainer.scrollHeight;

        document.getElementById("detailsContent").innerHTML = `
            <p><strong>Summary:</strong> ${data.summary}</p>
            <p><strong>Reasoning:</strong> <pre>${JSON.stringify(data.reasoning, null, 2)}</pre></p>
            <p><strong>Sources:</strong> ${data.sources.join(", ")}</p>
            <p><strong>Cost:</strong> $${data.cost}</p>
            <p><strong>Tokens:</strong> ${data.token_usage.input_tokens} / ${data.token_usage.output_tokens}</p>
            <p><strong>Trace ID:</strong> ${data.trace_id}</p>
        `;

        loadHistory();
        document.getElementById("queryInput").value = "";
        document.getElementById("fileInput").value = "";
    } catch (err) {
        console.error("Error submitting query:", err);
        alert("Error submitting query. Check console for details.");
    }
};

window.onload = loadHistory;
