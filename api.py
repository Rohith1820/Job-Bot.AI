# ─────────────────────────────────────────────────────────────────────────────
# utils/api.py  —  Claude AI resume tailoring
# ─────────────────────────────────────────────────────────────────────────────
import re
import anthropic
import streamlit as st


def tailor_resume(base_resume, jd, role, company, name, email, phone):
    """Call Claude API to tailor resume. Returns dict {tailored, score}."""
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .streamlit/secrets.toml")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=1500,
        system=f"""You are an expert ATS resume optimizer. Given a base resume and job description:
1. Rewrite bullet points to mirror JD keywords and language exactly
2. Reorder the skills section to match what the JD prioritizes
3. ALWAYS keep the candidate's real email ({email}) and phone ({phone}) in the header — never change them
4. Keep all facts truthful — never fabricate experience
5. Make it ATS-friendly with proper keyword density
6. On the very last line output exactly: MATCH_SCORE: [0-100]
Return only the tailored resume text + the score line. No commentary.""",
        messages=[{
            "role": "user",
            "content": (
                f"CANDIDATE: {name}\nEMAIL: {email}\nPHONE: {phone}\n\n"
                f"BASE RESUME:\n{base_resume}\n\n"
                f"TARGET ROLE: {role} at {company}\n\n"
                f"JOB DESCRIPTION:\n{jd}\n\n"
                f"Tailor the resume. End with MATCH_SCORE: [number]."
            )
        }]
    )

    text = message.content[0].text
    m    = re.search(r"MATCH_SCORE:\s*(\d+)", text)
    return {
        "tailored": re.sub(r"MATCH_SCORE:\s*\d+", "", text).strip(),
        "score":    int(m.group(1)) if m else 75,
    }


# ─────────────────────────────────────────────────────────────────────────────
# utils/resume_helpers.py  —  PDF + TXT generation
# ─────────────────────────────────────────────────────────────────────────────

def resume_to_html(text: str) -> str:
    """Convert plain-text resume to styled HTML."""
    lines = text.split("\n")
    html = """<html><head><style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body{font-family:Inter,Arial,sans-serif;font-size:11px;margin:40px 50px;
             color:#1a1a2e;line-height:1.6}
        h1{font-size:20px;margin:0 0 2px;font-weight:700}
        .contact{font-size:10px;color:#555;margin-bottom:14px;
                 border-bottom:2px solid #6c63ff;padding-bottom:8px}
        h2{font-size:11px;color:#6c63ff;border-bottom:1px solid #e5e7eb;
           margin:14px 0 5px;text-transform:uppercase;letter-spacing:.8px;font-weight:700}
        p{margin:2px 0}
        ul{margin:2px 0;padding-left:16px}
        li{margin:1px 0}
    </style></head><body>"""

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            html += "<br style='line-height:4px;'>"
        elif i == 0:
            html += f"<h1>{line}</h1>"
        elif i == 1 and ("@" in line or "|" in line):
            html += f"<div class='contact'>{line}</div>"
        elif line == line.upper() and len(line) > 3 and not line.startswith("-"):
            html += f"<h2>{line}</h2>"
        elif line.startswith("-") or line.startswith("•"):
            html += f"<ul><li>{line[1:].strip()}</li></ul>"
        else:
            html += f"<p>{line}</p>"

    html += "</body></html>"
    return html


def generate_pdf_bytes(resume_text: str) -> bytes:
    """Generate a PDF from resume text using WeasyPrint. Returns bytes."""
    try:
        from weasyprint import HTML
        html = resume_to_html(resume_text)
        return HTML(string=html).write_pdf()
    except ImportError:
        # Fallback: return HTML bytes if WeasyPrint not installed
        html = resume_to_html(resume_text)
        return html.encode("utf-8")


def generate_txt_bytes(resume_text: str) -> bytes:
    """Return plain-text resume as bytes for download."""
    return resume_text.encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# utils/constants.py
# ─────────────────────────────────────────────────────────────────────────────

SUGGESTED_ROLES = [
    "Data Scientist", "Data Analyst", "AI/ML Engineer", "Data Engineer",
    "Machine Learning Engineer", "Business Intelligence Analyst",
    "Analytics Engineer", "NLP Engineer", "MLOps Engineer", "Research Scientist",
]

DEFAULT_RESUME = """Rohith Reddy Aleti
aleti.ro@northeastern.edu | LinkedIn | +1-857-675-0070 | Open to relocate

EDUCATION
Northeastern University - MS Data Analytics Engineering | GPA: 3.6/4 | 09/2023 - 05/2025
Courses: Data Visualization, Data Management for Analytics, Machine Learning, Data Mining

Institute of Aeronautical Engineering - B.Tech Civil Engineering | GPA: 3.5/4 | 07/2019 - 11/2023
Courses: Data Structures & Algorithms, DBMS, Python Programming

SKILLS
Programming & Data: Python, R, SQL, MATLAB, SAS, PySpark, NumPy, pandas, Apache Spark, Hadoop, Airflow, Apache Kafka
Databases & Cloud: MySQL, PostgreSQL, MSSQL, Oracle, Snowflake, MongoDB, NoSQL, AWS, GCP
ML & AI: Scikit-Learn, PyTorch, TensorFlow, Keras, XGBoost, LightGBM, SHAP, LIME
Deep Learning & NLP: CNN, RNN, LSTM, Transfer Learning, Word2Vec, BERT, Sentiment Analysis
MLOps & Deployment: Flask, FastAPI, MLflow, Docker, REST API, Streamlit, Cloud Deployment
Analytics & Visualization: Tableau, Power BI, Excel (Advanced), Matplotlib, Seaborn, Plotly
Tools: GitHub, Jira, n8n Workflow Automation, Technical Documentation

EXPERIENCE
AI Engineer | Humanitarians AI | Boston, MA | 05/2025 - Present
- Led Content Agent Layer in Madison, an open-source AI marketing intelligence framework
- Built automated n8n workflows to collect and analyze multi-channel engagement metrics
- Drove KPI dashboards, sentiment analysis, and optimization strategies

Graduate Program Assistant | Northeastern University | Boston, MA | 01/2024 - 04/2025
- Extracted and analyzed large datasets using SQL, R, and Python
- Built Tableau dashboards to track academic KPIs for faculty teams

Data Analyst Intern | Renewa Pellets | Hyderabad, India | 05/2024 - 08/2024
- Conducted statistical analysis to identify operational inefficiencies
- Automated reporting with advanced Excel formulas and pivot tables

Data Scientist | Solix Solutions | Hyderabad, India | 04/2022 - 08/2023
- Developed Tableau/Power BI dashboards improving decision-making timelines by 30%
- Created advanced SQL queries for sales strategy, forecasting, and scenario modeling
- Translated business needs into ML-driven insights and KPI tracking systems

PROJECTS
ML-Based Customer Churn Prediction
- Built end-to-end ML pipeline (Python, XGBoost) achieving 91% F1-score
Real-Time Traffic Flow Prediction
- LSTM time-series forecasting in TensorFlow, reducing RMSE by 18% vs. ARIMA baselines"""


# ─────────────────────────────────────────────────────────────────────────────
# utils/mock_data.py
# ─────────────────────────────────────────────────────────────────────────────

def get_mock_apps(email: str) -> list:
    return [
        {
            "id": "mock-1", "company": "Google", "role": "Data Scientist",
            "status": "Applied", "date": "2026-03-01", "score": 93, "email": email,
            "resume": f"Rohith Reddy Aleti\n{email}\n\nTailored for Google DS — "
                      "emphasized TensorFlow, BigQuery, GCP pipelines, distributed ML.",
        },
        {
            "id": "mock-2", "company": "Meta", "role": "AI/ML Engineer",
            "status": "Applied", "date": "2026-03-01", "score": 89, "email": email,
            "resume": f"Rohith Reddy Aleti\n{email}\n\nTailored for Meta MLE — "
                      "highlighted PyTorch, BERT, NLP, recommendation systems.",
        },
        {
            "id": "mock-3", "company": "Amazon", "role": "Data Engineer",
            "status": "Pending", "date": "2026-03-02", "score": 85, "email": email,
            "resume": f"Rohith Reddy Aleti\n{email}\n\nTailored for Amazon DE — "
                      "foregrounded Spark, Kafka, Airflow, AWS Redshift.",
        },
        {
            "id": "mock-4", "company": "Stripe", "role": "Data Scientist",
            "status": "Applied", "date": "2026-03-02", "score": 91, "email": email,
            "resume": f"Rohith Reddy Aleti\n{email}\n\nTailored for Stripe DS — "
                      "highlighted SQL, Python, A/B testing, payment analytics.",
        },
        {
            "id": "mock-5", "company": "Netflix", "role": "ML Engineer",
            "status": "Failed",  "date": "2026-02-28", "score": 74, "email": email,
            "resume": f"Rohith Reddy Aleti\n{email}\n\nTailored for Netflix MLE — "
                      "CAPTCHA blocked form submission.",
        },
    ]
