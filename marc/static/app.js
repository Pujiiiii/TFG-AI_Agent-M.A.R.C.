// ELEMENTS DOM PRINCIPALS
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const statusSearxng = document.getElementById("status-searxng");
const btnRefresh = document.getElementById("btn-refresh");
const btnNewSession = document.getElementById("btn-new-session");
const sessionSelect = document.getElementById("session-select");
const currentSessionLabel = document.getElementById("current-session-label");

// ELEMENTS MODAL ACCIONS (HITL)
const actionModal = document.getElementById("diff-modal");
const modalSummary = document.getElementById("modal-summary");
const actionDetails = document.getElementById("action-details");
const modalCloseBtn = document.getElementById("modal-close-btn");
const modalApproveBtn = document.getElementById("modal-approve-btn");
const modalRejectBtn = document.getElementById("modal-reject-btn");

// ESTAT GLOBAL
let currentSession = "sessio_per_defecte";
let currentActiveAction = null;

// CONFIGURACIÓ DE MARKED & HIGHLIGHT.JS
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  breaks: true
});

// CONSULTAR ESTAT DEL SISTEMA I SESSIONS
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/system-status");
    if (!res.ok) return;
    const data = await res.json();

    if (data.services && data.services.searxng) {
      statusSearxng.textContent = data.services.searxng;
      statusSearxng.className = `badge ${data.services.searxng === "OFFLINE" ? "offline" : ""}`;
    }

    const existing = Array.from(sessionSelect.options).map(o => o.value);
    if (data.sessions) {
      data.sessions.forEach(s => {
        if (!existing.includes(s)) {
          const opt = document.createElement("option");
          opt.value = s;
          opt.textContent = s;
          sessionSelect.appendChild(opt);
        }
      });
    }
  } catch (err) {
    console.error("Error carregant estat del sistema:", err);
  }
}

// INSERCIÓ DE MISSATGES AL XAT
function appendMessage(sender, rawText, isUser = false) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${isUser ? "user" : "assistant"}`;
  
  const authorDiv = document.createElement("div");
  authorDiv.className = "msg-author";
  authorDiv.textContent = sender;

  const bodyDiv = document.createElement("div");
  bodyDiv.className = "msg-body";

  if (isUser) {
    bodyDiv.textContent = rawText;
  } else {
    const textToRender = (rawText && rawText.trim()) ? rawText : "*(Sense resposta de text)*";
    bodyDiv.innerHTML = marked.parse(textToRender);
  }

  msgDiv.appendChild(authorDiv);
  msgDiv.appendChild(bodyDiv);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return bodyDiv;
}

// VISUALITZACIÓ DEL MODAL D'APROVACIÓ D'ACCIONS (HITL)
function obrirModalAccio(pendingAction) {
  currentActiveAction = pendingAction;
  modalSummary.textContent = pendingAction.summary || "Revisió d'acció proposada";
  actionModal.classList.remove("hidden");

  actionDetails.innerHTML = "";

  const tipus = pendingAction.type || "acció";
  const dades = pendingAction.data || {};

  const card = document.createElement("div");
  card.className = "action-card";

  let htmlDetalls = `<div class="action-card-header">TIPUS D'ACCIÓ: <span class="action-type-badge">${tipus.toUpperCase()}</span></div>`;
  htmlDetalls += `<div class="action-card-body">`;

  // Renderitzem dinàmicament els camps de l'acció
  const claus = Object.keys(dades);
  if (claus.length > 0) {
    claus.forEach(k => {
      const valor = typeof dades[k] === "object" ? JSON.stringify(dades[k], null, 2) : dades[k];
      htmlDetalls += `
        <div class="action-field">
          <div class="action-field-name">${k.toUpperCase().replace(/_/g, " ")}:</div>
          <div class="action-field-val">${valor}</div>
        </div>
      `;
    });
  } else {
    htmlDetalls += `<p class="action-field-val">${pendingAction.summary || "Cap informació addicional."}</p>`;
  }

  htmlDetalls += `</div>`;
  card.innerHTML = htmlDetalls;
  actionDetails.appendChild(card);
}

// EXECUTAR O REBUTJAR L'ACCIÓ
async function respondreAccio(aprovat) {
  if (!currentActiveAction) return;
  modalApproveBtn.disabled = true;
  modalRejectBtn.disabled = true;

  // Tanquem el modal per retornar al xat
  actionModal.classList.add("hidden");
  const loadingMsg = appendMessage("M.A.R.C.", aprovat ? "Executant acció..." : "Cancel·lant acció...");

  try {
    const res = await fetch("/api/confirm-action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_id: currentActiveAction.action_id,
        approved: aprovat,
        session_id: currentSession
      })
    });
    const result = await res.json();

    if (loadingMsg && loadingMsg.parentElement) {
      chatMessages.removeChild(loadingMsg.parentElement);
    }

    const detallMsg = result.message || (aprovat ? "Acció completada amb èxit." : "Acció cancel·lada per l'usuari.");
    appendMessage("M.A.R.C.", `${aprovat ? "🟢 **Aprovat:**" : "🔴 **Rebutjat:**"} ${detallMsg}`);

    fetchSystemStatus();
  } catch (err) {
    if (loadingMsg && loadingMsg.parentElement) {
      chatMessages.removeChild(loadingMsg.parentElement);
    }
    appendMessage("M.A.R.C.", `⚠️ **Error en processar la confirmació:** ${err.message}`);
  } finally {
    modalApproveBtn.disabled = false;
    modalRejectBtn.disabled = false;
    currentActiveAction = null;
  }
}

// GESTIÓ DEL FORMULARI DE XAT
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage("USER", text, true);
  userInput.value = "";
  const loadingMsg = appendMessage("M.A.R.C.", "Pensant i processant...");

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: currentSession })
    });

    if (!res.ok) {
      loadingMsg.innerHTML = `<span style="color:#ff3366">Error del servidor (${res.status})</span>`;
      return;
    }

    const data = await res.json();
    if (loadingMsg && loadingMsg.parentElement) {
      chatMessages.removeChild(loadingMsg.parentElement);
    }

    appendMessage("M.A.R.C.", data.response);

    if (data.pending_action) {
      obrirModalAccio(data.pending_action);
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
    fetchSystemStatus();
  } catch (err) {
    if (loadingMsg) {
      loadingMsg.innerHTML = `<span style="color:#ff3366">Error de connexió: ${err.message}</span>`;
    }
  }
});

// CANVI I CREACIÓ DE SESSIONS
sessionSelect.addEventListener("change", (e) => {
  currentSession = e.target.value;
  currentSessionLabel.textContent = currentSession;
  chatMessages.innerHTML = "";
  appendMessage("M.A.R.C.", `Has canviat a la sessió **${currentSession}**.`);
});

btnNewSession.addEventListener("click", () => {
  const nom = prompt("Nom de la nova sessió:");
  if (nom && nom.trim()) {
    const cleanNom = nom.trim().replace(/\s+/g, "_");
    const opt = document.createElement("option");
    opt.value = cleanNom;
    opt.textContent = cleanNom;
    sessionSelect.appendChild(opt);
    sessionSelect.value = cleanNom;
    currentSession = cleanNom;
    currentSessionLabel.textContent = currentSession;
    chatMessages.innerHTML = "";
    appendMessage("M.A.R.C.", `Nova sessió **${cleanNom}** iniciada.`);
  }
});

// LISTENERS GENERALS
btnRefresh.addEventListener("click", fetchSystemStatus);
modalApproveBtn.addEventListener("click", () => respondreAccio(true));
modalRejectBtn.addEventListener("click", () => respondreAccio(false));
modalCloseBtn.addEventListener("click", () => actionModal.classList.add("hidden"));

// INICIALITZACIÓ
fetchSystemStatus();