# pages/dashboard.py

import streamlit as st
from tabs import tailor_tab, applications_tab, botlog_tab, profile_tab


def render():
    p = st.session_state.profile

    # ── Header ────────────────────────────────────────────────────────────
    h1, h2 = st.columns([6, 2])
    with h1:
        st.markdown(f"""
        <div style='display:flex; align-items:center; gap:12px; padding:8px 0;'>
            <div style='width:40px;height:40px;border-radius:12px;
                        background:linear-gradient(135deg,#7c3aed,#2563eb);
                        display:flex;align-items:center;justify-content:center;font-size:22px;'>🤖</div>
            <div>
                <div style='font-size:16px;font-weight:700;color:#f9fafb;'>
                    JobBot AI — {p["name"]}</div>
                <div style='font-size:12px;color:#6b7280;'>
                    📧 {p["email"]} &nbsp;·&nbsp;
                    🎯 {", ".join(p["roles"][:2])}{"" if len(p["roles"]) <= 2 else f" +{len(p['roles'])-2} more"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown("""
        <div style='text-align:right; padding-top:10px;'>
            <span style='background:#052e16;color:#4ade80;border:1px solid #166534;
                         padding:4px 14px;border-radius:9999px;font-size:12px;font-weight:600;'>
                ● 24/7 Active
            </span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚙ Reset", key="reset_btn"):
            for k in ["profile", "applications", "setup_roles", "draft"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.divider()

    # ── Stats row ─────────────────────────────────────────────────────────
    apps = st.session_state.get("applications", [])
    total   = len(apps)
    applied = sum(1 for a in apps if a["status"] == "Applied")
    pending = sum(1 for a in apps if a["status"] == "Pending")
    failed  = sum(1 for a in apps if a["status"] == "Failed")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total",   total)
    c2.metric("✅ Applied",  applied)
    c3.metric("⏳ Pending",  pending)
    c4.metric("❌ Failed",   failed)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "✨ Tailor & Apply",
        "📋 Applications",
        "🤖 Bot Log",
        "👤 Profile",
    ])

    with tab1: tailor_tab.render()
    with tab2: applications_tab.render()
    with tab3: botlog_tab.render()
    with tab4: profile_tab.render()
