# PS28 - Viva Question Generator
Upload a project report PDF and get 15 viva questions with short answers, grouped Easy / Medium / Hard.
Runs fully offline with a local LLM (Ollama) - no API key.

## How to run
1. Install Ollama from https://ollama.com/download
2. `ollama pull llama3.1:8b`  (Ollama runs in the background after install)
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

## Tech
Python, Streamlit, PyPDF2, Llama 3.1 8B via Ollama
