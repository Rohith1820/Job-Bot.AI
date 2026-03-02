# tabs/tailor_tab.py

import streamlit as st
import uuid
from datetime import date
from utils.api import tailor_resume
from utils.resume_helpers import generate_pdf_bytes, generate_txt_bytes


def render():
    p = st.session_state.profile

    col_left, col_right = st.columns(2, gap="large")

    # ── Left: Inputs ──────────────────────────────────────────────────────
    with col_left:
        st.markdown("#### 🎯 Select Role")
        role = st.radio(
            "Target role for this application",
            options=p["roles"],
            horizontal=True,
            label_visibility="collapsed",
            key="tailor_role",
        )
        st.markdown(
            f"<div style='background:#052e16;border:1px solid #166534;"
            f"border-radius:8px;padding:8px 12px;font-size:12px;color:#4ade80;"
            f"margin-bottom:12px;'>📧 Applying with: <strong>{p['email']}</strong></div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### 🏢 Job Details")
        company = st.text_input("Company Name", placeholder="e.g. Google", key="tailor_company")
        jd      = st.text_area("Job Description", placeholder="Paste the full job description here...",
                               height=220, key="tailor_jd")

        tailor_btn = st.button("✨ Tailor Resume with AI", use_container_width=True, type="primary")

    # ── Right: Output ─────────────────────────────────────────────────────
    with col_right:
        st.markdown("#### 📄 Tailored Resume")

        if tailor_btn:
            if not company.strip() or not jd.strip():
                st.error("Enter company name and job description.")
            else:
                with st.spinner("AI is tailoring your resume..."):
                    result = tailor_resume(
                        base_resume = p["resume_text"],
                        jd          = jd,
                        role        = role,
                        company     = company,
                        name        = p["name"],
                        email       = p["email"],
                        phone       = p.get("phone", ""),
                    )
                st.session_state.tailored_resume = result["tailored"]
                st.session_state.tailored_score  = result["score"]
                st.session_state.tailor_company  = company
                st.session_state.tailor_role     = role

        tailored = st.session_state.get("tailored_resume", "")
        score    = st.session_state.get("tailored_score",  None)
        t_co     = st.session_state.get("tailor_company",  company)
        t_role   = st.session_state.get("tailor_role",     role)

        if not tailored:
            st.info("Paste a job description and click **Tailor Resume with AI** to see the result here.")
        else:
            if score:
                st.progress(score / 100, text=f"JD Match Score: **{score}%**")

            st.text_area("Tailored Resume", value=tailored, height=280,
                         disabled=True, key="tailored_output")

            # ── Downloads ─────────────────────────────────────────────────
            d1, d2 = st.columns(2)
            with d1:
                pdf_bytes = generate_pdf_bytes(tailored)
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"Resume_{t_co}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with d2:
                txt_bytes = generate_txt_bytes(tailored)
                st.download_button(
                    label="📄 Download .txt",
                    data=txt_bytes,
                    file_name=f"Resume_{t_co}_{t_role.replace(' ','_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            # ── Save ──────────────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Save & Mark as Applied", use_container_width=True):
                new_app = {
                    "id":      str(uuid.uuid4()),
                    "company": t_co,
                    "role":    t_role,
                    "status":  "Applied",
                    "date":    str(date.today()),
                    "score":   score or 80,
                    "email":   p["email"],
                    "resume":  tailored,
                }
                if "applications" not in st.session_state:
                    st.session_state.applications = []
                st.session_state.applications.insert(0, new_app)

                # Clear tailored state
                for k in ["tailored_resume", "tailored_score", "tailor_company", "tailor_role"]:
                    st.session_state.pop(k, None)

                st.success(f"✅ Application saved for {t_co} — {t_role}!")
                st.rerun()
