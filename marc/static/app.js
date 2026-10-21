// ELEMENTS DOM PRINCIPALS
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const btnRefresh = document.getElementById("btn-refresh");
const btnNewSession = document.getElementById("btn-new-session");
const sessionSelect = document.getElementById("session-select");
const currentSessionLabel = document.getElementById("current-session-label");

// BADGES D'ESTAT DE SERVEIS
const statusBackend = document.getElementById("status-backend");
const statusDb = document.getElementById("status-db");
const statusSearxng = document.getElementById("status-searxng");
const statusEmail = document.getElementById("status-email");
const statusTelegram = document.getElementById("status-telegram");

// ELEMENTS DEL WIDGET D'AGENDA I TASQUES
const tabBtnTasks = document.getElementById("tab-btn-tasks");
const tabBtnAgenda = document.getElementById("tab-btn-agenda");
const tasksContainer = document.getElementById("tasks-container");
const agendaContainer = document.getElementById("agenda-container");
const tasksList = document.getElementById("tasks-list");
const agendaList = document.getElementById("agenda-list");
const taskCount = document.getElementById("task-count");
const agendaCount = document.getElementById("agenda-count");
const agendaDateLabel = document.getElementById("agenda-date-label");
const btnAddTaskUi = document.getElementById("btn-add-task-ui");

// MODAL DE NOVA TASCA
const newTaskModal = document.getElementById("new-task-modal");
const newTaskForm = document.getElementById("new-task-form");
const taskModalCloseBtn = document.getElementById("task-modal-close-btn");
const taskCancelBtn = document.getElementById("task-cancel-btn");
const taskTitleInput = document.getElementById("task-title-input");
const taskPrioInput = document.getElementById("task-prio-input");
const taskDateInput = document.getElementById("task-date-input");
const taskDescInput = document.getElementById("task-desc-input");

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

// PESTANYES DEL WIDGET (TASQUES / AGENDA)
tabBtnTasks.addEventListener("click", () => {
  tabBtnTasks.classList.add("active");
  tabBtnAgenda.classList.remove("active");
  tasksContainer.classList.remove("hidden");
  agendaContainer.classList.add("hidden");
});

tabBtnAgenda.addEventListener("click", () => {
  tabBtnAgenda.classList.add("active");
  tabBtnTasks.classList.remove("active");
  agendaContainer.classList.remove("hidden");
  tasksContainer.classList.add("hidden");
});

// CONSULTAR ESTAT DEL SISTEMA I SESSIONS
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/system-status");
    if (!res.ok) return;
    const data = await res.json();

    if (data.services) {
      if (statusBackend) statusBackend.textContent = data.services.backend || "ONLINE";
      if (statusDb) statusDb.textContent = data.services.database || "ONLINE";
      if (statusSearxng) {
        statusSearxng.textContent = data.services.searxng;
        statusSearxng.className = `badge ${data.services.searxng === "OFFLINE" ? "offline" : ""}`;
      }
      if (statusEmail) statusEmail.textContent = data.services.email_hub || "LOCAL_HUB";
      if (statusTelegram) {
        statusTelegram.textContent = data.services.telegram;
        statusTelegram.className = `badge ${data.services.telegram === "STANDBY" ? "standby" : ""}`;
      }
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

// CONSULTAR I PINTAR DASHBOARD (TASQUES I AGENDA)
async function fetchDashboard() {
  try {
    const res = await fetch("/api/dashboard");
    if (!res.ok) return;
    const data = await res.json();

    // 1. RENDERITZAR TASQUES
    const tasks = data.tasks || [];
    const pendingTasks = tasks.filter(t => t.status === "pendent");
    taskCount.textContent = pendingTasks.length;

    if (tasks.length === 0) {
      tasksList.innerHTML = `<div class="empty-state">No hi ha cap tasca. Fes clic a '+ Nova' per afegir-ne una!</div>`;
    } else {
      tasksList.innerHTML = "";
      tasks.forEach(t => {
        const item = document.createElement("div");
        item.className = "task-item";

        const isDone = (t.status === "completada");
        const prioClass = (t.priority || "mitjana").toLowerCase();

        item.innerHTML = `
          <input type="checkbox" class="task-checkbox" ${isDone ? "checked" : ""} data-id="${t.id}">
          <div class="task-content">
            <span class="task-title ${isDone ? "completed" : ""}">${t.title}</span>
            <div class="task-meta">
              <span class="prio-badge ${prioClass}">${(t.priority || "mitjana").toUpperCase()}</span>
              ${t.due_date ? `<span class="task-due">📅 ${t.due_date}</span>` : ""}
            </div>
          </div>
        `;

        const chk = item.querySelector(".task-checkbox");
        chk.addEventListener("change", async () => {
          await toggleTask(t.id);
        });

        tasksList.appendChild(item);
      });
    }

    // 2. RENDERITZAR AGENDA
    const events = data.events || [];
    agendaCount.textContent = events.length;
    if (data.today_date) {
      agendaDateLabel.textContent = `Reunions d'avui (${data.today_date})`;
    }

    if (events.length === 0) {
      agendaList.innerHTML = `<div class="empty-state">Sense reunions per avui. Jornada lliure!</div>`;
    } else {
      agendaList.innerHTML = "";
      events.forEach(ev => {
        const evItem = document.createElement("div");
        evItem.className = "agenda-item";

        const horaInici = ev.start_time.includes(" ") ? ev.start_time.split(" ")[1] : ev.start_time;
        const horaFi = (ev.end_time && ev.end_time.includes(" ")) ? ` - ${ev.end_time.split(" ")[1]}` : "";

        evItem.innerHTML = `
          <div class="agenda-time">🕒 ${horaInici}${horaFi}</div>
          <div class="agenda-title">${ev.title}</div>
          ${ev.location ? `<div class="agenda-location">📍 ${ev.location}</div>` : ""}
        `;
        agendaList.appendChild(evItem);
      });
    }

  } catch (err) {
    console.error("Error carregant el dashboard:", err);
  }
}

// TOGGLE TASCA (COMPLETAR / REACTIVAR)
async function toggleTask(taskId) {
  try {
    const res = await fetch("/api/tasks/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId })
    });
    if (res.ok) {
      await fetchDashboard();
    }
  } catch (err) {
    console.error("Error canviant estat de la tasca:", err);
  }
}

// MODAL DE CREACIÓ DE TASCA MANUAL
btnAddTaskUi.addEventListener("click", () => {
  taskTitleInput.value = "";
  taskDescInput.value = "";
  taskDateInput.value = new Date().toISOString().split("T")[0];
  taskPrioInput.value = "mitjana";
  newTaskModal.classList.remove("hidden");
});

taskModalCloseBtn.addEventListener("click", () => newTaskModal.classList.add("hidden"));
taskCancelBtn.addEventListener("click", () => newTaskModal.classList.add("hidden"));

newTaskForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const titol = taskTitleInput.value.trim();
  if (!titol) return;

  try {
    const res = await fetch("/api/tasks/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: titol,
        priority: taskPrioInput.value,
        due_date: taskDateInput.value,
        description: taskDescInput.value
      })
    });
    if (res.ok) {
      newTaskModal.classList.add("hidden");
      await fetchDashboard();
      appendMessage("M.A.R.C.", `✅ Tasca manual afegida: **${titol}** (${taskPrioInput.value.toUpperCase()}).`);
    }
  } catch (err) {
    alert("Error creant la tasca: " + err.message);
  }
});

// XIPS D'ACCIONS RÀPIDES
document.querySelectorAll(".quick-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const prompt = chip.getAttribute("data-prompt");
    if (prompt) {
      enviarMissatgeXat(prompt);
    }
  });
});

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

  // Renderització personalitzada segons el tipus d'acció
  if (tipus === "email") {
    htmlDetalls += `
      <div class="action-field">
        <div class="action-field-name">DESTINATARI:</div>
        <div class="action-field-val">${dades.destinatari || "(Sense destinatari)"}</div>
      </div>
      <div class="action-field">
        <div class="action-field-name">ASSUMPTE:</div>
        <div class="action-field-val">${dades.assumpte || "(Sense assumpte)"}</div>
      </div>
      <div class="action-field">
        <div class="action-field-name">COS DEL CORREU:</div>
        <div class="action-field-val">${dades.cos || ""}</div>
      </div>
    `;
  } else if (tipus === "calendar" || tipus === "calendar_delete") {
    htmlDetalls += `
      <div class="action-field">
        <div class="action-field-name">TÍTOL / REUNIÓ:</div>
        <div class="action-field-val">${dades.titol || dades.esdeveniment_id}</div>
      </div>
      ${dades.data_inici ? `
        <div class="action-field">
          <div class="action-field-name">DATA I HORA D'INICI:</div>
          <div class="action-field-val">${dades.data_inici} (Durada: ${dades.durada || '60 minuts'})</div>
        </div>
      ` : ""}
      ${dades.lloc ? `
        <div class="action-field">
          <div class="action-field-name">LLOC / ENLLAÇ:</div>
          <div class="action-field-val">${dades.lloc}</div>
        </div>
      ` : ""}
    `;
  } else if (tipus === "message") {
    htmlDetalls += `
      <div class="action-field">
        <div class="action-field-name">CANAL I DESTINATARI:</div>
        <div class="action-field-val">${(dades.canal || 'Telegram').toUpperCase()} → ${dades.destinatari}</div>
      </div>
      <div class="action-field">
        <div class="action-field-name">MISSATGE:</div>
        <div class="action-field-val">${dades.missatge}</div>
      </div>
    `;
  } else {
    // Genèric
    const claus = Object.keys(dades);
    if (claus.length > 0) {
      claus.forEach(k => {
        const val = typeof dades[k] === "object" ? JSON.stringify(dades[k], null, 2) : dades[k];
        htmlDetalls += `
          <div class="action-field">
            <div class="action-field-name">${k.toUpperCase().replace(/_/g, " ")}:</div>
            <div class="action-field-val">${val}</div>
          </div>
        `;
      });
    } else {
      htmlDetalls += `<div class="action-field-val">${pendingAction.summary}</div>`;
    }
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

    await fetchDashboard();
    await fetchSystemStatus();
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

// ENVIAMENT DE MISSATGES AL XAT
async function enviarMissatgeXat(text) {
  if (!text || !text.trim()) return;

  appendMessage("USER", text, true);
  userInput.value = "";
  const loadingMsg = appendMessage("M.A.R.C.", "Pensant i processant comanda executiva...");

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

    await fetchDashboard();
    await fetchSystemStatus();
  } catch (err) {
    if (loadingMsg) {
      loadingMsg.innerHTML = `<span style="color:#ff3366">Error de connexió: ${err.message}</span>`;
    }
  }
}

// FORMULARI DE XAT
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  enviarMissatgeXat(userInput.value.trim());
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
btnRefresh.addEventListener("click", () => {
  fetchDashboard();
  fetchSystemStatus();
});
modalApproveBtn.addEventListener("click", () => respondreAccio(true));
modalRejectBtn.addEventListener("click", () => respondreAccio(false));
modalCloseBtn.addEventListener("click", () => actionModal.classList.add("hidden"));

// INICIALITZACIÓ
fetchDashboard();
fetchSystemStatus();