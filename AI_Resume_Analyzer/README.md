# AI Resume Analyzer & Job Matcher

A Streamlit application that compares a PDF resume against a job description with Groq. It generates an ATS-style match score, skill-gap analysis, strengths, weaknesses, resume improvements, and interview questions.

## Features

- Upload a text-based PDF resume
- Paste any job description
- Get a structured, AI-assisted ATS-style report
- See matched, missing, and partial-match skills
- Generate targeted improvement recommendations and interview questions
- Keep the Groq API key outside source control

## Setup

1. Create and activate a virtual environment.

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`, then replace the placeholder with a Groq API key from the [Groq Console](https://console.groq.com/keys).

   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```

4. Run the app.

   ```powershell
   streamlit run app.py
   ```

Open the local URL Streamlit displays (normally `http://localhost:8501`).

## Deploy on Streamlit Community Cloud

1. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) with the GitHub account that can access this repository.
2. Choose **Create app**, then select repository `Ashish00172/Ai-Resume_Analyzer`, branch `main`, and main file path `AI_Resume_Analyzer/app.py`.
3. In **Advanced settings → Secrets**, add your Groq key:

   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```

4. Choose **Deploy**. The app will install dependencies from `AI_Resume_Analyzer/requirements.txt`.

Keep the real API key in Community Cloud secrets; do not commit it to GitHub. After the first deployment, pushes to `main` update the app automatically.

## Notes

- Use a text-based PDF. Scanned PDFs need OCR before they can be analyzed.
- The reported ATS score is a heuristic to help improve a resume; it is not a hiring recommendation or employment decision.
- The default Groq model is `openai/gpt-oss-20b`. If your account cannot access it, set `GROQ_MODEL` in `.env` to another model your account supports.

## Project layout

```text
AI_Resume_Analyzer/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
