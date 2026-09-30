"""AI Resume Analyzer & Job Matcher built with Streamlit and Groq."""

import json
import os
import re
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader


load_dotenv()

# Groq retired llama-3.3-70b-versatile for free/developer-tier users.
# GPT-OSS 20B is a current production model with JSON mode support.
DEFAULT_MODEL = "openai/gpt-oss-20b"
MODEL = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
REQUIRED_FIELDS = {
    "ats_score": 0,
    "candidate_summary": "",
    "matched_skills": [],
    "missing_skills": [],
    "partial_match_skills": [],
    "strengths": [],
    "weaknesses": [],
    "experience_match": "",
    "education_match": "",
    "project_match": "",
    "resume_improvements": [],
    "interview_questions": [],
}


st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_styles() -> None:
    """Apply a small, app-specific visual treatment."""
    st.markdown(
        """
        <style>
            .main-title { font-size: 2.5rem; font-weight: 750; margin-bottom: 0; }
            .subtitle { color: #64748b; font-size: 1.08rem; margin-bottom: 1.5rem; }
            .section-card {
                border: 1px solid rgba(128, 128, 128, .25); border-radius: 12px;
                padding: 1rem 1.2rem; min-height: 9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def extract_resume_text(uploaded_file: Any) -> str:
    """Extract all readable text from a text-based PDF upload."""
    try:
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise ValueError(f"Unable to read this PDF: {exc}") from exc

    return clean_text(text)


def clean_text(text: str) -> str:
    """Normalize whitespace before sending text to the model."""
    return re.sub(r"\s+", " ", text).strip()


def get_client() -> Groq:
    """Return an authenticated Groq client or a helpful configuration error."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Copy .env.example to .env and add your key."
        )
    return Groq(api_key=api_key)


def parse_json_response(content: str) -> dict[str, Any]:
    """Parse JSON returned by a model, tolerating accidental Markdown fencing."""
    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end < start:
            raise ValueError("The AI returned an invalid response. Please try again.")
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("The AI returned invalid JSON. Please try again.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("The AI response was not a JSON object. Please try again.")

    result = REQUIRED_FIELDS.copy()
    result.update({key: value for key, value in parsed.items() if key in result})
    try:
        result["ats_score"] = max(0, min(100, int(result["ats_score"])))
    except (TypeError, ValueError):
        result["ats_score"] = 0

    for key in (
        "matched_skills", "missing_skills", "partial_match_skills", "strengths",
        "weaknesses", "resume_improvements", "interview_questions",
    ):
        if not isinstance(result[key], list):
            result[key] = []
    return result


def analyze_resume(resume_text: str, job_description: str) -> dict[str, Any]:
    """Ask Groq for a structured, evidence-based resume comparison."""
    prompt = f"""
You are an expert technical recruiter and ATS resume analyzer. Compare the RESUME
with the JOB DESCRIPTION below. Use only evidence in those two texts; never invent
skills, qualifications, achievements, or years of experience.

Return JSON only, with exactly these keys:
{{
  "ats_score": 0,
  "candidate_summary": "",
  "matched_skills": [],
  "missing_skills": [],
  "partial_match_skills": [],
  "strengths": [],
  "weaknesses": [],
  "experience_match": "",
  "education_match": "",
  "project_match": "",
  "resume_improvements": [],
  "interview_questions": []
}}

Rules:
- ats_score is an integer from 0 through 100, representing a heuristic match—not a hiring decision.
- Include only skills explicit in both texts under matched_skills.
- Put important JD requirements absent from the resume under missing_skills.
- Use partial_match_skills only for related but weakly evidenced skills.
- Provide concise, actionable list items and exactly 10 interview_questions.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""
    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a professional ATS analyzer. Respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return parse_json_response(response.choices[0].message.content or "")


def generate_resume_tips(resume_text: str) -> str:
    """Generate general, practical resume suggestions from the uploaded resume."""
    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert technical resume coach."},
            {
                "role": "user",
                "content": (
                    "Review this resume and give eight concise, practical recommendations. "
                    "Cover ATS keywords, measurable achievements, skills, projects, and formatting. "
                    "Return only a numbered list.\n\nRESUME:\n" + resume_text
                ),
            },
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or "No tips were returned."


def display_list(items: list[Any], empty_message: str, marker: str = "•") -> None:
    """Render values as a simple readable list."""
    if not items:
        st.write(empty_message)
        return
    for item in items:
        st.write(f"{marker} {item}")


def render_report(result: dict[str, Any]) -> None:
    """Render all parts of the structured analysis report."""
    st.divider()
    st.header("Resume Analysis Report")
    score = result["ats_score"]
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("ATS Match Score", f"{score}%")
    metric_2.metric("Matched Skills", len(result["matched_skills"]))
    metric_3.metric("Missing Skills", len(result["missing_skills"]))
    st.progress(score / 100)
    st.caption("This score is an AI-assisted heuristic, not an employment decision.")

    st.subheader("Candidate Summary")
    st.write(result["candidate_summary"] or "No summary available.")

    matched_column, missing_column = st.columns(2)
    with matched_column:
        st.subheader("Matched Skills")
        display_list(result["matched_skills"], "No strong matches identified.", "✓")
    with missing_column:
        st.subheader("Missing Skills")
        display_list(result["missing_skills"], "No major missing skills identified.")

    st.subheader("Partial Match Skills")
    display_list(result["partial_match_skills"], "No partial matches identified.", "~")

    strengths_column, weaknesses_column = st.columns(2)
    with strengths_column:
        st.subheader("Strengths")
        display_list(result["strengths"], "No strengths identified.", "✓")
    with weaknesses_column:
        st.subheader("Weaknesses")
        display_list(result["weaknesses"], "No weaknesses identified.")

    st.subheader("Experience Match")
    st.write(result["experience_match"] or "Not available.")
    st.subheader("Education Match")
    st.write(result["education_match"] or "Not available.")
    st.subheader("Project Match")
    st.write(result["project_match"] or "Not available.")

    st.subheader("Resume Improvement Recommendations")
    display_list(result["resume_improvements"], "No recommendations available.")
    st.subheader("AI-Generated Interview Questions")
    for number, question in enumerate(result["interview_questions"], start=1):
        st.write(f"{number}. {question}")


def main() -> None:
    apply_styles()
    st.markdown('<div class="main-title">AI Resume Analyzer & Job Matcher</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Compare a PDF resume with a job description using Generative AI.</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("About")
        st.write("Upload a text-based PDF resume, paste a job description, and receive an AI-assisted fit report.")
        st.divider()
        st.subheader("Technology")
        st.write("Python · Streamlit · Groq · PyPDF")
        st.divider()
        st.caption(f"Model: `{MODEL}`")

    upload_column, description_column = st.columns(2)
    with upload_column:
        st.subheader("1. Upload Resume")
        uploaded_file = st.file_uploader("Upload a PDF resume", type=["pdf"])
    with description_column:
        st.subheader("2. Job Description")
        job_description = st.text_area(
            "Paste the complete job description", height=260,
            placeholder="Include responsibilities, required skills, and preferred qualifications...",
        )

    st.divider()
    if st.button("Analyze Resume", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.warning("Please upload a resume PDF.")
        elif not job_description.strip():
            st.warning("Please enter a job description.")
        else:
            with st.spinner("Reading and analyzing your resume..."):
                try:
                    resume_text = extract_resume_text(uploaded_file)
                    if len(resume_text) < 100:
                        raise ValueError("Very little text was extracted. Upload a text-based, selectable-text PDF.")
                    st.session_state.analysis = analyze_resume(resume_text, clean_text(job_description))
                    st.session_state.resume_text = resume_text
                except Exception as exc:
                    st.error(str(exc))

    if "analysis" in st.session_state:
        render_report(st.session_state.analysis)
        with st.expander("Generate General Resume Improvement Tips"):
            if st.button("Generate Tips"):
                with st.spinner("Generating recommendations..."):
                    try:
                        st.write(generate_resume_tips(st.session_state.resume_text))
                    except Exception as exc:
                        st.error(f"Unable to generate tips: {exc}")

    st.divider()
    st.caption("AI Resume Analyzer | Python + Streamlit + Groq")


if __name__ == "__main__":
    main()
