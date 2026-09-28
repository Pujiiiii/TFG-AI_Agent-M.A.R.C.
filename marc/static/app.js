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
const workspaceLabel = document.getElementById("workspace-label");
const btnChangeWs = document.getElementById("btn-change-ws");
const btnNewFile = document.getElementById("btn-new-file");
const btnNewFolder = document.getElementById("btn-new-folder");

// ELEMENTS MODAL STAGING / DIFF / COMANDES
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

// ELEMENTS MODAL EDITOR DE FITXERS
const fileEditorModal = document.getElementById("file-editor-modal");
const editorFilename = document.getElementById("editor-filename");
const editorTextarea = document.getElementById("file-editor-textarea");
const editorStatus = document.getElementById("editor-status");
const editorSaveBtn = document.getElementById("editor-save-btn");
const editorCancelBtn = document.getElementById("editor-cancel-btn");
const editorCloseBtn = document.getElementById("editor-close-btn");

// ESTAT GLOBAL
let currentSession = "sessio_per_defecte";
let currentActiveAction = null;
let currentEditingPath = null;
let currentWorkspace = "marc_test_dropzone";
let arrossegantPath = null;

// CONFIGURACIÓ DE MARKED & HIGHLIGHT.JS
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  breaks: true
});

// GESTIÓ DE L'EDITOR DE FITXERS
async function obrirEditor(path) {
  try {
    const res = await fetch("/api/fs/read", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path })
    });
    if (!res.ok) {
      alert("No s'ha pogut llegir el fitxer.");
      return;
    }
    const data = await res.json();
    currentEditingPath = path;
    editorFilename.textContent = path;
    editorTextarea.value = data.content;
    editorStatus.textContent = "Edita el contingut i clica desar.";
    fileEditorModal.classList.remove("hidden");
  } catch (err) {
    alert("Error obrint l'editor: " + err.message);
  }
}

editorSaveBtn.addEventListener("click", async () => {
  if (!currentEditingPath) return;
  editorSaveBtn.disabled = true;
  editorStatus.textContent = "Desant canvis...";
  try {
    const res = await fetch("/api/fs/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: currentEditingPath,
        content: editorTextarea.value
      })
    });
    const data = await res.json();
    if (res.ok) {
      editorStatus.textContent = "✓ Canvis desats correctament.";
      setTimeout(() => fileEditorModal.classList.add("hidden"), 600);
      fetchSystemStatus();
    } else {
      editorStatus.textContent = "Error: " + data.detail;
    }
  } catch (err) {
    editorStatus.textContent = "Error: " + err.message;
  } finally {
    editorSaveBtn.disabled = false;
  }
});

editorCancelBtn.addEventListener("click", () => fileEditorModal.classList.add("hidden"));
editorCloseBtn.addEventListener("click", () => fileEditorModal.classList.add("hidden"));

// REANOMENAR, MOURE I ELIMINAR FITXERS
async function executarMoure(origen, desti) {
  try {
    const res = await fetch("/api/fs/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ old_path: origen, new_path: desti })
    });
    const data = await res.json();
    if (res.ok) {
      fetchSystemStatus();
    } else {
      alert("Error: " + data.detail);
    }
  } catch (err) {
    alert("Error de xarxa en moure: " + err.message);
  }
}

async function moureElement(oldPath) {
  const nouNom = prompt(`Indica la nova ruta o nom per a:\n${oldPath}`, oldPath);
  if (!nouNom || nouNom.trim() === oldPath) return;
  await executarMoure(oldPath, nouNom.trim());
}

async function esborrarElement(path) {
  if (!confirm(`Estàs segur que vols eliminar definitivament:\n${path}?`)) return;

  try {
    const res = await fetch("/api/fs/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path })
    });
    const data = await res.json();
    if (res.ok) {
      fetchSystemStatus();
    } else {
      alert("Error: " + data.detail);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// RENDERITZAR L'ARBRE AMB DRAG & DROP I ACCIONS
function renderTree(nodes, container) {
  container.innerHTML = "";
  if (!nodes || nodes.length === 0) {
    container.innerHTML = `<div class="loading" style="padding: 8px;">(Carpeta buida. Arrossega arxius aquí per moure'ls a l'arrel)</div>`;
    return;
  }

  const ul = document.createElement("div");

  nodes.forEach(node => {
    if (node.type === "folder") {
      const folderDiv = document.createElement("div");
      folderDiv.className = "tree-folder";

      const row = document.createElement("div");
      row.className = "tree-item-row folder-title";

      const left = document.createElement("div");
      left.className = "item-left";
      left.innerHTML = `📁 <span>${node.name}</span>`;

      const actions = document.createElement("div");
      actions.className = "item-actions";
      actions.innerHTML = `
        <span class="action-icon" title="Moure / Reanomenar">✏️</span>
        <span class="action-icon delete" title="Eliminar carpeta">🗑️</span>
      `;

      actions.children[0].addEventListener("click", (e) => { 
        e.stopPropagation(); 
        moureElement(node.path); 
      });
      actions.children[1].addEventListener("click", (e) => { 
        e.stopPropagation(); 
        esborrarElement(node.path); 
      });

      const content = document.createElement("div");
      content.className = "folder-content";

      left.addEventListener("click", () => {
        content.classList.toggle("collapsed");
        left.firstChild.textContent = content.classList.contains("collapsed") ? "📁" : "📂";
      });

      // DRAG & DROP CAP A SUBFOLDER
      folderDiv.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.stopPropagation(); // Evita que salti el dropzone de l'arrel
        folderDiv.classList.add("drag-over");
      });

      folderDiv.addEventListener("dragleave", (e) => {
        e.stopPropagation();
        folderDiv.classList.remove("drag-over");
      });

      folderDiv.addEventListener("drop", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        folderDiv.classList.remove("drag-over");
        if (arrossegantPath && arrossegantPath !== node.path) {
          const nomFitxer = arrossegantPath.split('/').pop();
          const desti = `${node.path}/${nomFitxer}`;
          await executarMoure(arrossegantPath, desti);
          arrossegantPath = null;
        }
      });

      row.appendChild(left);
      row.appendChild(actions);
      folderDiv.appendChild(row);

      renderTree(node.children, content);
      folderDiv.appendChild(content);
      ul.appendChild(folderDiv);
    } else {
      const fileDiv = document.createElement("div");
      fileDiv.className = "tree-file";

      const row = document.createElement("div");
      row.className = "tree-item-row";
      row.setAttribute("draggable", "true");

      const left = document.createElement("div");
      left.className = "item-left";
      left.innerHTML = `📄 <span>${node.name}</span>`;

      const actions = document.createElement("div");
      actions.className = "item-actions";
      actions.innerHTML = `
        <span class="action-icon" title="Obrir / Editar">✏️</span>
        <span class="action-icon" title="Moure / Reanomenar">⇄</span>
        <span class="action-icon delete" title="Eliminar fitxer">🗑️</span>
      `;

      left.addEventListener("click", () => obrirEditor(node.path));
      actions.children[0].addEventListener("click", (e) => { 
        e.stopPropagation(); 
        obrirEditor(node.path); 
      });
      actions.children[1].addEventListener("click", (e) => { 
        e.stopPropagation(); 
        moureElement(node.path); 
      });
      actions.children[2].addEventListener("click", (e) => { 
        e.stopPropagation(); 
        esborrarElement(node.path); 
      });

      // DRAG & DROP EMISSOR
      row.addEventListener("dragstart", (e) => {
        arrossegantPath = node.path;
        e.dataTransfer.setData("text/plain", node.path);
      });

      row.appendChild(left);
      row.appendChild(actions);
      fileDiv.appendChild(row);
      ul.appendChild(fileDiv);
    }
  });
  container.appendChild(ul);
}

// CONFIGURACIÓ DEL DROPZONE DE L'ARREL (PER TREURE FITXERS CAP A FORA)
function configurarDropzoneArrel(element) {
  element.addEventListener("dragover", (e) => {
    e.preventDefault();
    element.classList.add("root-drag-over");
    if (element === workspaceLabel) element.classList.add("drag-over");
  });

  element.addEventListener("dragleave", () => {
    element.classList.remove("root-drag-over");
    if (element === workspaceLabel) element.classList.remove("drag-over");
  });

  element.addEventListener("drop", async (e) => {
    e.preventDefault();
    element.classList.remove("root-drag-over");
    if (element === workspaceLabel) element.classList.remove("drag-over");

    if (arrossegantPath) {
      const nomFitxer = arrossegantPath.split('/').pop();
      const desti = `${currentWorkspace}/${nomFitxer}`;
      
      // Només movem si realment està canviant de lloc
      if (arrossegantPath !== desti) {
        await executarMoure(arrossegantPath, desti);
      }
      arrossegantPath = null;
    }
  });
}

// Activem la zona de l'arbre i l'etiqueta del workspace com a receptors d'arrel
configurarDropzoneArrel(fileTreeContainer);
configurarDropzoneArrel(workspaceLabel);

// CREACIÓ D'ELEMENTS NOUS
btnNewFile.addEventListener("click", async () => {
  const nom = prompt(`Nom del nou fitxer (dins de ${currentWorkspace}):`);
  if (!nom || !nom.trim()) return;
  const path = `${currentWorkspace}/${nom.trim()}`;
  const res = await fetch("/api/fs/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, is_folder: false })
  });
  if (res.ok) fetchSystemStatus();
});

btnNewFolder.addEventListener("click", async () => {
  const nom = prompt(`Nom de la nova carpeta (dins de ${currentWorkspace}):`);
  if (!nom || !nom.trim()) return;
  const path = `${currentWorkspace}/${nom.trim()}`;
  const res = await fetch("/api/fs/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, is_folder: true })
  });
  if (res.ok) fetchSystemStatus();
});

// CANVI DE WORKSPACE ROOT
btnChangeWs.addEventListener("click", async () => {
  const nou = prompt("Introdueix la ruta del nou espai de treball (ex: '.' o 'marc_test_dropzone'):", currentWorkspace);
  if (!nou || nou.trim() === currentWorkspace) return;

  try {
    const res = await fetch("/api/workspace", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: nou.trim() })
    });
    const data = await res.json();
    if (res.ok) {
      currentWorkspace = data.workspace;
      const targetLabel = document.getElementById("workspace-label");
      if (targetLabel) targetLabel.textContent = currentWorkspace;
      fetchSystemStatus();
      appendMessage("M.A.R.C.", `Espai de treball canviat a: **${currentWorkspace}**.`);
    } else {
      alert("Error: " + data.detail);
    }
  } catch (err) {
    alert("Error de xarxa: " + err.message);
  }
});

// CONSULTAR ESTAT DEL SISTEMA I SESSIONS
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/system-status");
    if (!res.ok) return;
    const data = await res.json();

    if (data.workspace) {
      currentWorkspace = data.workspace;
      const targetLabel = document.getElementById("workspace-label");
      if (targetLabel) {
        targetLabel.textContent = currentWorkspace;
      }
    }

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

    renderTree(data.file_tree, fileTreeContainer);
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

// MODAL D'STAGING / DIFF I RUNNER
function obrirModalDiff(pendingAction) {
  currentActiveAction = pendingAction;
  modalSummary.textContent = pendingAction.summary;
  diffModal.classList.remove("hidden");

  if (pendingAction.type === "exec") {
    diffViewerWrapper.classList.add("hidden");
    modalTabs.classList.add("hidden");
    commandView.classList.remove("hidden");
    commandText.textContent = pendingAction.command || "(Cap ordre especificada)";
    hljs.highlightElement(commandText);
    return;
  }

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

  files.forEach((f, idx) => {
    const tab = document.createElement("button");
    tab.className = `tab-btn ${idx === 0 ? "active" : ""}`;
    tab.textContent = f.ruta.split(/[\\/]/).pop();
    tab.addEventListener("click", () => mostrarFitxer(idx));
    modalTabs.appendChild(tab);
  });

  if (files.length > 0) mostrarFitxer(0);
}

async function respondreAccio(aprovat) {
  if (!currentActiveAction) return;
  modalApproveBtn.disabled = true;
  modalRejectBtn.disabled = true;

  // Tanquem la finestra modal immediatament per retornar el focus al xat
  diffModal.classList.add("hidden");
  const loadingMsg = appendMessage("M.A.R.C.", aprovat ? "Executant acció i recopilant resposta..." : "Cancel·lant acció...");

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

    // Eliminem l'indicador de càrrega
    if (loadingMsg && loadingMsg.parentElement) {
      chatMessages.removeChild(loadingMsg.parentElement);
    }

    // 1. Mostrem l'estat d'aprovació o rebuig del sistema
    const detallMsg = result.message || (aprovat ? "Ordre executada." : "Acció cancel·lada.");
    appendMessage("M.A.R.C.", `${aprovat ? "🟢 **Aprovat:**" : "🔴 **Rebutjat:**"} ${detallMsg}`);

    // 2. Si l'agent ha generat una conclusió posterior a la consola, la pintem al xat
    const explicacioAgent = result.agent_response || result.response;
    if (explicacioAgent && explicacioAgent.trim()) {
      appendMessage("M.A.R.C.", explicacioAgent);
    }

    // 3. Si l'aprovació ha desencadenat una nova acció encadenada (ex: add -> commit)
    if (result.pending_action) {
      obrirModalDiff(result.pending_action);
    }

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

// ENVIAMENT DE FORMULARI DE XAT
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage("USER", text, true);
  userInput.value = "";
  const loadingMsg = appendMessage("M.A.R.C.", "Processant comanda...");

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
modalCloseBtn.addEventListener("click", () => diffModal.classList.add("hidden"));

// INICIALITZACIÓ
fetchSystemStatus();