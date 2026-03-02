# tabs/applications_tab.py

import streamlit as st
from utils.resume_helpers import generate_pdf_bytes, generate_txt_bytes

STATUS_COLORS = {
    "Applied": ("✅", "#4ade80"),
    "Pending": ("⏳", "#fbbf24"),
    "Failed":  ("❌", "#f87171"),
}

def render():
    apps = st.session_state.get("applications", [])

    if not apps:
        st.info("No applications yet. Use the **Tailor & Apply** tab to get started.")
        return

    # ── Search + Filter bar ───────────────────────────────────────────────
    c1, c2 = st.columns([3, 1])
    search = c1.text_input("🔍 Search", placeholder="Search company or role...",
                            label_visibility="collapsed", key="app_search")
    status_filter = c2.selectbox("Status", ["All", "Applied", "Pending", "Failed"],
                                  label_visibility="collapsed", key="app_filter")

    filtered = [
        a for a in apps
        if (search.lower() in a["company"].lower() or search.lower() in a["role"].lower())
        and (status_filter == "All" or a["status"] == status_filter)
    ]

    st.markdown(f"**{len(filtered)}** application(s) found")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Application cards ─────────────────────────────────────────────────
    for app in filtered:
        icon, color = STATUS_COLORS.get(app["status"], ("·", "#9ca3af"))

        with st.container():
            st.markdown(f"""
            <div class='card'>
                <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                    <div>
                        <span style='font-size:18px;font-weight:700;color:#f9fafb;'>{app["company"]}</span>
                        &nbsp;
                        <span style='font-size:12px;color:#6b7280;'>{app["role"]} &nbsp;·&nbsp; {app["date"]}</span>
                        <br>
                        <span style='font-size:12px;color:#4ade80;'>📧 {app["email"]}</span>
                    </div>
                    <div style='text-align:right;'>
                        <span style='color:{color};font-size:13px;font-weight:600;'>{icon} {app["status"]}</span>
                        <br>
                        <span style='color:#a78bfa;font-size:12px;font-weight:600;'>
                            JD Match: {app["score"]}%
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons per card
            b1, b2, b3, b4 = st.columns([2, 1, 1, 1])

            # Expandable resume preview
            with b1:
                with st.expander("👁 View Resume"):
                    st.text_area(
                        f"resume_{app['id']}",
                        value=app["resume"],
                        height=220,
                        disabled=True,
                        label_visibility="collapsed",
                    )

            with b2:
                pdf = generate_pdf_bytes(app["resume"])
                st.download_button(
                    label="📥 PDF",
                    data=pdf,
                    file_name=f"Resume_{app['company']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"pdf_{app['id']}",
                )

            with b3:
                txt = generate_txt_bytes(app["resume"])
                st.download_button(
                    label="📄 .txt",
                    data=txt,
                    file_name=f"Resume_{app['company']}_{app['role'].replace(' ','_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"txt_{app['id']}",
                )

            with b4:
                if st.button("🗑", key=f"del_{app['id']}", help="Remove this application"):
                    st.session_state.applications = [
                        a for a in st.session_state.applications if a["id"] != app["id"]
                    ]
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
