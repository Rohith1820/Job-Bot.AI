# pages/setup.py

import streamlit as st
from utils.constants import SUGGESTED_ROLES, DEFAULT_RESUME

def render():
    # ── Header ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding: 40px 0 20px;'>
        <div style='font-size:56px;'>🤖</div>
        <h1 style='color:#f9fafb; margin:8px 0 4px;'>JobBot AI</h1>
        <p style='color:#6b7280;'>Your 24/7 automated job application assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Step tracker in session state ─────────────────────────────────────
    if "setup_step" not in st.session_state:
        st.session_state.setup_step = 1
    if "setup_roles" not in st.session_state:
        st.session_state.setup_roles = []

    step = st.session_state.setup_step

    # Progress bar
    st.progress((step - 1) / 2)
    cols = st.columns(3)
    for i, label in enumerate(["1 · Profile", "2 · Target Roles", "3 · Resume"]):
        color = "#7c3aed" if step >= i + 1 else "#374151"
        cols[i].markdown(
            f"<p style='text-align:center; color:{color}; font-weight:600;'>{label}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # ── STEP 1 : Profile ──────────────────────────────────────────────
        if step == 1:
            st.markdown("### 👤 Your Profile")
            name     = st.text_input("Full Name *",  placeholder="e.g. Rohith Reddy Aleti",  key="s_name")
            email    = st.text_input("Email *",       placeholder="your@email.com",            key="s_email")
            st.caption("⚡ Companies will reply to this address — used in every application form")
            phone    = st.text_input("Phone",         placeholder="+1-xxx-xxx-xxxx",           key="s_phone")
            location = st.text_input("Location",      placeholder="Boston, MA / Open to relocate", key="s_location")

            if st.button("Continue →", use_container_width=True, type="primary"):
                if not name.strip() or not email.strip():
                    st.error("Name and email are required.")
                else:
                    st.session_state.draft = {
                        "name": name, "email": email,
                        "phone": phone, "location": location,
                    }
                    st.session_state.setup_step = 2
                    st.rerun()

        # ── STEP 2 : Target Roles ─────────────────────────────────────────
        elif step == 2:
            st.markdown("### 🎯 Target Roles")
            st.caption("Bot searches and applies for these roles 24/7.")

            # Suggested role toggles
            st.markdown("**Select from suggestions:**")
            cols2 = st.columns(2)
            for i, role in enumerate(SUGGESTED_ROLES):
                with cols2[i % 2]:
                    checked = role in st.session_state.setup_roles
                    if st.checkbox(role, value=checked, key=f"role_{role}"):
                        if role not in st.session_state.setup_roles:
                            st.session_state.setup_roles.append(role)
                    else:
                        if role in st.session_state.setup_roles:
                            st.session_state.setup_roles.remove(role)

            # Custom role
            st.markdown("**Or add a custom role:**")
            c1, c2 = st.columns([4, 1])
            custom = c1.text_input("", placeholder="e.g. Quantitative Analyst", label_visibility="collapsed", key="custom_role")
            if c2.button("+ Add"):
                if custom.strip() and custom.strip() not in st.session_state.setup_roles:
                    st.session_state.setup_roles.append(custom.strip())
                    st.rerun()

            if st.session_state.setup_roles:
                st.success(f"Selected ({len(st.session_state.setup_roles)}): " +
                           ", ".join(st.session_state.setup_roles))

            bc1, bc2 = st.columns(2)
            if bc1.button("← Back"):
                st.session_state.setup_step = 1; st.rerun()
            if bc2.button("Continue →", type="primary"):
                if not st.session_state.setup_roles:
                    st.error("Select at least one role.")
                else:
                    st.session_state.setup_step = 3; st.rerun()

        # ── STEP 3 : Resume ───────────────────────────────────────────────
        elif step == 3:
            st.markdown("### 📄 Your Resume")
            st.caption("AI tailors this for every job it applies to.")

            source = st.radio("Resume source", ["Use Sample Resume", "Paste My Own"],
                              horizontal=True, key="resume_source")

            if source == "Use Sample Resume":
                resume_text = DEFAULT_RESUME
                st.text_area("Resume Preview", value=resume_text, height=260,
                             disabled=True, key="resume_preview")
            else:
                resume_text = st.text_area(
                    "Paste your resume here",
                    placeholder="Paste full resume text...",
                    height=260, key="resume_paste"
                )

            bc1, bc2 = st.columns(2)
            if bc1.button("← Back"):
                st.session_state.setup_step = 2; st.rerun()
            if bc2.button("🚀 Launch 24/7 Bot", type="primary"):
                if not resume_text.strip():
                    st.error("Resume is required.")
                else:
                    st.session_state.profile = {
                        **st.session_state.draft,
                        "roles":       st.session_state.setup_roles,
                        "resume_text": resume_text,
                    }
                    # Seed mock applications
                    from utils.mock_data import get_mock_apps
                    st.session_state.applications = get_mock_apps(
                        st.session_state.profile["email"]
                    )
                    st.session_state.setup_step = 1
                    st.rerun()
