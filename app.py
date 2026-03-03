# app.py — Complete single-file Streamlit frontend. No pages/ or tabs/ needed.
# run: streamlit run app.py

import os
import re
import uuid
import base64
import streamlit as st
from datetime import date
import anthropic
import httpx

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JobBot AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
body, .stApp { background-color: #030712; color: #f9fafb; }
.block-container { padding: 2rem; max-width: 1100px; }
.stButton > button { border-radius: 10px; font-weight: 600; transition: all .2s; }
.stTextInput > div > input,
.stTextArea > div > textarea {
    background: #1f2937; border: 1px solid #374151;
    color: #f9fafb; border-radius: 8px;
}
div[data-testid="stMetric"] {
    background: #111827; border: 1px solid #1f2937;
    border-radius: 12px; padding: 16px;
}
.card {
    background: #111827; border: 1px solid #1f2937;
    border-radius: 14px; padding: 20px; margin-bottom: 12px;
}
.log-box {
    background: #000; border-radius: 10px; padding: 16px;
    font-family: monospace; font-size: 12px;
    max-height: 400px; overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────
SUGGESTED_ROLES = [
    "Data Scientist", "Data Analyst", "AI/ML Engineer", "Data Engineer",
    "Machine Learning Engineer", "Business Intelligence Analyst",
    "Analytics Engineer", "NLP Engineer", "MLOps Engineer", "Research Scientist",
]

DEFAULT_RESUME = """Rohith Reddy Aleti
aleti.ro@northeastern.edu | LinkedIn | +1-857-675-0070 | Open to relocate

EDUCATION
Northeastern University - MS Data Analytics Engineering | GPA: 3.6/4 | 09/2023 - 05/2025
Institute of Aeronautical Engineering - B.Tech Civil Engineering | GPA: 3.5/4 | 07/2019 - 11/2023

SKILLS
Programming: Python, R, SQL, PySpark, NumPy, pandas, Apache Spark, Kafka
Cloud & DB: MySQL, PostgreSQL, Snowflake, MongoDB, AWS, GCP
ML & AI: Scikit-Learn, PyTorch, TensorFlow, XGBoost, LightGBM, SHAP
NLP: BERT, Word2Vec, LSTM, Sentiment Analysis, Recommendation Systems
MLOps: FastAPI, MLflow, Docker, Streamlit, REST API, Cloud Deployment
Visualization: Tableau, Power BI, Matplotlib, Seaborn, Plotly

EXPERIENCE
AI Engineer | Humanitarians AI | Boston, MA | 05/2025 - Present
- Led Content Agent Layer in Madison, an open-source AI marketing intelligence framework
- Built automated n8n workflows to collect and analyze multi-channel engagement metrics

Graduate Program Assistant | Northeastern University | 01/2024 - 04/2025
- Analyzed large datasets using SQL, R, and Python
- Built Tableau dashboards to track academic KPIs

Data Scientist | Solix Solutions | Hyderabad | 04/2022 - 08/2023
- Developed Tableau/Power BI dashboards improving decision-making timelines by 30%
- Created SQL queries for sales strategy, forecasting, and scenario modeling

PROJECTS
ML-Based Customer Churn Prediction - XGBoost pipeline, 91% F1-score
Real-Time Traffic Flow Prediction  - LSTM TensorFlow, 18% RMSE improvement"""

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Helpers ───────────────────────────────────────────────────────────────
def tailor_resume_ai(base_resume, jd, role, company, name, email, phone):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=1500,
        system=f"""You are an expert ATS resume optimizer.
1. Rewrite bullet points to mirror JD keywords exactly
2. Reorder skills to match JD priorities
3. ALWAYS keep email ({email}) and phone ({phone}) unchanged in header
4. Never fabricate experience — keep all facts truthful
5. Last line must be exactly: MATCH_SCORE: [0-100]
Return only the tailored resume + score line.""",
        messages=[{"role": "user", "content":
            f"CANDIDATE: {name}\nEMAIL: {email}\nPHONE: {phone}\n\n"
            f"BASE RESUME:\n{base_resume}\n\n"
            f"TARGET ROLE: {role} at {company}\n\nJOB DESCRIPTION:\n{jd}\n\n"
            f"Tailor the resume. End with MATCH_SCORE: [number]."}]
    )
    text = msg.content[0].text
    m = re.search(r"MATCH_SCORE:\s*(\d+)", text)
    return {
        "tailored": re.sub(r"MATCH_SCORE:\s*\d+", "", text).strip(),
        "score": int(m.group(1)) if m else 75
    }

def generate_pdf_bytes(resume_text):
    try:
        from weasyprint import HTML
        html = resume_to_html(resume_text)
        return HTML(string=html).write_pdf()
    except Exception:
        return resume_text.encode("utf-8")

def resume_to_html(text):
    lines = text.split("\n")
    html = """<html><head><style>
    body{font-family:Arial,sans-serif;font-size:11px;margin:40px;color:#1a1a2e;line-height:1.6}
    h1{font-size:18px;margin:0 0 2px;font-weight:700}
    .contact{font-size:10px;color:#555;border-bottom:2px solid #6c63ff;padding-bottom:6px;margin-bottom:12px}
    h2{font-size:11px;color:#6c63ff;border-bottom:1px solid #eee;margin:12px 0 4px;
       text-transform:uppercase;letter-spacing:.8px;font-weight:700}
    p{margin:2px 0} ul{margin:2px 0;padding-left:16px} li{margin:1px 0}
    </style></head><body>"""
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: html += "<br>"
        elif i == 0: html += f"<h1>{line}</h1>"
        elif i == 1 and ("@" in line or "|" in line): html += f"<div class='contact'>{line}</div>"
        elif line == line.upper() and len(line) > 3 and not line.startswith("-"): html += f"<h2>{line}</h2>"
        elif line.startswith("-") or line.startswith("•"): html += f"<ul><li>{line[1:].strip()}</li></ul>"
        else: html += f"<p>{line}</p>"
    html += "</body></html>"
    return html

def get_mock_apps(email):
    return [
        {"id":"m1","company":"Google","role":"Data Scientist","status":"Applied",
         "date":"2026-03-01","score":93,"email":email,
         "resume":f"Rohith Reddy Aleti\n{email}\n\nTailored for Google DS — emphasized TensorFlow, BigQuery, GCP."},
        {"id":"m2","company":"Meta","role":"AI/ML Engineer","status":"Applied",
         "date":"2026-03-01","score":89,"email":email,
         "resume":f"Rohith Reddy Aleti\n{email}\n\nTailored for Meta MLE — highlighted PyTorch, BERT, NLP."},
        {"id":"m3","company":"Amazon","role":"Data Engineer","status":"Pending",
         "date":"2026-03-02","score":85,"email":email,
         "resume":f"Rohith Reddy Aleti\n{email}\n\nTailored for Amazon DE — foregrounded Spark, Kafka, Airflow."},
    ]

STATUS_COLORS = {"Applied":("#4ade80","#052e16","#166534"),
                 "Pending":("#fbbf24","#1c1405","#92400e"),
                 "Failed": ("#f87171","#1c0505","#991b1b")}

# ── SETUP SCREEN ──────────────────────────────────────────────────────────
def render_setup():
    st.markdown("""
    <div style='text-align:center;padding:40px 0 20px;'>
        <div style='font-size:56px;'>🤖</div>
        <h1 style='color:#f9fafb;margin:8px 0 4px;'>JobBot AI</h1>
        <p style='color:#6b7280;'>Your 24/7 automated job application assistant</p>
    </div>""", unsafe_allow_html=True)

    if "setup_step" not in st.session_state: st.session_state.setup_step = 1
    if "setup_roles" not in st.session_state: st.session_state.setup_roles = []

    step = st.session_state.setup_step
    st.progress((step-1)/2)
    c1,c2,c3 = st.columns(3)
    for col, label, s in [(c1,"1 · Profile",1),(c2,"2 · Target Roles",2),(c3,"3 · Resume",3)]:
        col.markdown(f"<p style='text-align:center;color:{'#7c3aed' if step>=s else '#374151'};font-weight:600;'>{label}</p>",
                     unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])

    with col:
        # Step 1
        if step == 1:
            st.markdown("### 👤 Your Profile")
            name     = st.text_input("Full Name *",  placeholder="e.g. Rohith Reddy Aleti", key="s_name")
            email    = st.text_input("Email *",       placeholder="your@email.com",          key="s_email")
            st.caption("⚡ Companies will reply to this — used in every application form")
            phone    = st.text_input("Phone",         placeholder="+1-xxx-xxx-xxxx",          key="s_phone")
            location = st.text_input("Location",      placeholder="Boston, MA / Open to relocate", key="s_loc")
            if st.button("Continue →", use_container_width=True, type="primary", key="s1_next"):
                if not name.strip() or not email.strip():
                    st.error("Name and email are required.")
                else:
                    st.session_state.draft = {"name":name,"email":email,"phone":phone,"location":location}
                    st.session_state.setup_step = 2
                    st.rerun()

        # Step 2
        elif step == 2:
            st.markdown("### 🎯 Target Roles")
            st.caption("Bot searches and applies for these 24/7.")
            cols = st.columns(2)
            for i, role in enumerate(SUGGESTED_ROLES):
                with cols[i % 2]:
                    checked = role in st.session_state.setup_roles
                    if st.checkbox(role, value=checked, key=f"role_{role}"):
                        if role not in st.session_state.setup_roles:
                            st.session_state.setup_roles.append(role)
                    else:
                        if role in st.session_state.setup_roles:
                            st.session_state.setup_roles.remove(role)
            st.markdown("**Add custom role:**")
            ca, cb = st.columns([4,1])
            custom = ca.text_input("", placeholder="e.g. Quantitative Analyst",
                                   label_visibility="collapsed", key="custom_role")
            if cb.button("+ Add", key="add_custom"):
                if custom.strip() and custom.strip() not in st.session_state.setup_roles:
                    st.session_state.setup_roles.append(custom.strip()); st.rerun()
            if st.session_state.setup_roles:
                st.success(f"Selected ({len(st.session_state.setup_roles)}): " +
                           ", ".join(st.session_state.setup_roles))
            b1, b2 = st.columns(2)
            if b1.button("← Back", key="s2_back"):
                st.session_state.setup_step = 1; st.rerun()
            if b2.button("Continue →", type="primary", key="s2_next"):
                if not st.session_state.setup_roles:
                    st.error("Select at least one role.")
                else:
                    st.session_state.setup_step = 3; st.rerun()

        # Step 3
        elif step == 3:
            st.markdown("### 📄 Your Resume")
            st.caption("AI tailors this for every job application.")
            src = st.radio("Source", ["Use Sample Resume","Paste My Own"],
                           horizontal=True, key="resume_src")
            resume_text = DEFAULT_RESUME if src == "Use Sample Resume" else ""
            if src == "Use Sample Resume":
                st.text_area("Preview", value=DEFAULT_RESUME, height=240,
                             disabled=True, key="res_preview")
            else:
                resume_text = st.text_area("Paste resume", placeholder="Paste full resume text...",
                                           height=240, key="res_paste")
            b1, b2 = st.columns(2)
            if b1.button("← Back", key="s3_back"):
                st.session_state.setup_step = 2; st.rerun()
            if b2.button("🚀 Launch 24/7 Bot", type="primary", key="s3_launch"):
                final_resume = DEFAULT_RESUME if src == "Use Sample Resume" else resume_text
                if not final_resume.strip():
                    st.error("Resume is required.")
                else:
                    st.session_state.profile = {
                        **st.session_state.draft,
                        "roles": st.session_state.setup_roles,
                        "resume_text": final_resume,
                    }
                    st.session_state.applications = get_mock_apps(st.session_state.profile["email"])
                    st.session_state.setup_step = 1
                    st.rerun()

# ── DASHBOARD ─────────────────────────────────────────────────────────────
def render_dashboard():
    p = st.session_state.profile
    apps = st.session_state.get("applications", [])

    # Header
    h1, h2 = st.columns([6,2])
    with h1:
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:12px;padding:8px 0;'>
          <div style='width:40px;height:40px;border-radius:12px;
               background:linear-gradient(135deg,#7c3aed,#2563eb);
               display:flex;align-items:center;justify-content:center;font-size:22px;'>🤖</div>
          <div>
            <div style='font-size:16px;font-weight:700;color:#f9fafb;'>JobBot AI — {p["name"]}</div>
            <div style='font-size:12px;color:#6b7280;'>
              📧 {p["email"]} &nbsp;·&nbsp;
              🎯 {", ".join(p["roles"][:2])}{"" if len(p["roles"])<=2 else f" +{len(p['roles'])-2} more"}
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    with h2:
        st.markdown("""<div style='text-align:right;padding-top:10px;'>
        <span style='background:#052e16;color:#4ade80;border:1px solid #166534;
             padding:4px 14px;border-radius:9999px;font-size:12px;font-weight:600;'>
             ● 24/7 Active</span></div>""", unsafe_allow_html=True)
        if st.button("⚙ Reset", key="reset"):
            for k in ["profile","applications","setup_roles","draft"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.divider()

    # Stats
    total   = len(apps)
    applied = sum(1 for a in apps if a["status"]=="Applied")
    pending = sum(1 for a in apps if a["status"]=="Pending")
    failed  = sum(1 for a in apps if a["status"]=="Failed")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📋 Total",   total)
    c2.metric("✅ Applied",  applied)
    c3.metric("⏳ Pending",  pending)
    c4.metric("❌ Failed",   failed)
    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1,tab2,tab3,tab4 = st.tabs(["✨ Tailor & Apply","📋 Applications","🤖 Bot Log","👤 Profile"])

    # ── TAB 1: Tailor ─────────────────────────────────────────────────────
    with tab1:
        cl, cr = st.columns(2, gap="large")
        with cl:
            st.markdown("#### 🎯 Select Role")
            role = st.radio("Role", p["roles"], horizontal=True,
                            label_visibility="collapsed", key="t_role")
            st.markdown(
                f"<div style='background:#052e16;border:1px solid #166534;border-radius:8px;"
                f"padding:8px 12px;font-size:12px;color:#4ade80;margin-bottom:12px;'>"
                f"📧 Applying with: <strong>{p['email']}</strong></div>",
                unsafe_allow_html=True)
            st.markdown("#### 🏢 Job Details")
            company = st.text_input("Company", placeholder="e.g. Google", key="t_company")
            jd      = st.text_area("Job Description", placeholder="Paste full JD here...",
                                   height=220, key="t_jd")
            tailor_btn = st.button("✨ Tailor Resume with AI",
                                   use_container_width=True, type="primary", key="t_btn")

        with cr:
            st.markdown("#### 📄 Tailored Resume")
            if tailor_btn:
                if not company.strip() or not jd.strip():
                    st.error("Enter company name and job description.")
                elif not ANTHROPIC_KEY:
                    st.error("ANTHROPIC_API_KEY not set in environment variables.")
                else:
                    with st.spinner("AI is tailoring your resume..."):
                        result = tailor_resume_ai(p["resume_text"], jd, role, company,
                                                  p["name"], p["email"], p.get("phone",""))
                    st.session_state.t_result  = result["tailored"]
                    st.session_state.t_score   = result["score"]
                    st.session_state.t_company = company
                    st.session_state.t_role    = role

            tailored = st.session_state.get("t_result","")
            score    = st.session_state.get("t_score", None)
            t_co     = st.session_state.get("t_company", "")
            t_role   = st.session_state.get("t_role", role)

            if not tailored:
                st.info("Paste a JD and click **Tailor Resume with AI** to see the result.")
            else:
                if score:
                    st.progress(score/100, text=f"JD Match: **{score}%**")
                st.text_area("Result", value=tailored, height=260,
                             disabled=True, key="t_output")
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button("📥 Download PDF",
                        data=generate_pdf_bytes(tailored),
                        file_name=f"Resume_{t_co}.pdf",
                        mime="application/pdf",
                        use_container_width=True, key="dl_pdf_tailor")
                with d2:
                    st.download_button("📄 Download .txt",
                        data=tailored.encode("utf-8"),
                        file_name=f"Resume_{t_co}_{t_role.replace(' ','_')}.txt",
                        mime="text/plain",
                        use_container_width=True, key="dl_txt_tailor")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ Save & Mark as Applied", use_container_width=True, key="save_app"):
                    new_app = {"id": str(uuid.uuid4()), "company": t_co, "role": t_role,
                               "status":"Applied", "date": str(date.today()),
                               "score": score or 80, "email": p["email"], "resume": tailored}
                    st.session_state.applications.insert(0, new_app)
                    for k in ["t_result","t_score","t_company","t_role"]:
                        st.session_state.pop(k, None)
                    st.success(f"✅ Saved: {t_role} at {t_co}")
                    st.rerun()

    # ── TAB 2: Applications ───────────────────────────────────────────────
    with tab2:
        s1, s2 = st.columns([3,1])
        search = s1.text_input("🔍", placeholder="Search company or role...",
                               label_visibility="collapsed", key="app_search")
        filt   = s2.selectbox("Status", ["All","Applied","Pending","Failed"],
                              label_visibility="collapsed", key="app_filt")
        filtered = [a for a in apps
                    if (search.lower() in a["company"].lower() or
                        search.lower() in a["role"].lower())
                    and (filt=="All" or a["status"]==filt)]
        st.markdown(f"**{len(filtered)}** application(s)")
        st.markdown("<br>", unsafe_allow_html=True)

        for app in filtered:
            col,bg,border = STATUS_COLORS.get(app["status"],("#9ca3af","#111","#374151"))
            st.markdown(f"""
            <div class='card'>
              <div style='display:flex;justify-content:space-between;'>
                <div>
                  <span style='font-size:17px;font-weight:700;color:#f9fafb;'>{app["company"]}</span>
                  &nbsp;<span style='font-size:12px;color:#6b7280;'>{app["role"]} · {app["date"]}</span>
                  <br><span style='font-size:12px;color:#4ade80;'>📧 {app["email"]}</span>
                </div>
                <div style='text-align:right;'>
                  <span style='background:{bg};color:{col};border:1px solid {border};
                    padding:3px 10px;border-radius:9999px;font-size:12px;font-weight:600;'>
                    {app["status"]}</span>
                  <br><span style='color:#a78bfa;font-size:12px;font-weight:600;'>
                    {app["score"]}% match</span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            b1,b2,b3,b4 = st.columns([2,1,1,1])
            with b1:
                with st.expander("👁 View Resume"):
                    st.text_area("", value=app["resume"], height=200,
                                 disabled=True, label_visibility="collapsed",
                                 key=f"view_{app['id']}")
            with b2:
                st.download_button("📥 PDF",
                    data=generate_pdf_bytes(app["resume"]),
                    file_name=f"Resume_{app['company']}.pdf",
                    mime="application/pdf",
                    use_container_width=True, key=f"pdf_{app['id']}")
            with b3:
                st.download_button("📄 .txt",
                    data=app["resume"].encode("utf-8"),
                    file_name=f"Resume_{app['company']}_{app['role'].replace(' ','_')}.txt",
                    mime="text/plain",
                    use_container_width=True, key=f"txt_{app['id']}")
            with b4:
                if st.button("🗑", key=f"del_{app['id']}", help="Delete"):
                    st.session_state.applications = [
                        a for a in st.session_state.applications if a["id"] != app["id"]]
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

    # ── TAB 3: Bot Log ────────────────────────────────────────────────────
    with tab3:
        roles_str = ", ".join(p["roles"][:3])
        st.markdown("""<div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
        <span style='width:10px;height:10px;background:#4ade80;border-radius:50%;
             display:inline-block;'></span>
        <span style='color:#4ade80;font-weight:600;'>Running on Render server</span>
        </div>""", unsafe_allow_html=True)

        logs = [
            ("09:42:11","✅",f"Applied: Data Scientist @ Google | Email: {p['email']} | Match: 93%","#4ade80"),
            ("09:40:55","📄","Generated PDF resume for Google application","#60a5fa"),
            ("09:38:30","🤖","AI tailoring resume for Google Data Scientist JD...","#a78bfa"),
            ("09:35:10","🔍","Found new job: Data Scientist @ Google (indeed.com)","#d1d5db"),
            ("09:32:00","✅",f"Applied: AI/ML Engineer @ Meta | Email: {p['email']} | Match: 89%","#4ade80"),
            ("09:28:01","🤖","AI tailoring resume for Meta AI/ML Engineer JD...","#a78bfa"),
            ("09:20:00","⏳","Pending: Data Engineer @ Amazon | CAPTCHA encountered","#fbbf24"),
            ("09:15:00","🔍",f"Scanning Indeed/LinkedIn for: {roles_str}","#9ca3af"),
            ("09:00:00","🚀","Bot cycle started. Scanning job boards...","#a78bfa"),
        ]
        log_html = "<div class='log-box'>"
        for t, ic, msg, color in logs:
            log_html += (f"<div style='margin-bottom:6px;'>"
                         f"<span style='color:#4b5563;'>[{t}]</span> "
                         f"<span style='color:{color};'>{ic} {msg}</span></div>")
        log_html += "</div>"
        st.markdown(log_html, unsafe_allow_html=True)
        st.warning("⚙️ **Real logs:** Deploy `scheduler.py` as a Background Worker on Render "
                   "with the same environment variables. It writes live logs to PostgreSQL.")

    # ── TAB 4: Profile ────────────────────────────────────────────────────
    with tab4:
        pc1, pc2 = st.columns(2, gap="large")
        with pc1:
            st.markdown("#### 👤 Your Profile")
            for label, val, color in [
                ("Name",        p["name"],              "#f9fafb"),
                ("Email",       p["email"],             "#4ade80"),
                ("Phone",       p.get("phone","—"),     "#f9fafb"),
                ("Location",    p.get("location","—"),  "#f9fafb"),
            ]:
                st.markdown(
                    f"<p style='color:#6b7280;font-size:12px;margin:0;'>{label}</p>"
                    f"<p style='color:{color};font-size:14px;margin:0 0 10px;'><strong>{val}</strong></p>",
                    unsafe_allow_html=True)
        with pc2:
            st.markdown(f"#### 🎯 Target Roles ({len(p['roles'])})")
            tags = " ".join(
                f"<span style='background:#2e1065;color:#c4b5fd;border:1px solid #5b21b6;"
                f"padding:4px 12px;border-radius:9999px;font-size:12px;margin:2px;"
                f"display:inline-block;'>{r}</span>" for r in p["roles"])
            st.markdown(f"<div style='line-height:2.6;'>{tags}</div>", unsafe_allow_html=True)

        st.markdown("#### 📄 Base Resume")
        st.text_area("", value=p["resume_text"], height=260,
                     disabled=True, label_visibility="collapsed", key="base_resume_view")

# ── Router ────────────────────────────────────────────────────────────────
if "profile" not in st.session_state:
    render_setup()
else:
    render_dashboard()
