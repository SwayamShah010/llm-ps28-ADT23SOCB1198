"""PS28 - Viva Question Generator (offline, no API key)
Upload a project report PDF -> extract text -> local Ollama model generates
exactly 15 viva questions (5 Easy, 5 Medium, 5 Hard) with short answers.
"""
import json

import requests
import streamlit as st
from PyPDF2 import PdfReader

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"   # your local model (see: ollama list)
MAX_CHARS = 12000       # report text sent to the model
PER_LEVEL = 5           # 5 x 3 levels = 15 questions

LEVELS = {
    "Easy": "basic concepts, definitions and what the project does",
    "Medium": "design and implementation choices, tools and how modules work",
    "Hard": "limitations, alternatives ('why not X?'), testing and future improvements",
}

PROMPT = """You are an examiner conducting a viva for a final-year student project.
Using ONLY the project report text below, write exactly {n} {level} viva questions
({focus}), each with a short model answer of 2-3 sentences.

Return ONLY JSON in this exact format:
{{"questions": [{{"question": "...", "answer": "..."}}]}}

REPORT TEXT:
{text}
"""


def extract_text(pdf_file) -> str:
    reader = PdfReader(pdf_file)
    return "\n".join((p.extract_text() or "") for p in reader.pages).strip()


def call_ollama(text: str, level: str) -> list[dict]:
    payload = {
        "model": MODEL,
        "prompt": PROMPT.format(n=PER_LEVEL, level=level, focus=LEVELS[level], text=text[:MAX_CHARS]),
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.4},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=600)
    r.raise_for_status()
    data = json.loads(r.json()["response"])
    return [
        {"difficulty": level, "question": q["question"], "answer": q["answer"]}
        for q in data.get("questions", [])
        if isinstance(q, dict) and "question" in q and "answer" in q
    ]


def get_level(text: str, level: str) -> list[dict]:
    """Ask the model; retry once if it returned too few or bad JSON."""
    items = []
    for _ in range(2):
        try:
            items = call_ollama(text, level)
        except json.JSONDecodeError:
            items = []
        if len(items) >= PER_LEVEL:
            break
    return items[:PER_LEVEL]


def to_text(items) -> str:
    return "\n".join(
        f"Q{i} [{q['difficulty']}] {q['question']}\nAns: {q['answer']}\n"
        for i, q in enumerate(items, 1)
    )


st.set_page_config(page_title="Viva Question Generator", page_icon="🎓")
st.title("🎓 Viva Question Generator")
st.caption(f"Generates 15 viva questions offline using {MODEL} via Ollama - no API key.")

pdf = st.file_uploader("Upload project report (PDF)", type="pdf")

if st.button("Generate 15 viva questions", type="primary"):
    if not pdf:
        st.error("Please upload a PDF report.")
    else:
        text = extract_text(pdf)
        if len(text) < 200:
            st.error("Couldn't extract enough text (scanned PDF?). Use a text-based PDF.")
        else:
            results = []
            try:
                bar = st.progress(0.0, text="Starting...")
                for i, level in enumerate(LEVELS):
                    bar.progress(i / 3, text=f"Generating {level} questions... (may take a few minutes)")
                    results += get_level(text, level)
                bar.progress(1.0, text="Done")
                st.session_state["qs"] = results
            except requests.exceptions.ConnectionError:
                st.error("Can't reach Ollama. Start it (open the Ollama app or run: ollama serve).")
            except Exception as e:
                st.error(f"Error: {e}")

if st.session_state.get("qs"):
    qs = st.session_state["qs"]
    st.success(f"Generated {len(qs)} questions")
    for level, icon in [("Easy", "🟢"), ("Medium", "🟡"), ("Hard", "🔴")]:
        group = [q for q in qs if q["difficulty"] == level]
        st.subheader(f"{icon} {level} ({len(group)})")
        for q in group:
            with st.expander(q["question"]):
                st.write(q["answer"])
    st.download_button("Download as .txt", to_text(qs), "viva_questions.txt")
