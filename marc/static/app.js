const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const fileTreeContainer = document.getElementById("file-tree-container");
const statusSearxng = document.getElementById("status-searxng");
const btnRefresh = document.getElementById("btn-refresh");
const btnNewSession = document.getElementById("btn-new-session");
const sessionSelect = document.getElementById("session-select");
const currentSessionLabel = document.getElementById("current-session-label");

let currentSession = "sessio_per_defecte";

// Configurar Marked per a utilitzar Highlight.js
marked.setOptions({
  highlight: function(code, lang) {
    const language = highlight.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  breaks: true
});

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
      
      // En fer clic a un fitxer, prepara una petició per analitzar-lo
      fileDiv.addEventListener("click", () => {
        userInput.value = `Explica'm el fitxer ${node.path} i què fa.`;
        userInput.focus();
      });
      ul.appendChild(fileDiv);
    }
  });
  container.appendChild(ul);
}

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

    // Actualitzar sessions disponibles al selector
    const existing = Array.from(sessionSelect.options).map(o => o.value);
    data.sessions.forEach(s => {
      if (!existing.includes(s)) {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = s;
        sessionSelect.appendChild(opt);
      }
    });

    // Renderitzar arbre jeràrquic
    renderTree(data.file_tree, fileTreeContainer);

  } catch (err) {
    console.error("Error carregant estat:", err);
  }
}

function appendMessage(sender, rawText, isUser = false, pendingAction = null) {
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

    // Si hi ha una acció pendent, afegim el bloc de confirmació amb els dos botons
    if (pendingAction) {
      const actionBox = document.createElement("div");
      actionBox.className = "action-box";

      actionBox.innerHTML = `
        <div class="action-title">⚠️ AUTORITZACIÓ REQUERIDA: ${pendingAction.summary}</div>
        <div class="action-buttons" id="btns-${pendingAction.action_id}">
          <button class="btn-action btn-approve" data-id="${pendingAction.action_id}" data-action="approve">✓ ACCEPTAR I APLICAR</button>
          <button class="btn-action btn-reject" data-id="${pendingAction.action_id}" data-action="reject">✕ REBUTJAR</button>
        </div>
      `;

      bodyDiv.appendChild(actionBox);

      // Gestionar els clics als botons
      const approveBtn = actionBox.querySelector('.btn-approve');
      const rejectBtn = actionBox.querySelector('.btn-reject');
      const btnsContainer = actionBox.querySelector(`#btns-${pendingAction.action_id}`);

      const handleConfirm = async (approved) => {
        approveBtn.disabled = true;
        rejectBtn.disabled = true;

        try {
          const res = await fetch("/api/confirm-action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              action_id: pendingAction.action_id,
              approved: approved,
              session_id: currentSession
            })
          });
          const result = await res.json();
          
          btnsContainer.innerHTML = `<span class="action-status-resolved">${approved ? "🟢 Aprovat:" : "🔴 Rebutjat:"} ${result.message}</span>`;
          fetchSystemStatus(); // Refrescar arbre de fitxers si s'ha aplicat un canvi
        } catch (err) {
          btnsContainer.innerHTML = `<span style="color:#ff3366">Error enviant confirmació: ${err.message}</span>`;
        }
      };

      approveBtn.addEventListener("click", () => handleConfirm(true));
      rejectBtn.addEventListener("click", () => handleConfirm(false));
    }
  }

  msgDiv.appendChild(authorDiv);
  msgDiv.appendChild(bodyDiv);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return bodyDiv;
}

// Canvi de sessió
sessionSelect.addEventListener("change", (e) => {
  currentSession = e.target.value;
  currentSessionLabel.textContent = currentSession;
  chatMessages.innerHTML = "";
  appendMessage("M.A.R.C.", `Has canviat a la sessió **${currentSession}**.`);
});

// Crear nova sessió
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

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  // 1. Mostrem el missatge de l'usuari i netegem l'input
  appendMessage("USER", text, true);
  userInput.value = "";

  // 2. Creem el missatge temporal d'espera
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

    // 3. Eliminem el missatge temporal de càrrega
    if (loadingMsg && loadingMsg.parentElement) {
      chatMessages.removeChild(loadingMsg.parentElement);
    }

    // 4. Inserim la resposta definitiva (i els botons d'acció si n'hi ha)
    appendMessage("M.A.R.C.", data.response, false, data.pending_action);

    chatMessages.scrollTop = chatMessages.scrollHeight;

    // 5. Refresquem l'arbre de fitxers i l'estat del sistema
    fetchSystemStatus();

  } catch (err) {
    if (loadingMsg) {
      loadingMsg.innerHTML = `<span style="color:#ff3366">Error de connexió: ${err.message}</span>`;
    }
  }
});

btnRefresh.addEventListener("click", fetchSystemStatus);

fetchSystemStatus();