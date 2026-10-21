import os
import json
import groq
from datetime import datetime, timezone
from dotenv import load_dotenv

from marc.core.db import (
    db_get_workflows,
    db_get_workflow,
    db_update_workflow,
    db_add_workflow_log,
    db_add_task,
    db_get_emails,
    db_add_chat_message
)
from marc.services.calendar_service import add_calendar_event

load_dotenv()

def _get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return groq.Groq(api_key=api_key)

def evaluate_email_against_workflow(email_item: dict, workflow: dict) -> dict:
    """
    Avalua mitjançant IA si un correu rebut compleix les condicions d'un flux asíncron pendent
    i determina quina acció executiva cal emprendre.
    """
    client = _get_groq_client()
    if not client:
        return {"is_match": False, "intent": "no_llm", "confidence": 0.0}

    sender = email_item.get("sender", "")
    subject = email_item.get("subject", "")
    body = email_item.get("body", "")

    wf_title = workflow.get("title", "")
    wf_type = workflow.get("workflow_type", "")
    cond = workflow.get("trigger_condition", {})
    action_cfg = workflow.get("action_config", {})
    context_data = workflow.get("context_data", {})

    prompt = f"""
Ets el motor d'orquestració de fluxos asíncrons de M.A.R.C., un assistent executiu autònom.
Tens un flux de treball en estat d'espera i s'ha rebut un nou correu. Has d'analitzar si el correu respon al flux i quina decisió prendre.

DADES DEL FLUX DE TREBALL EN ESPERA:
- Títol del flux: {wf_title}
- Tipus de flux: {wf_type}
- Condicions d'espera / Trigger: {json.dumps(cond, ensure_ascii=False)}
- Objectiu / Acció a prendre: {json.dumps(action_cfg, ensure_ascii=False)}
- Context previ: {json.dumps(context_data, ensure_ascii=False)}

CORREU ELECTRÒNIC REBUT:
- Remitent: {sender}
- Assumpte: {subject}
- Cos del missatge:
\"\"\"{body}\"\"\"

INSTRUCCIONS DE RESPOSTA:
Retorna UNICAMENT un objecte JSON amb aquest format exacte (sense blocs de text extra):
{{
  "is_match": true | false,
  "intent": "confirmed" | "rejected" | "alternative_proposed" | "question" | "unrelated",
  "confidence": 0.0 a 1.0,
  "extracted_data": {{
    "confirmed_date": "YYYY-MM-DD HH:MM (o null)",
    "duration_minutes": 60,
    "location": "lloc o online",
    "notes": "observacions clau"
  }},
  "explanation": "Breu explicació en català de per què coincideix i què diu el remitent",
  "recommended_action": "complete_and_execute" | "create_followup_task" | "continue_waiting" | "ignore"
}}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        raw_text = response.choices[0].message.content
        return json.loads(raw_text)
    except Exception as e:
        print(f"[Workflow Engine LLM Error]: {e}")
        return {"is_match": False, "intent": "error", "error": str(e), "confidence": 0.0}

def execute_workflow_action(workflow: dict, evaluation: dict, trigger_item: dict) -> dict:
    """Executa l'acció configurada per al flux quan el trigger es compleix."""
    wf_id = workflow["id"]
    action_type = workflow.get("action_type", "")
    action_cfg = workflow.get("action_config", {})
    context_data = workflow.get("context_data", {})
    extracted = evaluation.get("extracted_data", {})

    result_summary = ""
    success = False

    # CAS A: L'altra persona ha confirmat la reunió o esdeveniment
    if evaluation.get("intent") == "confirmed" or action_type == "schedule_event":
        data_inici = extracted.get("confirmed_date") or context_data.get("proposed_datetime") or action_cfg.get("start_time")
        durada = extracted.get("duration_minutes") or action_cfg.get("duration_minutes") or 60
        titol_event = action_cfg.get("event_title") or f"Reunió amb {trigger_item.get('sender', 'contacte')}"
        lloc = extracted.get("location") or action_cfg.get("location") or "Despatx / Online"

        if data_inici:
            # Calculem fi si tenim data inici
            try:
                dt_inici = datetime.strptime(data_inici[:16], "%Y-%m-%d %H:%M")
                from datetime import timedelta
                dt_fi = dt_inici + timedelta(minutes=int(durada))
                data_fi = dt_fi.strftime("%Y-%m-%d %H:%M")
            except Exception:
                data_fi = data_inici

            event_id = add_calendar_event(
                title=titol_event,
                start_time=data_inici,
                end_time=data_fi,
                location=lloc,
                description=f"Programat automàticament pel flux asíncron #{wf_id}. Notes: {extracted.get('notes', '')}"
            )
            result_summary = f"Esdeveniment programat amb èxit: '{titol_event}' el {data_inici} ({durada} min)."
            success = True
            
            db_add_workflow_log(wf_id, "action_executed", result_summary)
            db_update_workflow(wf_id, status="completed", result_summary=result_summary)
            
            # Notifiquem al xat de l'usuari
            db_add_chat_message("sessio_per_defecte", "assistant", f"🤖 **Flux Asíncron Completat:**\n{result_summary}\n*Motiu:* {evaluation.get('explanation', '')}")
        else:
            result_summary = "Confirmació detectada, però no s'ha pogut determinar la data exacta."
            db_add_task(
                title=f"Fixar data final reunió: {workflow['title']}",
                priority="alta",
                description=f"El remitent ha acceptat, però cal acordar hora exacta. Correu: {trigger_item.get('body', '')[:200]}"
            )
            db_update_workflow(wf_id, status="waiting_user_review", result_summary=result_summary)
            db_add_workflow_log(wf_id, "needs_manual_time", result_summary)

    # CAS B: Proposa una data alternativa o rebutja
    elif evaluation.get("intent") in ("alternative_proposed", "rejected", "question"):
        task_title = f"Proposta alternativa de {trigger_item.get('sender')}: {workflow['title']}"
        desc = f"Motiu: {evaluation.get('explanation')}\nData alternativa: {extracted.get('confirmed_date', 'No especificada')}\nNotes: {extracted.get('notes', '')}"
        
        db_add_task(title=task_title, priority="alta", description=desc)
        result_summary = f"S'ha generat una tasca d'atenció per a l'usuari: '{task_title}'."
        success = True
        
        db_update_workflow(wf_id, status="waiting_user_review", result_summary=result_summary, context_update={"last_evaluation": evaluation})
        db_add_workflow_log(wf_id, "alternative_received", result_summary)
        db_add_chat_message("sessio_per_defecte", "assistant", f"⚠️ **Atenció al Flux Asíncron #{wf_id}:**\n{desc}")

    # CAS C: Acció personalitzada genèrica
    elif action_type == "create_task":
        task_title = action_cfg.get("task_title") or f"Seguiment: {workflow['title']}"
        db_add_task(title=task_title, priority=action_cfg.get("priority", "mitjana"), description=evaluation.get("explanation", ""))
        result_summary = f"Tasca de seguiment creada: '{task_title}'."
        success = True
        db_update_workflow(wf_id, status="completed", result_summary=result_summary)
        db_add_workflow_log(wf_id, "task_created", result_summary)

    else:
        result_summary = f"Correu processat amb intent '{evaluation.get('intent')}'. Sense acció immediata."
        db_add_workflow_log(wf_id, "evaluated_no_action", result_summary)

    return {"success": success, "result_summary": result_summary}

def process_email_triggers(emails: list = None) -> list:
    """
    Comprova tots els fluxos asíncrons que esperen resposta de correu ('email_reply').
    Si troba correspondència, avalua amb IA i executa l'acció.
    """
    pending_workflows = db_get_workflows(status="pending", trigger_type="email_reply")
    if not pending_workflows:
        return []

    if emails is None:
        emails = db_get_emails(folder="inbox", limit=15)

    results = []

    for wf in pending_workflows:
        cond = wf.get("trigger_condition", {})
        expected_sender = cond.get("sender", "").lower().strip()
        expected_subject_kw = cond.get("subject_contains", "").lower().strip()

        for em in emails:
            em_sender = em.get("sender", "").lower()
            em_subject = em.get("subject", "").lower()

            # Filtre previ ràpid si hi ha remitent o assumpte especificat
            sender_match = (not expected_sender) or (expected_sender in em_sender)
            subject_match = (not expected_subject_kw) or (expected_subject_kw in em_subject)

            if sender_match and subject_match:
                db_add_workflow_log(wf["id"], "candidate_found", f"Revisant correu de '{em.get('sender')}' amb assumpte '{em.get('subject')}'")
                
                # Avaluació intel·ligent amb LLM
                eval_res = evaluate_email_against_workflow(em, wf)
                
                if eval_res.get("is_match") and eval_res.get("confidence", 0) >= 0.6:
                    exec_res = execute_workflow_action(wf, eval_res, em)
                    results.append({
                        "workflow_id": wf["id"],
                        "workflow_title": wf["title"],
                        "evaluation": eval_res,
                        "execution": exec_res
                    })
                    # Un cop resolt per a aquest correu, no cal provar més correus per a aquest mateix flux en aquesta passada
                    break

    return results

def process_datetime_triggers() -> list:
    """Comprova els fluxos que tenen un trigger basat en arribar a una data o hora límit."""
    pending_workflows = db_get_workflows(status="pending", trigger_type="datetime")
    if not pending_workflows:
        return []

    ara_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    results = []

    for wf in pending_workflows:
        cond = wf.get("trigger_condition", {})
        target_dt = cond.get("target_datetime") or cond.get("deadline")
        if target_dt and target_dt <= ara_str:
            action_type = wf.get("action_type")
            action_cfg = wf.get("action_config", {})
            
            summary = ""
            if action_type == "create_task":
                t_title = action_cfg.get("task_title", f"Termini assolit: {wf['title']}")
                db_add_task(title=t_title, priority="alta", description=action_cfg.get("description", ""))
                summary = f"Termini complert. Tasca creada: '{t_title}'."
            else:
                summary = f"Trigger temporal assolit per a '{wf['title']}'."
                db_add_chat_message("sessio_per_defecte", "assistant", f"⏰ **Recordatori de Flux Asíncron:**\n{summary}")

            db_update_workflow(wf["id"], status="completed", result_summary=summary)
            db_add_workflow_log(wf["id"], "time_trigger_fired", summary)
            results.append({"workflow_id": wf["id"], "summary": summary})

    return results

def run_workflow_cycle() -> dict:
    """Executa un cicle complet d'avaluació de tots els fluxos asíncrons actius."""
    email_results = process_email_triggers()
    time_results = process_datetime_triggers()
    total_triggered = len(email_results) + len(time_results)
    
    return {
        "total_triggered": total_triggered,
        "email_workflows": email_results,
        "time_workflows": time_results,
        "message": f"Cicle completat: {total_triggered} fluxos han avançat o completat el seu cicle."
    }
