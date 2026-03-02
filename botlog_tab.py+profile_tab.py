# tabs/botlog_tab.py

import streamlit as st

LOG_COLORS = {
    "✅": "#4ade80",
    "🔍": "#d1d5db",
    "🤖": "#a78bfa",
    "📄": "#60a5fa",
    "⏳": "#fbbf24",
    "❌": "#f87171",
    "🚀": "#a78bfa",
}

def render():
    p = st.session_state.profile
    roles_str = ", ".join(p["roles"][:3])

    logs = [
        ("09:42:11", f"✅ Applied: Data Scientist @ Google | Email: {p['email']} | Match: 93%"),
        ("09:40:55", "📄 Generated PDF resume for Google application"),
        ("09:38:30", "🤖 AI tailoring resume for Google Data Scientist JD..."),
        ("09:35:10", "🔍 Found new job: Data Scientist @ Google (indeed.com)"),
        ("09:32:00", f"✅ Applied: AI/ML Engineer @ Meta | Email: {p['email']} | Match: 89%"),
        ("09:30:44", "📄 Generated PDF resume for Meta application"),
        ("09:28:01", "🤖 AI tailoring resume for Meta AI/ML Engineer JD..."),
        ("09:25:20", "🔍 Found new job: AI/ML Engineer @ Meta (linkedin.com)"),
        ("09:20:00", "⏳ Pending: Data Engineer @ Amazon | CAPTCHA encountered, retrying..."),
        ("09:15:00", f"🔍 Scanning Indeed/LinkedIn for: {roles_str}"),
        ("09:00:00", "🚀 Bot cycle started. Scanning job boards..."),
    ]

    # Active indicator
    st.markdown("""
    <div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
        <span style='width:10px;height:10px;background:#4ade80;border-radius:50%;
                     display:inline-block;animation:pulse 1.5s infinite;'></span>
        <span style='color:#4ade80;font-weight:600;font-size:14px;'>Running on Railway server</span>
    </div>
    """, unsafe_allow_html=True)

    # Log box
    log_html = "<div class='log-box'>"
    for time, msg in logs:
        emoji = msg.split()[0]
        color = LOG_COLORS.get(emoji, "#d1d5db")
        log_html += (
            f"<div style='margin-bottom:6px;'>"
            f"<span style='color:#4b5563;'>[{time}]</span> "
            f"<span style='color:{color};'>{msg}</span>"
            f"</div>"
        )
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

    # Notice
    st.warning(
        "⚙️ **To activate real 24/7 logs:** Deploy `scheduler.py` to Railway or Render. "
        "The scheduler runs every 30 mins, writes logs to PostgreSQL, and this dashboard "
        "reads them live via `GET /api/botlog/{client_id}`."
    )


# ─────────────────────────────────────────────────────────────────────────────
# tabs/profile_tab.py
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st   # noqa: F811  (re-import for standalone file)


def render():            # noqa: F811
    p = st.session_state.profile

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("#### 👤 Your Profile")
        fields = [
            ("Name",                           p["name"],              ""),
            ("Email (used in all apps)",        p["email"],             "color:#4ade80;font-weight:600;"),
            ("Phone",                          p.get("phone", "—"),    ""),
            ("Location",                       p.get("location", "—"), ""),
        ]
        for label, value, style in fields:
            st.markdown(
                f"<p style='color:#6b7280;font-size:12px;margin:0;'>{label}</p>"
                f"<p style='{style}font-size:14px;margin:0 0 10px;color:#f9fafb;'>{value}</p>",
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown(f"#### 🎯 Target Roles ({len(p['roles'])})")
        tags_html = " ".join(
            f"<span style='background:#2e1065;color:#c4b5fd;border:1px solid #5b21b6;"
            f"padding:4px 12px;border-radius:9999px;font-size:12px;margin:2px;'>{r}</span>"
            for r in p["roles"]
        )
        st.markdown(f"<div style='line-height:2.4;'>{tags_html}</div>", unsafe_allow_html=True)

    st.markdown("#### 📄 Base Resume")
    st.text_area(
        "base_resume_view",
        value=p["resume_text"],
        height=260,
        disabled=True,
        label_visibility="collapsed",
    )
