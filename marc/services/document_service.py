import os
import json
from datetime import datetime
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = os.path.join(BASE_DIR, "marc", "data", "documents")
os.makedirs(DOCS_DIR, exist_ok=True)

def extract_text_from_file(filepath: str) -> str:
    """Extreu el text d'un fitxer PDF, TXT o MD."""
    if not os.path.exists(filepath):
        return ""
    if filepath.lower().endswith(".pdf"):
        try:
            reader = PdfReader(filepath)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- PÀGINA {i+1} ---\n" + page_text)
            return "\n\n".join(text_parts)
        except Exception as e:
            return f"Error llegint PDF: {e}"
    else:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error llegint fitxer: {e}"

def list_stored_documents() -> list:
    """Llista els fitxers emmagatzemats a marc/data/documents amb metadades enriquides."""
    if not os.path.exists(DOCS_DIR):
        return []
    docs = []
    for fname in os.listdir(DOCS_DIR):
        full_p = os.path.join(DOCS_DIR, fname)
        if os.path.isfile(full_p):
            sz_kb = round(os.path.getsize(full_p) / 1024, 1)
            mod_dt = datetime.fromtimestamp(os.path.getmtime(full_p)).strftime("%Y-%m-%d %H:%M")
            base, ext = os.path.splitext(fname)
            word_count = 0
            try:
                txt = extract_text_from_file(full_p)
                word_count = len(txt.split()) if txt else 0
            except Exception:
                pass
            docs.append({
                "title": base.replace("_", " ").replace("-", " ").title(),
                "filename": fname,
                "extension": ext.lower(),
                "size_kb": sz_kb,
                "word_count": word_count,
                "modified": mod_dt,
                "uploaded_at": mod_dt,
                "path": full_p
            })
    return docs

def analyze_document_with_ai(filename_or_path: str) -> dict:
    """
    Analitza un document acadèmic o professional (ex: enunciat de pràctica, reglament TFG, guia docent)
    mitjançant IA (Gemini), extreu requisits, terminis, criteris i recomana tasques.
    """
    if not os.path.isabs(filename_or_path):
        target_path = os.path.join(DOCS_DIR, filename_or_path)
        if not os.path.exists(target_path):
            target_path = filename_or_path
    else:
        target_path = filename_or_path
        
    if not os.path.exists(target_path):
        return {"success": False, "error": f"No s'ha trobat el fitxer: {filename_or_path}"}
        
    doc_text = extract_text_from_file(target_path)
    if not doc_text or len(doc_text.strip()) < 10:
        return {"success": False, "error": "El document és buit o no conté text llegible."}
        
    snippet = doc_text[:150000]
    
    prompt = f"""Ets en M.A.R.C., el secretari executiu i assistent d'en Marc a la universitat (UdG - EPS).
Has d'analitzar exhaustivament aquest document (enunciat de pràctica, projecte o guia acadèmica) i extreure'n tota la informació clau.

NOM DEL FITXER: {os.path.basename(target_path)}
CONTINGUT DEL DOCUMENT:
\"\"\"{snippet}\"\"\"

INSTRUCCIONS DE RESPOSTA:
Retorna UNICAMENT un objecte JSON amb aquest format exacte (sense blocs de text extra):
{{
  "title": "Títol o matèria del document (ex: SGBD - Pràctica 2, Memòria TFG)",
  "summary": "Resum executiu en català dels objectius i abast del treball",
  "deliverables": [
    "Lliurables exigits (ex: Memòria PDF, codi Python, scripts SQL, arxiu ZIP)"
  ],
  "deadlines": [
    {{
      "concept": "Data de lliurament / Defensa",
      "date": "YYYY-MM-DD (o descripció temporal)",
      "time": "HH:MM (o null)"
    }}
  ],
  "evaluation_criteria": [
    "Criteris o percentatges d'avaluació clau"
  ],
  "recommended_tasks": [
    {{
      "title": "Títol de la tasca per afegir a To-Do",
      "priority": "alta",
      "due_date": "YYYY-MM-DD"
    }}
  ]
}}
"""
    try:
        from marc.services.workflow_engine import _get_workflow_evaluation
        analysis = _get_workflow_evaluation(prompt)
        return {
            "success": True,
            "filename": os.path.basename(target_path),
            "analysis": analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def format_document_analysis_markdown(res: dict) -> str:
    """Transforma el diccionari d'anàlisi de document en un informe net en Markdown."""
    if not res.get("success"):
        return f"⚠️ No s'ha pogut analitzar el document: {res.get('error', 'Error desconegut')}"
    a = res.get("analysis", {})
    titol = a.get("title", res.get("filename", "Document"))
    resum = a.get("summary", "")
    lliurables = "\n".join([f"- {item}" for item in a.get("deliverables", [])]) or "- Cap detallat"
    terminis = "\n".join([f"- **{d.get('concept')}:** {d.get('date')} {d.get('time') or ''}" for d in a.get("deadlines", [])]) or "- Sense terminis explícits"
    criteris = "\n".join([f"- {c}" for c in a.get("evaluation_criteria", [])]) or "- Criteris generals"
    tasques = "\n".join([f"- **[{t.get('priority', 'alta').upper()}]** {t.get('title')} (Data límit: {t.get('due_date') or 'Sense data'})" for t in a.get("recommended_tasks", [])]) or "- Cap tasca suggerida"

    return (
        f"### 📄 Anàlisi Intel·ligent: **{titol}**\n\n"
        f"**📋 Resum executiu:**\n{resum}\n\n"
        f"**📦 Lliurables exigits:**\n{lliurables}\n\n"
        f"**⏰ Terminis i Dates Clau:**\n{terminis}\n\n"
        f"**🎯 Criteris d'Avaluació:**\n{criteris}\n\n"
        f"**✅ Tasques Recomanades per a To-Do:**\n{tasques}\n\n"
        f"---\n"
        f"*Les tasques i terminis clau s'han extret i integrat automàticament a la teva llista de feina.*"
    )

