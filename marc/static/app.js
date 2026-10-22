// ELEMENTS DOM PRINCIPALS
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const btnRefresh = document.getElementById("btn-refresh");
const btnNewSession = document.getElementById("btn-new-session");
const sessionSelect = document.getElementById("session-select");
const currentSessionLabel = document.getElementById("current-session-label");
let currentSession = localStorage.getItem("marc_session") || "sessio_per_defecte";

// BADGES D'ESTAT DE SERVEIS
const statusBackend = document.getElementById("status-backend");
const statusDb = document.getElementById("status-db");
const statusNetwork = document.getElementById("status-network");
const statusCalendar = document.getElementById("status-calendar");
const statusEmail = document.getElementById("status-email");
const statusSpotify = document.getElementById("status-spotify");
const statusSearxng = document.getElementById("status-searxng");
const statusTelegram = document.getElementById("status-telegram");
const btnSyncNow = document.getElementById("btn-sync-now");

// ELEMENTS DEL WIDGET D'AGENDA I TASQUES
const tabBtnTasks = document.getElementById("tab-btn-tasks");
const tabBtnAgenda = document.getElementById("tab-btn-agenda");
const tabBtnDual = document.getElementById("tab-btn-dual");
const widgetPanel = document.querySelector(".widget-panel");
const tasksContainer = document.getElementById("tasks-container");
const agendaContainer = document.getElementById("agenda-container");
const tasksList = document.getElementById("tasks-list");
const agendaList = document.getElementById("agenda-list");
const taskCount = document.getElementById("task-count");
const agendaCount = document.getElementById("agenda-count");
const agendaDateLabel = document.getElementById("agenda-date-label");
const btnAddTaskUi = document.getElementById("btn-add-task-ui");
const btnAddEventUi = document.getElementById("btn-add-event-ui");
const btnAnalyzeUdgUi = document.getElementById("btn-analyze-udg-ui");
const tabBtnWorkflows = document.getElementById("tab-btn-workflows");
const workflowsContainer = document.getElementById("workflows-container");
const workflowsList = document.getElementById("workflows-list");
const workflowsCount = document.getElementById("workflows-count");
const btnRunWorkflowsUi = document.getElementById("btn-run-workflows-ui");

// NOVES PESTANYES I VISTES (DOCS & MÈTRIQUES)
const tabBtnDocs = document.getElementById("tab-btn-docs");
const docsContainer = document.getElementById("docs-container");
const docsList = document.getElementById("docs-list");
const docsCount = document.getElementById("docs-count");
const btnUploadDocTab = document.getElementById("btn-upload-doc-tab");

const tabBtnAnalytics = document.getElementById("tab-btn-analytics");
const analyticsContainer = document.getElementById("analytics-container");
const analyticsContent = document.getElementById("analytics-content");
const btnRefreshAnalytics = document.getElementById("btn-refresh-analytics");

// NOVES EINES HUD & MULTIMODAL (METEO, FOCUS, VEU, DOCUMENTS)
const weatherBadge = document.getElementById("weather-badge");
const weatherIcon = document.getElementById("weather-icon");
const weatherText = document.getElementById("weather-text");
const btnFocusQuick = document.getElementById("btn-focus-quick");
const btnVoiceToggle = document.getElementById("btn-voice-toggle");
const btnMic = document.getElementById("btn-mic");
const btnUploadDoc = document.getElementById("btn-upload-doc");
const fileUploadInput = document.getElementById("file-upload-input");

// MODAL HITL CONFIRMACIÓ D'ACCIONS
const actionModal = document.getElementById("diff-modal");
const modalSummary = document.getElementById("modal-summary");
const actionDetails = document.getElementById("action-details");
const modalApproveBtn = document.getElementById("modal-approve-btn");
const modalRejectBtn = document.getElementById("modal-reject-btn");
const modalCloseBtn = document.getElementById("modal-close-btn");
let currentActiveAction = null;

// MODAL CREACIÓ TASCA MANUAL
const newTaskModal = document.getElementById("new-task-modal");
const taskTitleInput = document.getElementById("task-title-input");
const taskPrioInput = document.getElementById("task-prio-input");
const taskDateInput = document.getElementById("task-date-input");
const taskDescInput = document.getElementById("task-desc-input");
const taskModalCloseBtn = document.getElementById("task-modal-close-btn");
const taskCancelBtn = document.getElementById("task-cancel-btn");
const newTaskForm = document.getElementById("new-task-form");

// MODAL CREACIÓ CITA MANUAL
const newEventModal = document.getElementById("new-event-modal");
const eventTitleInput = document.getElementById("event-title-input");
const eventDateInput = document.getElementById("event-date-input");
const eventTimeInput = document.getElementById("event-time-input");
const eventDurationInput = document.getElementById("event-duration-input");
const eventLocInput = document.getElementById("event-loc-input");
const eventModalCloseBtn = document.getElementById("event-modal-close-btn");
const eventCancelBtn = document.getElementById("event-cancel-btn");
const newEventForm = document.getElementById("new-event-form");

// MODAL CREACIÓ DE SESSIÓ
const newSessionModal = document.getElementById("new-session-modal");
const newSessionForm = document.getElementById("new-session-form");
const sessionNameInput = document.getElementById("session-name-input");
const sessionModalClose = document.getElementById("session-modal-close");
const sessionModalCancel = document.getElementById("session-modal-cancel");

// MODAL DETALL D'ACTIVITAT (TASCA / CITA)
const activityDetailModal = document.getElementById("activity-detail-modal");
const activityModalClose = document.getElementById("activity-modal-close");
const activityModalBadge = document.getElementById("activity-modal-badge");
const activityDetailTitle = document.getElementById("activity-detail-title");
const activityDetailMeta = document.getElementById("activity-detail-meta");
const activityDetailTime = document.getElementById("activity-detail-time");
const activityDetailLoc = document.getElementById("activity-detail-loc");
const activityDetailStatus = document.getElementById("activity-detail-status");
const activityDetailDesc = document.getElementById("activity-detail-desc");
const activityInfoTimeBox = document.getElementById("activity-info-time-box");
const activityInfoLocBox = document.getElementById("activity-info-loc-box");
const btnActivityDelete = document.getElementById("btn-activity-delete");
const btnActivityToggleDone = document.getElementById("btn-activity-toggle-done");
const btnActivityEdit = document.getElementById("btn-activity-edit");
const activityViewMode = document.getElementById("activity-view-mode");
const activityEditForm = document.getElementById("activity-edit-form");
const editActivityTitle = document.getElementById("edit-activity-title");
const editEventFields = document.getElementById("edit-event-fields");
const editEventStart = document.getElementById("edit-event-start");
const editEventEnd = document.getElementById("edit-event-end");
const editEventLoc = document.getElementById("edit-event-loc");
const editTaskFields = document.getElementById("edit-task-fields");
const editTaskPrio = document.getElementById("edit-task-prio");
const editTaskDue = document.getElementById("edit-task-due");
const editActivityDesc = document.getElementById("edit-activity-desc");
const btnCancelEdit = document.getElementById("btn-cancel-edit");

// MODAL CALENDARI INTERACTIU
const calendarModal = document.getElementById("calendar-modal");
const btnOpenCalendarUi = document.getElementById("btn-open-calendar-ui");
const calendarModalClose = document.getElementById("calendar-modal-close");
const calendarGrid = document.getElementById("calendar-grid");
const calendarMonthYearLabel = document.getElementById("calendar-month-year-label");
const btnCalPrev = document.getElementById("btn-cal-prev");
const btnCalToday = document.getElementById("btn-cal-today");
const btnCalNext = document.getElementById("btn-cal-next");
const btnCalAdd = document.getElementById("btn-cal-add");

// MODAL DIAGRAMA DE FLUXOS ASÍNCRONS
const workflowDiagramModal = document.getElementById("workflow-diagram-modal");
const wfModalClose = document.getElementById("wf-modal-close");
const wfModalTitle = document.getElementById("wf-modal-title");
const wfModalSubtitle = document.getElementById("wf-modal-subtitle");
const wfModalDesc = document.getElementById("wf-modal-desc");
const nodeStart = document.getElementById("node-start");
const nodeWaiting = document.getElementById("node-waiting");
const nodeEval = document.getElementById("node-eval");
const nodeSuccess = document.getElementById("node-success");
const nodeReview = document.getElementById("node-review");
const nodeCounter = document.getElementById("node-counter");
const wfInteractiveActions = document.getElementById("wf-interactive-actions");
const wfDecisionMessage = document.getElementById("wf-decision-message");
const btnWfAcceptAlt = document.getElementById("btn-wf-accept-alt");
const btnWfProposeNew = document.getElementById("btn-wf-propose-new");
const btnWfCancel = document.getElementById("btn-wf-cancel");
const wfLogsList = document.getElementById("wf-logs-list");

// VARIABLES D'ESTAT INTERACTIU
let currentSelectedActivity = null;
let currentSelectedWorkflow = null;
let calYear = new Date().getFullYear();
let calMonth = new Date().getMonth();
let allDashboardEvents = [];

// SERVEIS ACTIUS (COLLAPSIBLE HUD)
const servicesHeader = document.getElementById("services-header");
const servicesGrid = document.getElementById("services-grid");
const servicesToggleIcon = document.getElementById("services-toggle-icon");
const servicesSummaryPill = document.getElementById("services-summary-pill");

if (servicesHeader && servicesGrid) {
  servicesHeader.addEventListener("click", (e) => {
    if (e.target.tagName === "BUTTON") return;
    const isCollapsed = servicesGrid.classList.toggle("collapsed");
    if (servicesToggleIcon) servicesToggleIcon.classList.toggle("collapsed", isCollapsed);
    localStorage.setItem("marc_services_collapsed", isCollapsed ? "1" : "0");
  });

  if (localStorage.getItem("marc_services_collapsed") === "1") {
    servicesGrid.classList.add("collapsed");
    if (servicesToggleIcon) servicesToggleIcon.classList.add("collapsed");
  }
}

// BOTÓ D'ANÀLISI DE CORREUS UDG
if (btnAnalyzeUdgUi) {
  btnAnalyzeUdgUi.addEventListener("click", async () => {
    btnAnalyzeUdgUi.disabled = true;
    btnAnalyzeUdgUi.textContent = "⏳...";
    try {
      const res = await fetch("/api/udg/analyze");
      const data = await res.json();
      if (data.processed_count > 0) {
        appendMessage("assistant", `🎓 **Anàlisi UdG completada:**\n${data.message}`);
      } else {
        appendMessage("assistant", "🎓 Tot al dia! No hi ha correus nous de la UdG pendents d'analitzar.");
      }
      await fetchDashboard();
    } catch (err) {
      console.error("Error analitzant correus UdG:", err);
    } finally {
      btnAnalyzeUdgUi.disabled = false;
      btnAnalyzeUdgUi.textContent = "🎓 UdG";
    }
  });
}

// PESTANYES DEL WIDGET (TASQUES / AGENDA / FLUXOS / DOCS / MÈTRIQUES / DUAL)
tabBtnTasks.addEventListener("click", () => {
  tabBtnTasks.classList.add("active");
  tabBtnAgenda.classList.remove("active");
  if (tabBtnWorkflows) tabBtnWorkflows.classList.remove("active");
  if (tabBtnDocs) tabBtnDocs.classList.remove("active");
  if (tabBtnAnalytics) tabBtnAnalytics.classList.remove("active");
  if (tabBtnDual) tabBtnDual.classList.remove("active");
  if (widgetPanel) widgetPanel.classList.remove("dual-mode");
  tasksContainer.classList.remove("hidden");
  agendaContainer.classList.add("hidden");
  if (workflowsContainer) workflowsContainer.classList.add("hidden");
  if (docsContainer) docsContainer.classList.add("hidden");
  if (analyticsContainer) analyticsContainer.classList.add("hidden");
});

tabBtnAgenda.addEventListener("click", () => {
  tabBtnAgenda.classList.add("active");
  tabBtnTasks.classList.remove("active");
  if (tabBtnWorkflows) tabBtnWorkflows.classList.remove("active");
  if (tabBtnDocs) tabBtnDocs.classList.remove("active");
  if (tabBtnAnalytics) tabBtnAnalytics.classList.remove("active");
  if (tabBtnDual) tabBtnDual.classList.remove("active");
  if (widgetPanel) widgetPanel.classList.remove("dual-mode");
  agendaContainer.classList.remove("hidden");
  tasksContainer.classList.add("hidden");
  if (workflowsContainer) workflowsContainer.classList.add("hidden");
  if (docsContainer) docsContainer.classList.add("hidden");
  if (analyticsContainer) analyticsContainer.classList.add("hidden");
});

if (tabBtnWorkflows) {
  tabBtnWorkflows.addEventListener("click", () => {
    tabBtnWorkflows.classList.add("active");
    tabBtnTasks.classList.remove("active");
    tabBtnAgenda.classList.remove("active");
    if (tabBtnDocs) tabBtnDocs.classList.remove("active");
    if (tabBtnAnalytics) tabBtnAnalytics.classList.remove("active");
    if (tabBtnDual) tabBtnDual.classList.remove("active");
    if (widgetPanel) widgetPanel.classList.remove("dual-mode");
    if (workflowsContainer) workflowsContainer.classList.remove("hidden");
    tasksContainer.classList.add("hidden");
    agendaContainer.classList.add("hidden");
    if (docsContainer) docsContainer.classList.add("hidden");
    if (analyticsContainer) analyticsContainer.classList.add("hidden");
  });
}

if (tabBtnDocs) {
  tabBtnDocs.addEventListener("click", () => {
    tabBtnDocs.classList.add("active");
    tabBtnTasks.classList.remove("active");
    tabBtnAgenda.classList.remove("active");
    if (tabBtnWorkflows) tabBtnWorkflows.classList.remove("active");
    if (tabBtnAnalytics) tabBtnAnalytics.classList.remove("active");
    if (tabBtnDual) tabBtnDual.classList.remove("active");
    if (widgetPanel) widgetPanel.classList.remove("dual-mode");
    if (docsContainer) docsContainer.classList.remove("hidden");
    tasksContainer.classList.add("hidden");
    agendaContainer.classList.add("hidden");
    if (workflowsContainer) workflowsContainer.classList.add("hidden");
    if (analyticsContainer) analyticsContainer.classList.add("hidden");
    loadDocuments();
  });
}

if (tabBtnAnalytics) {
  tabBtnAnalytics.addEventListener("click", () => {
    tabBtnAnalytics.classList.add("active");
    tabBtnTasks.classList.remove("active");
    tabBtnAgenda.classList.remove("active");
    if (tabBtnWorkflows) tabBtnWorkflows.classList.remove("active");
    if (tabBtnDocs) tabBtnDocs.classList.remove("active");
    if (tabBtnDual) tabBtnDual.classList.remove("active");
    if (widgetPanel) widgetPanel.classList.remove("dual-mode");
    if (analyticsContainer) analyticsContainer.classList.remove("hidden");
    tasksContainer.classList.add("hidden");
    agendaContainer.classList.add("hidden");
    if (workflowsContainer) workflowsContainer.classList.add("hidden");
    if (docsContainer) docsContainer.classList.add("hidden");
    loadAnalytics();
  });
}

if (tabBtnDual) {
  tabBtnDual.addEventListener("click", () => {
    tabBtnDual.classList.add("active");
    tabBtnTasks.classList.remove("active");
    tabBtnAgenda.classList.remove("active");
    if (tabBtnWorkflows) tabBtnWorkflows.classList.remove("active");
    if (tabBtnDocs) tabBtnDocs.classList.remove("active");
    if (tabBtnAnalytics) tabBtnAnalytics.classList.remove("active");
    if (widgetPanel) widgetPanel.classList.add("dual-mode");
    tasksContainer.classList.remove("hidden");
    agendaContainer.classList.remove("hidden");
    if (workflowsContainer) workflowsContainer.classList.add("hidden");
    if (docsContainer) docsContainer.classList.add("hidden");
    if (analyticsContainer) analyticsContainer.classList.add("hidden");
  });
}

if (btnRunWorkflowsUi) {
  btnRunWorkflowsUi.addEventListener("click", async () => {
    btnRunWorkflowsUi.disabled = true;
    btnRunWorkflowsUi.textContent = "⏳...";
    try {
      const res = await fetch("/api/workflows/run", { method: "POST" });
      const data = await res.json();
      if (data.total_triggered > 0) {
        appendMessage("assistant", `🤖 **Automatitzacions:** ${data.message}`);
      }
      await fetchDashboard();
    } catch (err) {
      console.error("Error executant cicle de fluxos:", err);
    } finally {
      btnRunWorkflowsUi.disabled = false;
      btnRunWorkflowsUi.textContent = "⟳ Comprovar";
    }
  });
}

// HELPER PER A ACTUALITZAR BADGES DE SERVEIS
function updateServiceBadge(badgeEl, statusVal) {
  if (!badgeEl) return;
  const val = (statusVal || "ONLINE").toUpperCase();
  badgeEl.textContent = val;
  let statusClass = "";
  if (val === "OFFLINE" || val === "ERROR") {
    statusClass = "offline";
  } else if (val === "STANDBY" || val.includes("CHECK")) {
    statusClass = "standby";
  }
  badgeEl.className = `chip-val badge ${statusClass}`.trim();
}

// HELPER PER A ACTUALITZAR PUNTS GLOWING DELS SERVEIS
function updateDot(dotId, statusVal) {
  const dot = document.getElementById(dotId);
  if (!dot) return;
  const val = (statusVal || "").toUpperCase();
  if (val === "OFFLINE" || val === "ERROR") {
    dot.className = "chip-dot offline";
  } else if (val === "STANDBY" || val.includes("CHECK")) {
    dot.className = "chip-dot standby";
  } else {
    dot.className = "chip-dot";
  }
}

// CONSULTAR ESTAT DEL SISTEMA I SESSIONS
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/system-status");
    if (!res.ok) return;
    const data = await res.json();

    if (data.services) {
      updateServiceBadge(statusBackend, data.services.backend);
      updateServiceBadge(statusDb, data.services.database);
      updateServiceBadge(statusNetwork, data.services.internet);
      updateServiceBadge(statusCalendar, data.services.calendar);
      updateServiceBadge(statusEmail, data.services.email_hub);
      updateServiceBadge(statusSpotify, data.services.spotify);
      updateServiceBadge(statusSearxng, data.services.searxng);
      updateServiceBadge(statusTelegram, data.services.telegram);

      // Actualització dels punts lluminosos HUD
      updateDot("dot-network", data.services.internet);
      updateDot("dot-backend", data.services.backend);
      updateDot("dot-db", data.services.database);
      updateDot("dot-calendar", data.services.calendar);
      updateDot("dot-email", data.services.email_hub);
      updateDot("dot-spotify", data.services.spotify);
      updateDot("dot-searxng", data.services.searxng);
      updateDot("dot-telegram", data.services.telegram);

      if (servicesSummaryPill) {
        if (data.services.internet === "OFFLINE") {
          servicesSummaryPill.textContent = "OFFLINE";
          servicesSummaryPill.className = "summary-pill warn";
        } else {
          servicesSummaryPill.textContent = "ONLINE";
          servicesSummaryPill.className = "summary-pill online";
        }
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

      const savedSession = localStorage.getItem("marc_session");
      if (savedSession && Array.from(sessionSelect.options).some(o => o.value === savedSession)) {
        sessionSelect.value = savedSession;
        currentSession = savedSession;
        currentSessionLabel.textContent = currentSession;
      }
    }
  } catch (err) {
    console.error("Error carregant estat del sistema:", err);
  }
}

// HELPER: CREAR ELEMENT DE CITA D'AGENDA
function createAgendaItemElement(ev, avuiStr, demaStr) {
  const evItem = document.createElement("div");
  evItem.className = "agenda-item clickable-card";
  evItem.setAttribute("title", "Fes clic per veure o modificar aquesta cita");

  let dataPart = "";
  let horaPart = ev.start_time;

  if (ev.start_time && ev.start_time.includes(" ")) {
    const parts = ev.start_time.split(" ");
    const rawDate = parts[0];
    const rawTime = parts[1];

    if (rawDate === avuiStr) {
      dataPart = "Avui · ";
    } else if (rawDate === demaStr) {
      dataPart = "Demà · ";
    } else {
      const dateSplits = rawDate.split("-");
      dataPart = (dateSplits.length === 3 ? `${dateSplits[2]}/${dateSplits[1]} · ` : `${rawDate} · `);
    }
    horaPart = rawTime;
  }

  const horaFi = (ev.end_time && ev.end_time.includes(" ")) ? ` - ${ev.end_time.split(" ")[1]}` : "";

  let displayTitle = ev.title || "(Sense títol)";
  let tagBadgeHtml = "";

  if (ev.tag) {
    const rawTag = ev.tag.replace(/[\[\]]/g, "");
    const tagClass = rawTag.toLowerCase().replace(/[^a-z0-9]/g, "-");
    tagBadgeHtml = `<span class="cal-badge tag-${tagClass}">${rawTag}</span>`;
    if (displayTitle.startsWith(ev.tag)) {
      displayTitle = displayTitle.substring(ev.tag.length).trim();
    }
  }

  evItem.innerHTML = `
    <div class="agenda-time">🕒 ${dataPart}${horaPart}${horaFi}</div>
    <div class="agenda-title">${tagBadgeHtml}${displayTitle}</div>
    ${ev.location ? `<div class="agenda-location">📍 ${ev.location}</div>` : ""}
  `;

  evItem.addEventListener("click", () => {
    openActivityDetailModal("event", ev);
  });

  return evItem;
}

// RENDERITZAR LLISTA D'AGENDA (AMB SUPORT DE PAGINACIÓ)
function renderAgendaList(events, totalEvents, allEvents) {
  if (events.length === 0) {
    agendaList.innerHTML = `<div class="empty-state">Sense cites a l'agenda. Clica a '+ Cita' per afegir-ne!</div>`;
    return;
  }

  agendaList.innerHTML = "";

  const ara = new Date();
  const avuiStr = ara.toISOString().split("T")[0];
  const dema = new Date();
  dema.setDate(dema.getDate() + 1);
  const demaStr = dema.toISOString().split("T")[0];

  events.forEach(ev => {
    const evItem = createAgendaItemElement(ev, avuiStr, demaStr);
    agendaList.appendChild(evItem);
  });

  // Si hi ha més cites que les mostrades inicialment, botó per desplegar-les
  if (totalEvents > events.length) {
    const loadMoreBtn = document.createElement("button");
    loadMoreBtn.className = "btn-load-more";
    loadMoreBtn.textContent = `+ MOSTRAR TOTS ELS ESDEVENIMENTS (${events.length} de ${totalEvents})`;
    loadMoreBtn.addEventListener("click", () => {
      renderAgendaList(allEvents, totalEvents, allEvents);
    });
    agendaList.appendChild(loadMoreBtn);
  }
}

// RENDERITZAR LLISTA DE TASQUES
function renderTasksList(tasks, totalTasks, allTasks) {
  if (tasks.length === 0) {
    tasksList.innerHTML = `<div class="empty-state">No hi ha cap tasca. Fes clic a '+ Nova' per afegir-ne una!</div>`;
    return;
  }

  tasksList.innerHTML = "";
  tasks.forEach(t => {
    const item = document.createElement("div");
    item.className = "task-item";

    const isDone = (t.status === "completada");
    const prioClass = (t.priority || "mitjana").toLowerCase();

    item.innerHTML = `
      <input type="checkbox" class="task-checkbox" ${isDone ? "checked" : ""} data-id="${t.id}" title="Completar o reobrir">
      <div class="task-content clickable-card" title="Fes clic per veure o editar la tasca">
        <span class="task-title ${isDone ? "completed" : ""}">${t.title}</span>
        <div class="task-meta">
          <span class="prio-badge ${prioClass}">${(t.priority || "mitjana").toUpperCase()}</span>
          ${t.due_date ? `<span class="task-due">📅 ${t.due_date}</span>` : ""}
        </div>
      </div>
    `;

    const chk = item.querySelector(".task-checkbox");
    chk.addEventListener("change", async (e) => {
      e.stopPropagation();
      await toggleTask(t.id);
    });

    const contentDiv = item.querySelector(".task-content");
    contentDiv.addEventListener("click", () => {
      openActivityDetailModal("task", t);
    });

    tasksList.appendChild(item);
  });

  if (totalTasks > tasks.length) {
    const loadMoreBtn = document.createElement("button");
    loadMoreBtn.className = "btn-load-more";
    loadMoreBtn.textContent = `+ MOSTRAR TOTES LES TASQUES (${tasks.length} de ${totalTasks})`;
    loadMoreBtn.addEventListener("click", () => {
      renderTasksList(allTasks, totalTasks, allTasks);
    });
    tasksList.appendChild(loadMoreBtn);
  }
}

// RENDERITZAR LLISTA DE FLUXOS ASÍNCRONS (AUTOMATITZACIONS)
function renderWorkflowsList(workflows) {
  if (!workflowsList) return;
  if (!workflows || workflows.length === 0) {
    workflowsList.innerHTML = `<div class="empty-state">No hi ha cap flux asíncron actiu. L'agent en crearà automàticament quan demanis una acció que requereixi esperar resposta o un termini!</div>`;
    return;
  }

  workflowsList.innerHTML = "";
  workflows.forEach(wf => {
    const item = document.createElement("div");
    item.className = "task-item clickable-card";
    item.setAttribute("title", "Fes clic per veure el diagrama interactiu d'aquest flux");
    
    let statusClass = "mitjana";
    let statusText = (wf.status || "pending").toUpperCase();
    if (wf.status === "completed") {
      statusClass = "baixa";
      statusText = "COMPLETAT";
    } else if (wf.status === "pending") {
      statusClass = "alta";
      statusText = "ESPERANT";
    } else if (wf.status === "waiting_user_review") {
      statusClass = "alta";
      statusText = "ATENCIÓ";
    }

    const cond = wf.trigger_condition || {};
    const triggerInfo = wf.trigger_type === "email_reply" 
      ? `📩 Espera correu: ${cond.sender || 'contacte'}`
      : `⏰ Data/Hora límit: ${cond.target_datetime || ''}`;

    item.innerHTML = `
      <div class="task-content" style="width:100%;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span class="task-title" style="font-weight:600;">${wf.title}</span>
          <span class="prio-badge ${statusClass}">${statusText}</span>
        </div>
        <div class="task-meta" style="margin-top:4px;">
          <span>${triggerInfo}</span>
          <span style="opacity:0.6;">Tipus: ${wf.workflow_type}</span>
        </div>
        ${wf.result_summary ? `<div style="font-size:0.75rem; color:var(--text-accent); margin-top:4px;">✓ ${wf.result_summary}</div>` : ""}
      </div>
    `;

    item.addEventListener("click", () => {
      openWorkflowDiagramModal(wf);
    });

    workflowsList.appendChild(item);
  });
}

// CONSULTAR I PINTAR DASHBOARD (AMB CAU D'ALTA VELOCITAT I PAGINACIÓ)
async function fetchDashboard(forceRefresh = false) {
  try {
    const url = `/api/dashboard?limit_agenda=15&limit_tasks=15${forceRefresh ? '&force_refresh=true' : ''}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    // 1. TASQUES
    const tasks = data.tasks || [];
    const allTasks = data.all_tasks || tasks;
    const totalTasks = data.total_tasks || tasks.length;
    const pendingCount = (data.stats && data.stats.pending_tasks !== undefined) 
      ? data.stats.pending_tasks 
      : tasks.filter(t => t.status === "pendent").length;
    taskCount.textContent = pendingCount;
    renderTasksList(tasks, totalTasks, allTasks);

    // 2. AGENDA
    const events = data.events || [];
    const allEvents = data.all_events || events;
    allDashboardEvents = allEvents; // Guardem en memòria per al calendari interactiu
    const totalEvents = data.total_events || events.length;
    agendaCount.textContent = totalEvents;
    agendaDateLabel.textContent = `Pròximes Cites (${totalEvents})`;
    renderAgendaList(events, totalEvents, allEvents);

    // Si el calendari interactiu està obert, refrescar-ne la vista
    if (calendarModal && !calendarModal.classList.contains("hidden")) {
      renderInteractiveCalendar();
    }

    // 3. FLUXOS ASÍNCRONS
    const workflows = data.workflows || [];
    const activeWfCount = data.active_workflows_count !== undefined 
      ? data.active_workflows_count 
      : workflows.filter(w => w.status === "pending").length;
    if (workflowsCount) workflowsCount.textContent = activeWfCount;
    renderWorkflowsList(workflows);

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

// MODAL DE CREACIÓ DE CITA D'AGENDA MANUAL
btnAddEventUi.addEventListener("click", () => {
  eventTitleInput.value = "";
  eventLocInput.value = "";
  eventDateInput.value = new Date().toISOString().split("T")[0];
  eventTimeInput.value = "10:00";
  eventDurationInput.value = "60";
  newEventModal.classList.remove("hidden");
});

eventModalCloseBtn.addEventListener("click", () => newEventModal.classList.add("hidden"));
eventCancelBtn.addEventListener("click", () => newEventModal.classList.add("hidden"));

newEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const titol = eventTitleInput.value.trim();
  const data = eventDateInput.value.trim();
  const hora = eventTimeInput.value.trim();
  const durada = parseInt(eventDurationInput.value || "60", 10);
  const lloc = eventLocInput.value.trim();

  if (!titol || !data || !hora) return;

  const dataHoraInici = `${data} ${hora}`;
  
  // Calculem fi
  const [h, m] = hora.split(":").map(Number);
  const dtFi = new Date();
  dtFi.setHours(h, m + durada, 0, 0);
  const horaFiStr = `${String(dtFi.getHours()).padStart(2, '0')}:${String(dtFi.getMinutes()).padStart(2, '0')}`;
  const dataHoraFi = `${data} ${horaFiStr}`;

  try {
    const res = await fetch("/api/events/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: titol,
        start_time: dataHoraInici,
        end_time: dataHoraFi,
        location: lloc
      })
    });
    if (res.ok) {
      newEventModal.classList.add("hidden");
      await fetchDashboard();
      appendMessage("M.A.R.C.", `📅 Nova cita programada a l'agenda: **${titol}** el **${dataHoraInici}**.`);
    }
  } catch (err) {
    alert("Error creant la cita: " + err.message);
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
  const loadingMsg = appendMessage("M.A.R.C.", "Processant comanda executiva...");

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

    // Reproducció per veu automàtica si està activat el mode veu
    if (voiceEnabled) {
      speakAssistantText(data.response);
    }

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

// FUNCIO PER CARREGAR L'HISTORIAL PERSISTENT DE LA SESSIÓ
async function loadSessionHistory(sessionId) {
  if (!sessionId) return;
  try {
    const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/messages`);
    if (!res.ok) return;
    const messages = await res.json();
    chatMessages.innerHTML = "";
    if (!messages || messages.length === 0) {
      appendMessage(
        "M.A.R.C.",
        "Hola! Sóc en **M.A.R.C.**, el teu secretari executiu i assistent personal autònom.\n\nEstic preparat per coordinar la teva agenda, tasques, correus i música. Com et puc ajudar?"
      );
    } else {
      messages.forEach(m => {
        const isUser = (m.sender || "").toLowerCase() === "user";
        appendMessage(isUser ? "USER" : "M.A.R.C.", m.message, isUser);
      });
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (err) {
    console.error("Error carregant l'historial de la sessió:", err);
  }
}

// CANVI I CREACIÓ DE SESSIONS
sessionSelect.addEventListener("change", async (e) => {
  currentSession = e.target.value;
  localStorage.setItem("marc_session", currentSession);
  if (currentSessionLabel) currentSessionLabel.textContent = currentSession;
  await loadSessionHistory(currentSession);
});

// --- SISTEMA DE GESTIÓ DE SESSIONS (MODAL NOU) ---
if (btnNewSession) {
  btnNewSession.addEventListener("click", () => {
    if (sessionNameInput) sessionNameInput.value = "";
    if (newSessionModal) {
      newSessionModal.classList.remove("hidden");
      if (sessionNameInput) sessionNameInput.focus();
    }
  });
}

if (sessionModalClose) {
  sessionModalClose.addEventListener("click", () => {
    if (newSessionModal) newSessionModal.classList.add("hidden");
  });
}

if (sessionModalCancel) {
  sessionModalCancel.addEventListener("click", () => {
    if (newSessionModal) newSessionModal.classList.add("hidden");
  });
}

if (newSessionForm) {
  newSessionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nom = sessionNameInput.value.trim();
    if (nom) {
      const cleanNom = nom.replace(/\s+/g, "_");
      if (!Array.from(sessionSelect.options).some(o => o.value === cleanNom)) {
        const opt = document.createElement("option");
        opt.value = cleanNom;
        opt.textContent = cleanNom;
        sessionSelect.appendChild(opt);
      }
      sessionSelect.value = cleanNom;
      currentSession = cleanNom;
      localStorage.setItem("marc_session", currentSession);
      if (currentSessionLabel) currentSessionLabel.textContent = currentSession;
      newSessionModal.classList.add("hidden");
      await loadSessionHistory(cleanNom);
    }
  });
}

// --- SISTEMA DE DETALL D'ACTIVITAT (TASCA / CITA) ---
function openActivityDetailModal(type, itemData) {
  currentSelectedActivity = { type, data: itemData };
  if (!activityDetailModal) return;

  // Mode visualització per defecte
  if (activityViewMode) activityViewMode.classList.remove("hidden");
  if (activityEditForm) activityEditForm.classList.add("hidden");

  if (type === "event") {
    let rawTag = itemData.tag ? itemData.tag.replace(/[\[\]]/g, "") : "CITA";
    let tagClass = rawTag.toLowerCase().replace(/[^a-z0-9]/g, "-");
    if (activityModalBadge) {
      activityModalBadge.textContent = rawTag;
      activityModalBadge.className = `diff-tag cal-badge tag-${tagClass}`;
    }
    let displayTitle = itemData.title || "(Sense títol)";
    if (itemData.tag && displayTitle.startsWith(itemData.tag)) {
      displayTitle = displayTitle.substring(itemData.tag.length).trim();
    }
    if (activityDetailTitle) activityDetailTitle.textContent = displayTitle;
    if (activityDetailMeta) {
      activityDetailMeta.textContent = itemData.calendar_id 
        ? `Calendari: ${itemData.calendar_id}` 
        : (itemData.synced ? "Sincronitzat amb Google Calendar" : "Calendari Local");
    }

    if (activityInfoTimeBox) activityInfoTimeBox.classList.remove("hidden");
    if (activityDetailTime) {
      activityDetailTime.textContent = `${itemData.start_time || 'N/A'}${itemData.end_time ? ' - ' + itemData.end_time : ''}`;
    }

    if (activityInfoLocBox) {
      activityInfoLocBox.classList.toggle("hidden", !itemData.location);
    }
    if (activityDetailLoc) activityDetailLoc.textContent = itemData.location || "Sense ubicació";

    if (activityDetailStatus) {
      activityDetailStatus.textContent = itemData.synced ? "✓ Connectat a Google Calendar" : "💾 Base de Dades Local";
    }

    if (activityDetailDesc) {
      activityDetailDesc.textContent = itemData.description || "Sense descripció addicional.";
    }

    if (btnActivityToggleDone) btnActivityToggleDone.classList.add("hidden");

    // Preparar formulari d'edició
    if (editEventFields) editEventFields.classList.remove("hidden");
    if (editTaskFields) editTaskFields.classList.add("hidden");
    if (editActivityTitle) editActivityTitle.value = itemData.title || "";
    if (editEventStart) editEventStart.value = (itemData.start_time || "").replace(" (Tot el dia)", "");
    if (editEventEnd) editEventEnd.value = (itemData.end_time || "").replace(" (Tot el dia)", "");
    if (editEventLoc) editEventLoc.value = itemData.location || "";
    if (editActivityDesc) editActivityDesc.value = itemData.description || "";

  } else if (type === "task") {
    const prio = (itemData.priority || "mitjana").toLowerCase();
    if (activityModalBadge) {
      activityModalBadge.textContent = `TASCA [${prio.toUpperCase()}]`;
      activityModalBadge.className = `diff-tag prio-badge ${prio}`;
    }
    if (activityDetailTitle) activityDetailTitle.textContent = itemData.title || "(Sense títol)";
    if (activityDetailMeta) activityDetailMeta.textContent = `Identificador: #${itemData.id}`;

    if (activityInfoTimeBox) activityInfoTimeBox.classList.toggle("hidden", !itemData.due_date);
    if (activityDetailTime) activityDetailTime.textContent = itemData.due_date ? `Data límit: ${itemData.due_date}` : "Sense data límit";

    if (activityInfoLocBox) activityInfoLocBox.classList.add("hidden");

    if (activityDetailStatus) {
      activityDetailStatus.textContent = (itemData.status === "completada") ? "🟢 Completada" : "⏳ Pendent";
    }

    if (activityDetailDesc) {
      activityDetailDesc.textContent = itemData.description || "Sense descripció addicional.";
    }

    if (btnActivityToggleDone) {
      btnActivityToggleDone.classList.remove("hidden");
      btnActivityToggleDone.textContent = (itemData.status === "completada") ? "↩ Reobrir Tasca" : "✓ Marcar Completada";
    }

    // Preparar formulari d'edició
    if (editEventFields) editEventFields.classList.add("hidden");
    if (editTaskFields) editTaskFields.classList.remove("hidden");
    if (editActivityTitle) editActivityTitle.value = itemData.title || "";
    if (editTaskPrio) editTaskPrio.value = prio;
    if (editTaskDue) editTaskDue.value = itemData.due_date || "";
    if (editActivityDesc) editActivityDesc.value = itemData.description || "";
  }

  activityDetailModal.classList.remove("hidden");
}

if (activityModalClose) {
  activityModalClose.addEventListener("click", () => {
    activityDetailModal.classList.add("hidden");
    currentSelectedActivity = null;
  });
}

if (btnActivityEdit) {
  btnActivityEdit.addEventListener("click", () => {
    if (activityViewMode) activityViewMode.classList.add("hidden");
    if (activityEditForm) activityEditForm.classList.remove("hidden");
  });
}

if (btnCancelEdit) {
  btnCancelEdit.addEventListener("click", () => {
    if (activityViewMode) activityViewMode.classList.remove("hidden");
    if (activityEditForm) activityEditForm.classList.add("hidden");
  });
}

if (btnActivityToggleDone) {
  btnActivityToggleDone.addEventListener("click", async () => {
    if (!currentSelectedActivity || currentSelectedActivity.type !== "task") return;
    const taskId = currentSelectedActivity.data.id;
    await toggleTask(taskId);
    activityDetailModal.classList.add("hidden");
  });
}

if (btnActivityDelete) {
  btnActivityDelete.addEventListener("click", async () => {
    if (!currentSelectedActivity) return;
    const isTask = (currentSelectedActivity.type === "task");
    const confirmMsg = isTask 
      ? `Segur que vols eliminar la tasca "${currentSelectedActivity.data.title}"?`
      : `Segur que vols eliminar l'esdeveniment "${currentSelectedActivity.data.title}" del calendari?`;
    
    if (!confirm(confirmMsg)) return;

    try {
      if (isTask) {
        await fetch("/api/tasks/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task_id: currentSelectedActivity.data.id })
        });
      } else {
        await fetch("/api/events/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            event_id: currentSelectedActivity.data.id,
            calendar_id: currentSelectedActivity.data.calendar_id || "primary"
          })
        });
      }
      activityDetailModal.classList.add("hidden");
      await fetchDashboard(true);
    } catch (err) {
      alert("Error eliminant l'activitat: " + err.message);
    }
  });
}

if (activityEditForm) {
  activityEditForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentSelectedActivity) return;

    try {
      if (currentSelectedActivity.type === "task") {
        await fetch("/api/tasks/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task_id: currentSelectedActivity.data.id,
            title: editActivityTitle.value.trim(),
            priority: editTaskPrio.value,
            due_date: editTaskDue.value,
            description: editActivityDesc.value.trim()
          })
        });
      } else {
        await fetch("/api/events/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            event_id: currentSelectedActivity.data.id,
            calendar_id: currentSelectedActivity.data.calendar_id || "primary",
            title: editActivityTitle.value.trim(),
            start_time: editEventStart.value.trim(),
            end_time: editEventEnd.value.trim(),
            location: editEventLoc.value.trim(),
            description: editActivityDesc.value.trim()
          })
        });
      }
      activityDetailModal.classList.add("hidden");
      await fetchDashboard(true);
    } catch (err) {
      alert("Error actualitzant l'activitat: " + err.message);
    }
  });
}

// --- SISTEMA DE CALENDARI INTERACTIU (GOOGLE CALENDAR STYLE) ---
const MONTH_NAMES_CA = [
  "GENER", "FEBRER", "MARÇ", "ABRIL", "MAIG", "JUNY",
  "JULIOL", "AGOST", "SETEMBRE", "OCTUBRE", "NOVEMBRE", "DESEMBRE"
];

function renderInteractiveCalendar() {
  if (!calendarGrid) return;
  calendarGrid.innerHTML = "";

  if (calendarMonthYearLabel) {
    calendarMonthYearLabel.textContent = `${MONTH_NAMES_CA[calMonth]} ${calYear}`;
  }

  // Agrupar esdeveniments per data YYYY-MM-DD
  const eventsByDate = {};
  allDashboardEvents.forEach(ev => {
    if (!ev.start_time) return;
    const dateKey = ev.start_time.split(" ")[0]; // YYYY-MM-DD
    if (!eventsByDate[dateKey]) eventsByDate[dateKey] = [];
    eventsByDate[dateKey].push(ev);
  });

  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

  // Primer dia del mes (Dilluns = 0 ... Diumenge = 6)
  const firstDayObj = new Date(calYear, calMonth, 1);
  const firstDay = firstDayObj.getDay();
  const startOffset = (firstDay === 0) ? 6 : firstDay - 1;

  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const daysInPrevMonth = new Date(calYear, calMonth, 0).getDate();

  // 1. Dies del mes anterior
  for (let i = startOffset - 1; i >= 0; i--) {
    const dayNum = daysInPrevMonth - i;
    const cell = document.createElement("div");
    cell.className = "calendar-day-cell other-month";
    cell.innerHTML = `<div class="calendar-day-num">${dayNum}</div>`;
    calendarGrid.appendChild(cell);
  }

  // 2. Dies del mes actual
  for (let d = 1; d <= daysInMonth; d++) {
    const dStr = String(d).padStart(2, '0');
    const mStr = String(calMonth + 1).padStart(2, '0');
    const dateKey = `${calYear}-${mStr}-${dStr}`;

    const cell = document.createElement("div");
    cell.className = "calendar-day-cell";
    if (dateKey === todayStr) cell.classList.add("today");

    cell.innerHTML = `<div class="calendar-day-num">${d}</div>`;

    const dayEvents = eventsByDate[dateKey] || [];
    dayEvents.forEach(ev => {
      const pill = document.createElement("div");
      let rawTag = ev.tag ? ev.tag.replace(/[\[\]]/g, "") : "LOCAL";
      let tagClass = rawTag.toLowerCase().replace(/[^a-z0-9]/g, "-");
      pill.className = `calendar-event-pill tag-${tagClass}`;

      let displayTitle = ev.title || "(Sense títol)";
      if (ev.tag && displayTitle.startsWith(ev.tag)) {
        displayTitle = displayTitle.substring(ev.tag.length).trim();
      }
      
      let hora = "";
      if (ev.start_time && ev.start_time.includes(" ")) {
        hora = ev.start_time.split(" ")[1] + " ";
      }

      pill.textContent = `${hora}${displayTitle}`;
      pill.title = `${ev.title}\n🕒 ${ev.start_time}${ev.end_time ? ' - ' + ev.end_time : ''}${ev.location ? '\n📍 ' + ev.location : ''}`;

      pill.addEventListener("click", (e) => {
        e.stopPropagation();
        openActivityDetailModal("event", ev);
      });

      cell.appendChild(pill);
    });

    // Clic a la casella per afegir cita directa en aquella data
    cell.addEventListener("click", () => {
      eventDateInput.value = dateKey;
      eventTitleInput.value = "";
      eventLocInput.value = "";
      eventTimeInput.value = "10:00";
      newEventModal.classList.remove("hidden");
    });

    calendarGrid.appendChild(cell);
  }

  // 3. Dies del mes següent per completar la quadrícula
  const totalCells = startOffset + daysInMonth;
  const nextMonthDays = (totalCells % 7 === 0) ? 0 : 7 - (totalCells % 7);
  for (let d = 1; d <= nextMonthDays; d++) {
    const cell = document.createElement("div");
    cell.className = "calendar-day-cell other-month";
    cell.innerHTML = `<div class="calendar-day-num">${d}</div>`;
    calendarGrid.appendChild(cell);
  }
}

if (btnOpenCalendarUi) {
  btnOpenCalendarUi.addEventListener("click", () => {
    calendarModal.classList.remove("hidden");
    renderInteractiveCalendar();
  });
}

if (calendarModalClose) {
  calendarModalClose.addEventListener("click", () => {
    calendarModal.classList.add("hidden");
  });
}

if (btnCalPrev) {
  btnCalPrev.addEventListener("click", () => {
    calMonth--;
    if (calMonth < 0) {
      calMonth = 11;
      calYear--;
    }
    renderInteractiveCalendar();
  });
}

if (btnCalNext) {
  btnCalNext.addEventListener("click", () => {
    calMonth++;
    if (calMonth > 11) {
      calMonth = 0;
      calYear++;
    }
    renderInteractiveCalendar();
  });
}

if (btnCalToday) {
  btnCalToday.addEventListener("click", () => {
    const now = new Date();
    calYear = now.getFullYear();
    calMonth = now.getMonth();
    renderInteractiveCalendar();
  });
}

if (btnCalAdd) {
  btnCalAdd.addEventListener("click", () => {
    btnAddEventUi.click();
  });
}

// --- SISTEMA DE DIAGRAMA D'ESTATS DE FLUXOS ASÍNCRONS ---
async function openWorkflowDiagramModal(wf) {
  currentSelectedWorkflow = wf;
  if (!workflowDiagramModal) return;

  if (wfModalTitle) wfModalTitle.textContent = wf.title || "Flux Asíncron";
  if (wfModalSubtitle) wfModalSubtitle.textContent = `Tipus: ${wf.workflow_type} · ID #${wf.id}`;

  const cond = wf.trigger_condition || {};
  let condStr = "";
  if (wf.trigger_type === "email_reply") {
    condStr = `Correu entrant de: ${cond.sender || 'contacte'}`;
    if (cond.subject_contains) condStr += ` (Assumpte conté: '${cond.subject_contains}')`;
  } else {
    condStr = `Data/hora objectiu: ${cond.target_datetime || 'N/A'}`;
  }

  if (wfModalDesc) {
    wfModalDesc.innerHTML = `
      <strong>Condició de Trigger:</strong> ${condStr}<br>
      <strong>Estat del cicle:</strong> <span class="prio-badge ${(wf.status === 'completed') ? 'baixa' : 'alta'}">${(wf.status || 'pending').toUpperCase()}</span>
      ${wf.result_summary ? `<div style="margin-top:6px; color:var(--accent-cyan);"><em>${wf.result_summary}</em></div>` : ''}
    `;
  }

  // Reset de classes a tots els nodes
  const allNodes = [nodeStart, nodeWaiting, nodeEval, nodeSuccess, nodeReview, nodeCounter];
  allNodes.forEach(node => {
    if (node) {
      node.classList.remove("active", "completed");
    }
  });

  const st = (wf.status || "pending").toLowerCase();

  if (st === "pending") {
    if (nodeStart) nodeStart.classList.add("completed");
    if (nodeWaiting) nodeWaiting.classList.add("active");
    if (wfInteractiveActions) wfInteractiveActions.classList.add("hidden");
  } else if (st === "waiting_user_review") {
    if (nodeStart) nodeStart.classList.add("completed");
    if (nodeWaiting) nodeWaiting.classList.add("completed");
    if (nodeEval) nodeEval.classList.add("completed");
    if (nodeReview) nodeReview.classList.add("active");
    if (nodeCounter) nodeCounter.classList.add("active");
    
    if (wfInteractiveActions) {
      wfInteractiveActions.classList.remove("hidden");
      if (wfDecisionMessage) {
        wfDecisionMessage.textContent = wf.result_summary || "El contacte proposa una data alternativa que requereix confirmació o contraproposta:";
      }
    }
  } else if (st === "completed") {
    if (nodeStart) nodeStart.classList.add("completed");
    if (nodeWaiting) nodeWaiting.classList.add("completed");
    if (nodeEval) nodeEval.classList.add("completed");
    if (nodeSuccess) nodeSuccess.classList.add("completed");
    if (wfInteractiveActions) wfInteractiveActions.classList.add("hidden");
  } else {
    if (nodeStart) nodeStart.classList.add("completed");
    if (wfInteractiveActions) wfInteractiveActions.classList.add("hidden");
  }

  await loadWorkflowLogs(wf.id);
  workflowDiagramModal.classList.remove("hidden");
}

async function loadWorkflowLogs(wfId) {
  if (!wfLogsList) return;
  wfLogsList.innerHTML = `<div class="loading">Carregant registre del flux...</div>`;
  try {
    const res = await fetch(`/api/workflows/${wfId}/logs`);
    if (!res.ok) {
      wfLogsList.innerHTML = `<div class="empty-state">Sense logs per mostrar.</div>`;
      return;
    }
    const logs = await res.json();
    if (logs.length === 0) {
      wfLogsList.innerHTML = `<div class="empty-state">Sense esdeveniments registrats encara.</div>`;
      return;
    }
    wfLogsList.innerHTML = "";
    logs.forEach(lg => {
      const row = document.createElement("div");
      row.className = "wf-log-row";
      row.innerHTML = `
        <span class="wf-log-time">${lg.timestamp || ''}</span>
        <span class="wf-log-action">${lg.action || ''}</span>
        <span class="wf-log-details">${lg.details || ''}</span>
      `;
      wfLogsList.appendChild(row);
    });
  } catch (err) {
    wfLogsList.innerHTML = `<div class="empty-state">Error carregant logs: ${err.message}</div>`;
  }
}

if (wfModalClose) {
  wfModalClose.addEventListener("click", () => {
    workflowDiagramModal.classList.add("hidden");
    currentSelectedWorkflow = null;
  });
}

if (btnWfAcceptAlt) {
  btnWfAcceptAlt.addEventListener("click", async () => {
    if (!currentSelectedWorkflow) return;
    try {
      const res = await fetch(`/api/workflows/${currentSelectedWorkflow.id}/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "accept_alternative" })
      });
      const data = await res.json();
      appendMessage("M.A.R.C.", `✅ **Flux actualitzat:** ${data.message}`);
      await fetchDashboard(true);
      await loadWorkflowLogs(currentSelectedWorkflow.id);
      if (nodeSuccess) nodeSuccess.classList.add("completed");
      if (wfInteractiveActions) wfInteractiveActions.classList.add("hidden");
    } catch (err) {
      alert("Error acceptant la data alternativa: " + err.message);
    }
  });
}

if (btnWfProposeNew) {
  btnWfProposeNew.addEventListener("click", async () => {
    if (!currentSelectedWorkflow) return;
    const contra = prompt("Escriu la nova contraproposta de dia/hora (ex: 'Dijous a les 11:30h us va bé?'):");
    if (!contra || !contra.trim()) return;

    try {
      const res = await fetch(`/api/workflows/${currentSelectedWorkflow.id}/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "propose_counter",
          counter_proposal_text: contra.trim()
        })
      });
      const data = await res.json();
      appendMessage("M.A.R.C.", `✉️ **Contraproposta enviada:** ${data.message}`);
      await fetchDashboard(true);
      await loadWorkflowLogs(currentSelectedWorkflow.id);
      if (wfInteractiveActions) wfInteractiveActions.classList.add("hidden");
      if (nodeCounter) nodeCounter.classList.add("completed");
    } catch (err) {
      alert("Error enviant la contraproposta: " + err.message);
    }
  });
}

if (btnWfCancel) {
  btnWfCancel.addEventListener("click", async () => {
    if (!currentSelectedWorkflow) return;
    if (!confirm("Vols cancel·lar definitivament aquest flux?")) return;

    try {
      const res = await fetch(`/api/workflows/${currentSelectedWorkflow.id}/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "cancel" })
      });
      const data = await res.json();
      appendMessage("M.A.R.C.", `🛑 **Flux cancel·lat:** ${data.message}`);
      await fetchDashboard(true);
      workflowDiagramModal.classList.add("hidden");
    } catch (err) {
      alert("Error cancel·lant el flux: " + err.message);
    }
  });
}

// LISTENERS GENERALS
if (btnSyncNow) {
  btnSyncNow.addEventListener("click", async () => {
    btnSyncNow.disabled = true;
    btnSyncNow.textContent = "⟳ SINCRONITZANT...";
    try {
      const res = await fetch("/api/sync");
      const data = await res.json();
      appendMessage("M.A.R.C.", data.message || "Sincronització completada.");
      await fetchDashboard(true);
      await fetchSystemStatus();
    } catch (err) {
      appendMessage("M.A.R.C.", `⚠️ Error en sincronitzar: ${err.message}`);
    } finally {
      btnSyncNow.disabled = false;
      btnSyncNow.textContent = "⟳ SINCRONITZA";
    }
  });
}

btnRefresh.addEventListener("click", () => {
  fetchDashboard(true);
  fetchSystemStatus();
});
modalApproveBtn.addEventListener("click", () => respondreAccio(true));
modalRejectBtn.addEventListener("click", () => respondreAccio(false));
modalCloseBtn.addEventListener("click", () => actionModal.classList.add("hidden"));

// ==========================================================================
// VEU (TTS & STT), TEMPS, FOCUS, DOCUMENTS I MÈTRIQUES
// ==========================================================================

// 1. SÍNTESI DE VEU (TTS)
let voiceEnabled = localStorage.getItem("marc_voice_enabled") !== "false"; // Actiu per defecte
if (btnVoiceToggle) {
  btnVoiceToggle.classList.toggle("active", voiceEnabled);
  btnVoiceToggle.textContent = voiceEnabled ? "🔊" : "🔇";
  btnVoiceToggle.addEventListener("click", () => {
    voiceEnabled = !voiceEnabled;
    localStorage.setItem("marc_voice_enabled", voiceEnabled ? "true" : "false");
    btnVoiceToggle.classList.toggle("active", voiceEnabled);
    btnVoiceToggle.textContent = voiceEnabled ? "🔊" : "🔇";
    if (!voiceEnabled && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  });
}

function cleanMarkdownForSpeech(md) {
  if (!md) return "";
  let clean = md;
  clean = clean.replace(/```[\s\S]*?```/g, " (bloc de codi) ");
  clean = clean.replace(/`([^`]+)`/g, "$1");
  clean = clean.replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");
  clean = clean.replace(/^[#>\-\*]+\s+/gm, "");
  clean = clean.replace(/[\*_~]/g, "");
  clean = clean.replace(/\n+/g, ". ").replace(/\s+/g, " ").trim();
  if (clean.length > 350) {
    const cut = clean.substring(0, 350);
    const lastDot = cut.lastIndexOf(".");
    clean = lastDot > 150 ? cut.substring(0, lastDot + 1) : cut + "...";
  }
  return clean;
}

function speakAssistantText(rawText) {
  if (!voiceEnabled || !("speechSynthesis" in window)) return;
  try {
    window.speechSynthesis.cancel();
    const cleaned = cleanMarkdownForSpeech(rawText);
    if (!cleaned) return;

    const utterance = new SpeechSynthesisUtterance(cleaned);
    const voices = window.speechSynthesis.getVoices();
    const bestVoice = voices.find(v => v.lang.startsWith("ca")) || 
                      voices.find(v => v.lang.startsWith("es"));
    if (bestVoice) {
      utterance.voice = bestVoice;
      utterance.lang = bestVoice.lang;
    } else {
      utterance.lang = "ca-ES";
    }
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn("Error en la síntesi de veu:", err);
  }
}

// 2. RECONEIXEMENT DE VEU (STT - WEB SPEECH RECOGNITION)
if (btnMic) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    btnMic.setAttribute("title", "Reconeixement de veu no disponible en aquest navegador");
    btnMic.style.opacity = "0.5";
    btnMic.addEventListener("click", () => {
      alert("El teu navegador no suporta Web Speech API (recomanat Google Chrome o Microsoft Edge).");
    });
  } else {
    const recognition = new SpeechRecognition();
    recognition.lang = "ca-ES";
    recognition.continuous = false;
    recognition.interimResults = false;
    let isListening = false;

    btnMic.addEventListener("click", () => {
      if (isListening) {
        recognition.stop();
      } else {
        try {
          recognition.start();
          isListening = true;
          btnMic.classList.add("listening");
          btnMic.textContent = "⏹️";
        } catch (err) {
          console.error("Error iniciant STT:", err);
          isListening = false;
          btnMic.classList.remove("listening");
          btnMic.textContent = "🎙️";
        }
      }
    });

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript && transcript.trim()) {
        userInput.value = transcript;
        enviarMissatgeXat(transcript);
      }
    };

    recognition.onerror = (event) => {
      console.warn("STT error:", event.error);
      isListening = false;
      btnMic.classList.remove("listening");
      btnMic.textContent = "🎙️";
    };

    recognition.onend = () => {
      isListening = false;
      btnMic.classList.remove("listening");
      btnMic.textContent = "🎙️";
    };
  }
}

// 3. BADGE DE METEOROLOGIA A GIRONA / CAMPUS MONTILIVI
async function fetchWeatherBadge() {
  if (!weatherBadge) return;
  try {
    const res = await fetch("/api/weather/girona");
    if (!res.ok) return;
    const data = await res.json();

    let icon = "⛅";
    const cond = (data.condition || "").toLowerCase();
    if (data.is_rainy || cond.includes("pluja") || cond.includes("plugim") || cond.includes("ruixat")) {
      icon = "🌧️";
    } else if (cond.includes("sol") || cond.includes("clar")) {
      icon = "☀️";
    } else if (cond.includes("boira")) {
      icon = "🌫️";
    } else if (cond.includes("tempesta")) {
      icon = "⛈️";
    } else if (cond.includes("neu")) {
      icon = "❄️";
    } else if (cond.includes("ennuvolat") || cond.includes("núvols")) {
      icon = "⛅";
    }

    if (weatherIcon) weatherIcon.textContent = icon;
    if (weatherText) weatherText.textContent = `Girona ${data.temperature_c}°C · ${data.condition}`;
    weatherBadge.setAttribute("title", `EPS Montilivi · ${data.condition}\nMàx: ${data.temp_max_c}°C / Mín: ${data.temp_min_c}°C\nVent: ${data.wind_speed_kmh} km/h | Precipitació: ${data.precipitation_mm} mm\n${data.rain_alert || ''}\nFes clic per consultar previsió al xat`);
  } catch (err) {
    console.warn("Error consultant el temps a Girona:", err);
  }
}

if (weatherBadge) {
  weatherBadge.addEventListener("click", () => {
    enviarMissatgeXat("Quin temps fa a Girona i quina és la previsió per a avui a l'EPS?");
  });
}

// 4. BOTÓ RÀPID MODE FOCUS (HUD)
if (btnFocusQuick) {
  btnFocusQuick.addEventListener("click", () => {
    enviarMissatgeXat("M.A.R.C., activa una sessió de mode focus de 50 minuts per a la feina del TFG amb música lo-fi.");
  });
}

// 5. GESTIÓ I CÀRREGA DE DOCUMENTS & ENUNCIATS PDF
if (btnUploadDoc && fileUploadInput) {
  btnUploadDoc.addEventListener("click", () => fileUploadInput.click());
}
if (btnUploadDocTab && fileUploadInput) {
  btnUploadDocTab.addEventListener("click", () => fileUploadInput.click());
}

if (fileUploadInput) {
  fileUploadInput.addEventListener("change", async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    appendMessage("USER", `📎 Pujant document per analitzar: **${file.name}**...`, true);
    const loadingMsg = appendMessage("M.A.R.C.", `📄 Extraient text i analitzant amb Gemini el document **${file.name}**...`);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", currentSession);

    try {
      const res = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      if (loadingMsg && loadingMsg.parentElement) {
        chatMessages.removeChild(loadingMsg.parentElement);
      }

      if (res.ok) {
        appendMessage("M.A.R.C.", data.analysis);
        if (voiceEnabled) {
          speakAssistantText(`He analitzat el document ${file.name}. T'he afegit les tasques i terminis clau.`);
        }
        await loadDocuments();
        await fetchDashboard();
      } else {
        appendMessage("M.A.R.C.", `⚠️ **Error en processar el document:** ${data.detail || data.message || 'Error desconegut'}`);
      }
    } catch (err) {
      if (loadingMsg && loadingMsg.parentElement) {
        chatMessages.removeChild(loadingMsg.parentElement);
      }
      appendMessage("M.A.R.C.", `⚠️ Error de càrrega: ${err.message}`);
    } finally {
      fileUploadInput.value = "";
    }
  });
}

async function loadDocuments() {
  if (!docsList) return;
  try {
    const res = await fetch("/api/documents");
    if (!res.ok) return;
    const docs = await res.json();
    if (docsCount) docsCount.textContent = docs.length;

    if (docs.length === 0) {
      docsList.innerHTML = `<div class="empty-state">No hi ha cap document ni enunciat carregat.<br>Fes clic a <b>+ Pujar PDF</b> per analitzar pràctiques o guies docents.</div>`;
      return;
    }

    docsList.innerHTML = "";
    docs.forEach(doc => {
      const card = document.createElement("div");
      card.className = "doc-card clickable-card";
      const dataStr = doc.uploaded_at ? doc.uploaded_at.split("T")[0] : "";

      card.innerHTML = `
        <div class="doc-info">
          <div class="doc-name">📄 ${doc.title}</div>
          <div class="doc-meta">${doc.filename} · ${doc.word_count} paraules ${dataStr ? '· ' + dataStr : ''}</div>
        </div>
        <button class="btn-micro" title="Preguntar sobre aquest document">ANALITZA</button>
      `;

      card.addEventListener("click", () => {
        enviarMissatgeXat(`M.A.R.C., mostra'm un resum i els lliurables pendents del document "${doc.title}".`);
      });

      docsList.appendChild(card);
    });
  } catch (err) {
    console.error("Error carregant documents:", err);
  }
}

// 6. TAULELL D'ANÀLISI EMPÍRICA I MÈTRIQUES PER AL TFG
async function loadAnalytics() {
  if (!analyticsContent) return;
  analyticsContent.innerHTML = `<div class="loading">Calculant mètriques del sistema...</div>`;

  try {
    const res = await fetch("/api/analytics/stats");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const stats = await res.json();

    const t = stats.tasks || {};
    const prio = t.by_priority || {};
    const wf = stats.workflows || {};
    const udg = stats.udg_emails || {};
    const focus = stats.focus_sessions || {};
    const chat = stats.chat_sessions || {};

    analyticsContent.innerHTML = `
      <div class="analytics-grid">
        <div class="metric-card accent-green">
          <div class="metric-label">Taxa Completesa Tasques</div>
          <div class="metric-val">${t.completion_rate}%</div>
          <div class="metric-sub">${t.completed} de ${t.total_tasks} tasques (${t.pending} pendents)</div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Prioritat de Feina</div>
          <div class="metric-val" style="font-size:1rem; display:flex; gap:6px; margin-top:4px;">
            <span class="prio-badge alta">Alta: ${prio.alta || 0}</span>
            <span class="prio-badge mitjana">Mitj: ${prio.mitjana || 0}</span>
            <span class="prio-badge baixa">Baixa: ${prio.baixa || 0}</span>
          </div>
          <div class="metric-sub">Distribució de tasques</div>
        </div>

        <div class="metric-card accent-purple">
          <div class="metric-label">Sessions de Focus TFG</div>
          <div class="metric-val">${focus.total_sessions}</div>
          <div class="metric-sub">Blocs de concentració profunda</div>
        </div>

        <div class="metric-card accent-yellow">
          <div class="metric-label">Correus UdG Processats</div>
          <div class="metric-val">${udg.emails_analyzed}</div>
          <div class="metric-sub">Filtre i extracció automàtica</div>
        </div>

        <div class="metric-card accent-green">
          <div class="metric-label">Taxa Èxit Automatitzacions</div>
          <div class="metric-val">${wf.success_rate}%</div>
          <div class="metric-sub">${wf.successful} de ${wf.total_workflows} fluxos completats</div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Sessions Conversacionals</div>
          <div class="metric-val">${chat.total_sessions}</div>
          <div class="metric-sub">Interaccions guardades a SQLite</div>
        </div>
      </div>
    `;
  } catch (err) {
    analyticsContent.innerHTML = `<div class="empty-state" style="color:var(--text-error);">Error carregant mètriques: ${err.message}</div>`;
  }
}

if (btnRefreshAnalytics) {
  btnRefreshAnalytics.addEventListener("click", () => loadAnalytics());
}

// INICIALITZACIÓ
(async function init() {
  if (currentSessionLabel) currentSessionLabel.textContent = currentSession;
  if (sessionSelect) {
    if (!Array.from(sessionSelect.options).some(o => o.value === currentSession)) {
      const opt = document.createElement("option");
      opt.value = currentSession;
      opt.textContent = currentSession;
      sessionSelect.appendChild(opt);
    }
    sessionSelect.value = currentSession;
  }
  // Executem en paral·lel per a màxima immediatesa i sense bloquejos mutus
  fetchSystemStatus();
  loadSessionHistory(currentSession);
  fetchDashboard();
  fetchWeatherBadge();
  loadDocuments();

  // Actualització suau periòdica de l'estat del sistema cada 30 segons
  setInterval(fetchSystemStatus, 30000);
  // Actualització meteorològica cada 10 minuts
  setInterval(fetchWeatherBadge, 600000);
})();