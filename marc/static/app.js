// ELEMENTS DOM PRINCIPALS
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const fileTreeContainer = document.getElementById("file-tree-container");
const statusSearxng = document.getElementById("status-searxng");
const btnRefresh = document.getElementById("btn-refresh");
const btnNewSession = document.getElementById("btn-new-session");
const sessionSelect = document.getElementById("session-select");
const currentSessionLabel = document.getElementById("current-session-label");

// ELEMENTS MODAL
const diffModal = document.getElementById("diff-modal");
const modalSummary = document.getElementById("modal-summary");
const modalTabs = document.getElementById("modal-tabs");
const codeBefore = document.getElementById("code-before");
const codeAfter = document.getElementById("code-after");
const filenameOrig = document.getElementById("diff-filename-orig");
const commandView = document.getElementById("command-view");
const commandText = document.getElementById("command-text");
const diffViewerWrapper = document.querySelector(".diff-viewer-wrapper");
const modalCloseBtn = document.getElementById("modal-close-btn");
const modalApproveBtn = document.getElementById("modal-approve-btn");
const modalRejectBtn = document.getElementById("modal-reject-btn");

let currentSession = "sessio_per_defecte";
let currentActiveAction = null;

// Configurar Marked per a utilitzar Highlight.js
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  breaks: true
});

// Renderitzar l'arbre jeràrquic de fitxers i carpetes
function renderTree(nodes, container) {
  container.innerHTML = "";
  const ul = document.createElement("div");

  nodes.forEach(node => {
    if (node.type === "folder") {
      const folderDiv = document.createElement("div");
      folderDiv.className = "tree-folder";

      const title = document.createElement("div");
      title.className = "folder-title";
      title.innerHTML = `📁 <span>${node.name}</span>`;

      const content = document.createElement("div");
      content.className = "folder-content";

      title.addEventListener("click", () => {
        content.classList.toggle("collapsed");
        title.firstChild.textContent = content.classList.contains("collapsed") ? "📁" : "📂";
      });

      renderTree(node.children, content);
      folderDiv.appendChild(title);
      folderDiv.appendChild(content);
      ul.appendChild(folderDiv);
    } else {
      const fileDiv = document.createElement("div");
      fileDiv.className = "tree-file";
      fileDiv.innerHTML = `📄 <span>${node.name}</span>`;
      
      fileDiv.addEventListener("click", () => {
        userInput.value = `Explica'm el fitxer ${node.path} i què fa.`;
        userInput.focus();
      });
      ul.appendChild(fileDiv);
    }
  });
  container.appendChild(ul);
}

// Consultar estat del sistema, serveis i arbre d'arxius
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/system-status");
    if (!res.ok) return;
    const data = await res.json();

    // Actualitzar SearxNG
    statusSearxng.textContent = data.services.searxng;
    if (data.services.searxng === "OFFLINE") {
      statusSearxng.classList.add("offline");
    } else {
      statusSearxng.classList.remove("offline");
    }

    // Actualitzar llista de sessions
    const existing = Array.from(sessionSelect.options).map(o => o.value);
    data.sessions.forEach(s => {
      if (!existing.includes(s)) {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = s;
        sessionSelect.appendChild(opt);
      }
    });

    // Renderitzar arbre
    renderTree(data.file_tree, fileTreeContainer);

  } catch (err) {
    console.error("Error carregant estat:", err);
  }
}

// Afegir missatge al xat
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
    bodyDiv.innerHTML = marked.parse(rawText);
  }

  msgDiv.appendChild(authorDiv);
  msgDiv.appendChild(bodyDiv);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return bodyDiv;
}

// OBRIR LA MODAL INTERACTIVA DE DIFF / RUNNER
function obrirModalDiff(pendingAction) {
  currentActiveAction = pendingAction;
  modalSummary.textContent = pendingAction.summary;
  diffModal.classList.remove("hidden");

  // Cas 1: Execució de comanda / script
  if (pendingAction.type === "exec") {
    diffViewerWrapper.classList.add("hidden");
    modalTabs.classList.add("hidden");
    commandView.classList.remove("hidden");
    commandText.textContent = pendingAction.command || "(Cap ordre especificada)";
    hljs.highlightElement(commandText);
    return;
  }

  // Cas 2: Diff / Modificació de fitxers
  commandView.classList.add("hidden");
  diffViewerWrapper.classList.remove("hidden");
  modalTabs.classList.remove("hidden");
  modalTabs.innerHTML = "";

  const files = pendingAction.files || [];

  function mostrarFitxer(index) {
    const f = files[index];
    filenameOrig.textContent = f.ruta;
    codeBefore.textContent = f.contingut_antic || "(Nou fitxer)";
    codeAfter.textContent = f.contingut_nou || "";
    hljs.highlightElement(codeBefore);
    hljs.highlightElement(codeAfter);

    document.querySelectorAll(".tab-btn").forEach((btn, idx) => {
      btn.classList.toggle("active", idx === index);
    });
  }

  // Crear pestanyes si hi ha múltiples fitxers
  files.forEach((f, idx) => {
    const tab = document.createElement("button");
    tab.className = `tab-btn ${idx === 0 ? "active" : ""}`;
    tab.textContent = f.ruta.split(/[\\/]/).pop();
    tab.addEventListener("click", () => mostrarFitxer(idx));
    modalTabs.appendChild(tab);
  });

  if (files.length > 0) {
    mostrarFitxer(0);
  }
}

// RESPONDRE A L'ACCIÓ (APROVAR O REBUTJAR)
async function respondreAccio(aprovat) {
  if (!currentActiveAction) return;
  modalApproveBtn.disabled = true;
  modalRejectBtn.disabled = true;

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
    diffModal.classList.add("hidden");
    appendMessage("M.A.R.C.", `${aprovat ? "🟢 **Aprovat:**" : "🔴 **Rebutjat:**"} ${result.message}`);
    fetchSystemStatus();
  } catch (err) {
    alert("Error enviant la decisió: " + err.message);
  } finally {
    modalApproveBtn.disabled = false;
    modalRejectBtn.disabled = false;
    currentActiveAction = null;
  }
}

// GESTIÓ DEL FORMULARI DE XAT (SUBMIT) SENCER
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  // 1. Mostrar missatge de l'usuari
  appendMessage("USER", text, true);
  userInput.value = "";

  // 2. Missatge temporal de càrrega
  const loadingMsg = appendMessage("M.A.R.C.", "Processant comanda...");

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        session_id: currentSession
      })
    });

    if (!res.ok) {
      loadingMsg.innerHTML = `<span style="color:#ff3366">Error del servidor (${res.status})</span>`;
      return;
    }

    const data = await res.json();

    // 3. Eliminar missatge temporal
    if (loadingMsg && loadingMsg.parentElement) {
      chatMessages.removeChild(loadingMsg.parentElement);
    }

    // 4. Mostrar resposta de M.A.R.C.
    appendMessage("M.A.R.C.", data.response);

    // 5. Si hi ha una acció pendent, obrim directament la finestra emergent interactiva
    if (data.pending_action) {
      obrirModalDiff(data.pending_action);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
    fetchSystemStatus();

  } catch (err) {
    if (loadingMsg) {
      loadingMsg.innerHTML = `<span style="color:#ff3366">Error de connexió: ${err.message}</span>`;
    }
  }
});

// ESDEVENIMENTS DE SESSIONS I MODAL
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

btnRefresh.addEventListener("click", fetchSystemStatus);
modalApproveBtn.addEventListener("click", () => respondreAccio(true));
modalRejectBtn.addEventListener("click", () => respondreAccio(false));
modalCloseBtn.addEventListener("click", () => diffModal.classList.add("hidden"));

// Càrrega inicial
fetchSystemStatus();