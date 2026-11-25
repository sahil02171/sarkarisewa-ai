import io
import csv
import json
import base64
import streamlit as st
import streamlit.components.v1 as components
from db import (
    init_db,
    init_officer_auth,
    load_city_config,
    get_ward_contractor_info,
    save_or_merge_complaint,
    fetch_all_complaints,
    get_complaint_by_ticket,
    reopen_complaint_by_citizen,
    resolve_complaint_with_proof,
    create_broadcast,
    get_top_10_broadcasts,
    register_officer,
    verify_officer_login,
)
from agents import analyze_civic_issue, bytes_to_b64, verify_resolution_proof

st.set_page_config(
    page_title="SarkariSewa.gov.in | National Civic Grievance & Governance Portal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_db()
init_officer_auth()
city_cfg = load_city_config()

# Session States
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "home"  # 'home' | 'citizen' | 'gov'
if "show_all_notices" not in st.session_state:
    st.session_state["show_all_notices"] = False
if "gov_officer" not in st.session_state:
    st.session_state["gov_officer"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# -------------------- FULL-WIDTH INDIA.GOV.IN & WHATSAPP CHAT CSS --------------------
st.markdown("""
<style>
    /* Force 100% Full-Width Edge-to-Edge across Mobile, Tablet, Laptop & Desktop */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    .stApp {
        background-color: #F4F6F9;
    }
    .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-top: 0rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* India.gov.in Top White Navbar */
    .india-nav {
        background: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
        padding: 12px 24px;
        margin-left: -1.5rem;
        margin-right: -1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .india-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .india-logo-text {
        font-size: 1.55rem;
        font-weight: 800;
        color: #1E3A8A;
        letter-spacing: -0.3px;
        line-height: 1.1;
    }
    .india-logo-text span {
        color: #D97706;
    }
    .india-logo-sub {
        font-size: 0.74rem;
        color: #475569;
        font-weight: 600;
    }
    .india-nav-right {
        display: flex;
        align-items: center;
        gap: 14px;
        font-size: 0.82rem;
        color: #334155;
        font-weight: 600;
        flex-wrap: wrap;
    }
    .nav-search-pill {
        background: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 6px 14px;
        color: #64748B;
        font-size: 0.82rem;
        min-width: 210px;
    }
    .nav-red-btn {
        background: #DC2626;
        color: #FFFFFF;
        padding: 6px 16px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.82rem;
    }
    .tricolor-accent {
        width: 26px;
        height: 18px;
        background: linear-gradient(180deg, #FF9933 33%, #FFFFFF 33%, #FFFFFF 66%, #138808 66%);
        border: 1px solid #CBD5E1;
        border-radius: 2px;
    }

    /* Hero Banner + Overlapping PM Quote Card (Exact india.gov.in style) */
    .hero-banner {
        background: linear-gradient(120deg, #1E1B4B 0%, #312E81 55%, #1E3A8A 100%);
        margin-left: -1.5rem;
        margin-right: -1.5rem;
        padding: 28px 36px 56px 36px;
        color: #FFFFFF;
    }
    .quote-card-wrap {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px 28px;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.12);
        border: 1px solid #E2E8F0;
        display: flex;
        align-items: center;
        gap: 22px;
        margin-top: -42px;
        margin-bottom: 18px;
        flex-wrap: wrap;
    }
    .quote-avatar {
        width: 74px;
        height: 74px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        border: 3px solid #D97706;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .quote-text {
        font-size: 1.02rem;
        font-weight: 600;
        color: #1E293B;
        line-height: 1.5;
        flex: 1;
        min-width: 250px;
    }
    .quote-mark {
        color: #DC2626;
        font-size: 1.35rem;
        font-weight: 900;
    }
    .quote-meta {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 6px;
        font-weight: 600;
    }

    /* 6-Column National Stats Strip */
    .stats-strip {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
        margin-bottom: 16px;
    }
    .stat-item {
        border-right: 1px solid #F1F5F9;
        padding: 4px 10px;
    }
    .stat-item:last-child {
        border-right: none;
    }
    .stat-num {
        font-size: 1.45rem;
        font-weight: 800;
        color: #0F172A;
    }
    .stat-lbl {
        font-size: 0.82rem;
        color: #475569;
        font-weight: 600;
        margin-top: 2px;
    }

    /* Moving Public Notice Bar */
    .marquee-container {
        background: #FFFBEB;
        border: 1px solid #F59E0B;
        border-left: 6px solid #DC2626;
        border-radius: 6px;
        padding: 8px 14px;
        display: flex;
        align-items: center;
        gap: 12px;
        overflow: hidden;
        margin-bottom: 14px;
    }
    .marquee-label {
        background: #DC2626;
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 4px;
        white-space: nowrap;
    }
    .marquee-track {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
    }
    .marquee-content {
        display: inline-block;
        padding-left: 100%;
        animation: scrollLeft 36s linear infinite;
        font-size: 0.86rem;
        font-weight: 600;
        color: #7F1D1D;
    }
    .marquee-content:hover {
        animation-play-state: paused;
    }
    @keyframes scrollLeft {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }

    /* Crimson Online Services Banner + Dual Portal Cards */
    .services-banner {
        background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
        color: #FFFFFF;
        padding: 22px 26px;
        border-radius: 12px;
        margin-bottom: 16px;
    }
    .services-banner h2 {
        margin: 0 0 6px 0;
        font-size: 1.55rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    .services-banner p {
        margin: 0;
        font-size: 0.9rem;
        color: #FEE2E2;
    }
    .portal-box {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-top: 5px solid #1E3A8A;
        border-radius: 10px;
        padding: 22px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        min-height: 225px;
        margin-bottom: 10px;
    }
    .portal-box-gov {
        border-top-color: #DC2626;
    }
    .portal-tag {
        font-size: 0.74rem;
        font-weight: 800;
        color: #DC2626;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-bottom: 6px;
    }
    .portal-heading {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 8px;
    }
    .portal-body {
        font-size: 0.9rem;
        color: #334155;
        line-height: 1.55;
        margin-bottom: 12px;
    }

    /* WhatsApp-Style Conversational Grievance UI */
    .wa-header {
        background: #075E54;
        color: #FFFFFF;
        padding: 12px 18px;
        border-radius: 10px 10px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .wa-header-title {
        font-weight: 700;
        font-size: 1rem;
    }
    .wa-header-sub {
        font-size: 0.75rem;
        color: #A7F3D0;
    }
    .wa-chat-bg {
        background-color: #EFEAE2;
        background-image: radial-gradient(#D5CEC2 1px, transparent 1px);
        background-size: 16px 16px;
        padding: 16px;
        border-left: 1px solid #CBD5E1;
        border-right: 1px solid #CBD5E1;
        max-height: 460px;
        overflow-y: auto;
    }
    .wa-bot-msg {
        background: #FFFFFF;
        color: #111B21;
        padding: 11px 15px;
        border-radius: 0 12px 12px 12px;
        max-width: 85%;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
        font-size: 0.88rem;
        line-height: 1.5;
    }
    .wa-user-msg {
        background: #D9FDD3;
        color: #111B21;
        padding: 11px 15px;
        border-radius: 12px 0 12px 12px;
        max-width: 82%;
        margin-left: auto;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
        font-size: 0.88rem;
        line-height: 1.5;
    }
    .wa-time {
        font-size: 0.68rem;
        color: #667781;
        text-align: right;
        margin-top: 4px;
    }
    .section-heading {
        font-size: 1.12rem;
        font-weight: 800;
        color: #0F172A;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
        margin-bottom: 14px;
    }

    /* Mobile & Tablet Responsive Adjustments */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
        .india-nav {
            margin-left: -0.75rem;
            margin-right: -0.75rem;
            padding: 10px 14px;
        }
        .hero-banner {
            margin-left: -0.75rem;
            margin-right: -0.75rem;
            padding: 20px 16px 46px 16px;
        }
        .quote-card-wrap {
            padding: 14px 16px;
        }
        .wa-bot-msg, .wa-user-msg {
            max-width: 94%;
        }
    }
</style>
""", unsafe_allow_html=True)

# -------------------- TOP INDIA.GOV.IN STYLE NAVBAR --------------------
st.markdown(f"""
<div class="india-nav">
    <div class="india-brand">
        <svg width="36" height="42" viewBox="0 0 64 76" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="32" cy="24" r="14" stroke="#1E3A8A" stroke-width="3.5"/>
            <circle cx="32" cy="24" r="3" fill="#1E3A8A"/>
            <line x1="32" y1="10" x2="32" y2="38" stroke="#1E3A8A" stroke-width="2"/>
            <line x1="18" y1="24" x2="46" y2="24" stroke="#1E3A8A" stroke-width="2"/>
            <line x1="22" y1="14" x2="42" y2="34" stroke="#1E3A8A" stroke-width="1.8"/>
            <line x1="42" y1="14" x2="22" y2="34" stroke="#1E3A8A" stroke-width="1.8"/>
            <rect x="14" y="45" width="36" height="6" rx="2" fill="#1E3A8A"/>
            <rect x="10" y="54" width="44" height="7" rx="2" fill="#FF9933"/>
        </svg>
        <div>
            <div class="india-logo-text">sarkarisewa<span>.gov.in</span></div>
            <div class="india-logo-sub">National Civic Grievance Portal • {city_cfg['city_name']}</div>
        </div>
    </div>
    <div class="india-nav-right">
        <span class="nav-search-pill">Search Wards, Tickets & Services</span>
        <span class="nav-red-btn">NIC VERIFIED</span>
        <span>Skip to main content</span>
        <span>|</span>
        <span>अ / A</span>
        <div class="tricolor-accent"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Fetch live numbers for the 6-column National Portal KPI strip
all_rows = fetch_all_complaints()
total_tickets = len(all_rows)
active_tickets = sum(1 for r in all_rows if r[18] != "Resolved")
critical_tickets = sum(1 for r in all_rows if r[8] >= 8 and r[18] != "Resolved")
duplicates_prevented = sum(max(0, r[17] - 1) for r in all_rows)
resolved_tickets = sum(1 for r in all_rows if r[18] == "Resolved")
citizen_engagements = sum(r[17] for r in all_rows)

# -------------------- HERO BANNER + OVERLAPPING QUOTE CARD + 6 STATS --------------------
st.markdown(f"""
<div class="hero-banner">
    <div style="font-size:0.78rem; color:#FDBA74; font-weight:700; letter-spacing:1px; text-transform:uppercase;">
        {city_cfg['ministry_header']}
    </div>
    <div style="font-size:1.65rem; font-weight:800; margin-top:4px;">
        Unified Municipal Civic Redressal & Public Accountability Grid
    </div>
</div>

<div class="quote-card-wrap">
    <div class="quote-avatar">
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#92400E" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
        </svg>
        <span style="font-size:0.6rem; font-weight:800; color:#78350F;">GOV.IN</span>
    </div>
    <div class="quote-text">
        <span class="quote-mark">“</span>
        India's Digital Public Infrastructure has demonstrated how technology can expand opportunity, improve governance,
        ensure contractor accountability, and deliver transparent civic services to millions of citizens.
        <span class="quote-mark">”</span>
        <div class="quote-meta">Digital India & Smart Cities Mission • {city_cfg['city_name']}</div>
    </div>
</div>

<div class="stats-strip">
    <div class="stat-item">
        <div class="stat-num">5</div>
        <div class="stat-lbl">Online Civic Services</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">{len(city_cfg['wards'])}</div>
        <div class="stat-lbl">Municipal Wards</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">{citizen_engagements}</div>
        <div class="stat-lbl">Citizen Engagements</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">{active_tickets}</div>
        <div class="stat-lbl">Active Grievances</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">{duplicates_prevented}</div>
        <div class="stat-lbl">Duplicates Merged</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">{resolved_tickets}</div>
        <div class="stat-lbl">AI-Verified Closures</div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------- TOP-10 MOVING PUBLIC NOTICE TICKER --------------------
top_notices = get_top_10_broadcasts()
if top_notices:
    ticker_items = " &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; ".join(
        [f"[{idx+1}] {n[2]} ({n[1]}): {n[3]}" for idx, n in enumerate(top_notices)]
    )
    t_col1, t_col2 = st.columns([6, 1])
    with t_col1:
        st.markdown(f"""
        <div class="marquee-container">
            <span class="marquee-label">PUBLIC NOTICES (TOP {len(top_notices)})</span>
            <div class="marquee-track">
                <div class="marquee-content">{ticker_items}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with t_col2:
        btn_label = "Hide Notices" if st.session_state["show_all_notices"] else f"View All ({len(top_notices)})"
        if st.button(btn_label, use_container_width=True):
            st.session_state["show_all_notices"] = not st.session_state["show_all_notices"]
            st.rerun()

if st.session_state["show_all_notices"] and top_notices:
    with st.container(border=True):
        st.markdown("**Official Municipal Public Notice Board (Top 10 Active Circulars)**")
        for idx, n in enumerate(top_notices, start=1):
            st.markdown(f"**{idx}. [{n[2]}]** *(Issued: {n[1]})* — {n[3]}")

# ==================== VIEW 1: FULL-WIDTH ONLINE SERVICES GATEWAY ====================
if st.session_state["active_view"] == "home":
    st.markdown("""
    <div class="services-banner">
        <h2>Online Services</h2>
        <p>Select your portal below — Citizen Grievance & Tracking Wing or Authorized Government Department Command Center</p>
    </div>
    """, unsafe_allow_html=True)

    g_col1, g_col2 = st.columns(2, gap="large")
    with g_col1:
        st.markdown("""
        <div class="portal-box">
            <div class="portal-tag">CITIZEN SERVICES • PUBLIC ACCESS</div>
            <div class="portal-heading">Citizen Civic Assistant & Tracking Portal</div>
            <div class="portal-body">
                Report road potholes, uncollected garbage, hanging electric wires, or waterlogging through a simple
                WhatsApp-style conversational assistant. Inspect ward contractor warranty records and track live resolutions.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Citizen Chat Assistant & Ticket Tracker", type="primary", use_container_width=True):
            st.session_state["active_view"] = "citizen"
            st.rerun()

    with g_col2:
        st.markdown("""
        <div class="portal-box portal-box-gov">
            <div class="portal-tag">GOVERNMENT & MUNICIPAL ADMINISTRATION</div>
            <div class="portal-heading">Department Command Center & Audit Dashboard</div>
            <div class="portal-body">
                Secured portal for Municipal Commissioners, Ward Engineers, and Department Officers. Access live geo-spatial
                heatmaps, verify Before/After photographic closure proofs, publish public notices, and export RTI logs.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Government Department Portal (Officer Sign-In / Register)", use_container_width=True):
            st.session_state["active_view"] = "gov"
            st.rerun()

# ==================== VIEW 2: WHATSAPP-STYLE CITIZEN PORTAL PAGE ====================
elif st.session_state["active_view"] == "citizen":
    nav1, nav2 = st.columns([1.2, 5])
    if nav1.button("Back to Home", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    nav2.markdown("#### Online Services > Citizen Civic Assistant & Public Verification")
    st.divider()

    chat_col, track_col = st.columns([1.2, 1], gap="large")

    # Left: WhatsApp-Style Conversational Grievance Bot
    with chat_col:
        ward_names = [w["name"] for w in city_cfg["wards"]]
        selected_ward = st.selectbox("Step 1: Select Your Municipal Ward / Area", ward_names)
        ward_meta = get_ward_contractor_info(selected_ward)

        # Render WhatsApp Header & Chat Bubbles
        st.markdown(f"""
        <div class="wa-header">
            <div>
                <div class="wa-header-title">SarkariSewa Civic Sahayak (Official AI Bot)</div>
                <div class="wa-header-sub">Online • Instant AI Audit & Municipal Dispatch • {selected_ward}</div>
            </div>
            <div style="font-size:0.75rem; background:rgba(255,255,255,0.16); padding:4px 10px; border-radius:12px;">
                Verified Gov.in
            </div>
        </div>
        <div class="wa-chat-bg">
            <div class="wa-bot-msg">
                <b>Namaste! Welcome to SarkariSewa Civic Assistant.</b><br>
                You selected <b>{selected_ward}</b>.<br>
                • <b>Responsible Contractor:</b> {ward_meta['contractor']} (Rating: {ward_meta['rating']}/5)<br>
                • <b>Road/Civic Warranty:</b> Valid till <code>{ward_meta['warranty_valid_till']}</code> (Budget: {ward_meta['sanctioned_budget']})<br><br>
                Please upload a photo of the problem below or type/tap your issue to register an official complaint.
                <div class="wa-time">AI Sahayak • Ready</div>
            </div>
        """, unsafe_allow_html=True)

        # Show past chat messages in this session
        for msg in st.session_state["chat_history"][-4:]:
            if msg["role"] == "user":
                st.markdown(f'<div class="wa-user-msg">{msg["text"]}<div class="wa-time">Citizen ✓✓</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="wa-bot-msg">{msg["text"]}<div class="wa-time">AI Sahayak • Verified</div></div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Chat Input Controls right below the WhatsApp chat box
        with st.container(border=True):
            uploaded_img = st.file_uploader("Attach Photo Evidence (Optional — JPG/PNG)", type=["jpg", "jpeg", "png"])
            inp_c1, inp_c2 = st.columns([3.5, 1])
            user_msg = inp_c1.text_input("Type a message (Hindi / English)...", label_visibility="collapsed", placeholder="Type message: e.g., Main road par bada gaddha hai...")
            send_clicked = inp_c2.button("Send ➤", type="primary", use_container_width=True)

            st.caption("Quick Tap Issues:")
            q1, q2, q3 = st.columns(3)
            quick_msg = None
            if q1.button("Report Pothole", use_container_width=True):
                quick_msg = "Deep pothole on main road obstructing vehicles."
            if q2.button("Report Live Wire", use_container_width=True):
                quick_msg = "Low-hanging sparking electric wire near Hospital gate."
            if q3.button("Report Garbage", use_container_width=True):
                quick_msg = "Uncollected garbage dump overflowing onto road."

            final_msg = quick_msg if quick_msg else (user_msg if send_clicked else None)
            if final_msg or (send_clicked and uploaded_img):
                text_to_send = final_msg or "Uploaded street photo for civic inspection."
                img_bytes = uploaded_img.read() if uploaded_img else None

                st.session_state["chat_history"].append({"role": "user", "text": text_to_send})

                with st.spinner("AI Sahayak is auditing photo & generating municipal work order..."):
                    vision_out, work_order_txt = analyze_civic_issue(img_bytes, text_to_send, selected_ward)

                if not vision_out.get("is_valid_civic_issue", True):
                    bot_reply = f"<b>Submission Rejected:</b> {vision_out.get('rejection_reason', 'Please upload a valid outdoor civic infrastructure photo.')}"
                else:
                    b64_before = bytes_to_b64(img_bytes)
                    db_res = save_or_merge_complaint(
                        ward=selected_ward,
                        lat=float(ward_meta["lat"]),
                        lon=float(ward_meta["lon"]),
                        category=vision_out["category"],
                        severity=vision_out["severity"],
                        department=vision_out["department"],
                        summary=vision_out["visual_findings"],
                        work_order=work_order_txt,
                        before_img_b64=b64_before
                    )
                    merge_note = (
                        f"Linked to existing nearby report <b>{db_res['ticket_code']}</b> (Citizen Impact Count boosted to <b>{db_res['impact_count']}</b>)."
                        if db_res["merged"]
                        else f"New Official Reference ID: <b>{db_res['ticket_code']}</b>"
                    )
                    bot_reply = (
                        f"<b>Grievance Registered & Dispatched!</b><br>"
                        f"• {merge_note}<br>"
                        f"• <b>Category:</b> {vision_out['category']} (Severity: <b>{vision_out['severity']}/10</b>)<br>"
                        f"• <b>Assigned Dept:</b> {vision_out['department']}<br>"
                        f"• <b>Contractor Liable:</b> {ward_meta['contractor']}<br>"
                        f"• <b>Audit Note:</b> {vision_out['visual_findings']}"
                    )
                    st.session_state["last_work_order"] = work_order_txt

                st.session_state["chat_history"].append({"role": "bot", "text": bot_reply})
                st.rerun()

        if "last_work_order" in st.session_state:
            with st.expander("View Generated Official Bilingual Work Order", expanded=False):
                st.code(st.session_state["last_work_order"], language="markdown")

    # Right: Ticket Tracking & Citizen Re-Open Veto
    with track_col:
        st.markdown('<div class="section-heading">Track Grievance & Public Verification Ledger</div>', unsafe_allow_html=True)
        st.caption("Sample Ticket IDs: SS-2026-101, SS-2026-102, SS-2026-103, SS-2026-104")
        track_id = st.text_input("Enter Grievance Reference ID", value="SS-2026-104")

        if track_id.strip():
            ticket = get_complaint_by_ticket(track_id)
            if not ticket:
                st.warning("No grievance found with this Reference ID.")
            else:
                (
                    tid, tcode, created, sla, tward, tcat, tsev, tdept,
                    tcontractor, twarranty, tsum, two, tclosure, timpact,
                    tstatus, treopen, b_img, a_img
                ) = ticket

                with st.container(border=True):
                    st.markdown(f"**Reference ID:** `{tcode}` &nbsp;|&nbsp; **Status:** `{tstatus}` &nbsp;|&nbsp; **Citizens Affected:** `{timpact}`")
                    st.write(f"**Ward:** {tward}")
                    st.write(f"**Department:** {tdept} &nbsp;|&nbsp; **SLA Deadline:** `{sla}`")
                    st.write(f"**Contractor:** {tcontractor}")
                    st.write(f"**Observation:** {tsum}")

                    if tclosure:
                        st.success(f"AI Closure Audit: {tclosure}")

                    if b_img or a_img:
                        ic1, ic2 = st.columns(2)
                        if b_img:
                            ic1.image(base64.b64decode(b_img), caption="Before (Citizen Evidence)", use_container_width=True)
                        if a_img:
                            ic2.image(base64.b64decode(a_img), caption="After (Officer Proof)", use_container_width=True)

                    if tstatus == "Resolved":
                        if st.button(f"Not Satisfied? Contest & Re-Open ({tcode})", key=f"reopen_{tcode}", use_container_width=True):
                            reopen_complaint_by_citizen(tcode)
                            st.error(f"Ticket {tcode} RE-OPENED and escalated to Municipal Commissioner (Severity 10/10).")
                            st.rerun()

# ==================== VIEW 3: SECURED GOVERNMENT DEPARTMENT PORTAL ====================
elif st.session_state["active_view"] == "gov":
    nav1, nav2 = st.columns([1.2, 5])
    if nav1.button("Back to Home", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()

    if st.session_state["gov_officer"] is None:
        nav2.markdown("#### Online Services > Government Department Portal — Official Authentication")
        st.divider()

        auth_col1, auth_col2 = st.columns(2, gap="large")
        with auth_col1:
            st.markdown('<div class="section-heading">Authorized Officer Sign-In</div>', unsafe_allow_html=True)
            st.caption("Default Evaluation Credentials — Officer ID: `PMC-ADMIN-01` | Password: `Gov@2026`")
            login_id = st.text_input("Government Officer ID", value="PMC-ADMIN-01")
            login_pwd = st.text_input("Secured Password", type="password", value="Gov@2026")
            if st.button("Authenticate & Enter Command Center", type="primary", use_container_width=True):
                officer = verify_officer_login(login_id, login_pwd)
                if officer:
                    st.session_state["gov_officer"] = {
                        "officer_id": officer[0],
                        "full_name": officer[1],
                        "department": officer[2],
                        "designation": officer[3]
                    }
                    st.rerun()
                else:
                    st.error("Authentication Failed: Invalid Officer ID or Password.")

        with auth_col2:
            st.markdown('<div class="section-heading">New Department Officer Registration</div>', unsafe_allow_html=True)
            reg_id = st.text_input("Assign Officer ID (e.g., PWD-JE-04)")
            reg_name = st.text_input("Officer Full Name")
            reg_dept = st.selectbox("Department Wing", [
                "All Departments",
                "PWD (Public Works Dept)",
                "Nagar Nigam Sanitation",
                "Electricity Board (DISCOM)",
                "Water & Drainage Wing",
                "Municipal Electrical Wing"
            ])
            reg_desig = st.text_input("Official Designation (e.g., Executive Engineer)")
            reg_pwd = st.text_input("Create Secured Password (min 6 chars)", type="password")
            if st.button("Register Departmental Account", use_container_width=True):
                ok, msg = register_officer(reg_id, reg_name, reg_dept, reg_desig, reg_pwd)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    else:
        off = st.session_state["gov_officer"]
        h_info, h_logout = st.columns([5, 1])
        h_info.markdown(f"#### Authenticated Session: {off['full_name']} ({off['designation']} — {off['department']})")
        if h_logout.button("Sign Out", use_container_width=True):
            st.session_state["gov_officer"] = None
            st.rerun()
        st.divider()

        gov_left, gov_right = st.columns([1.15, 1], gap="large")

        with gov_left:
            st.markdown('<div class="section-heading">Geo-Spatial Severity & Ward Command Map</div>', unsafe_allow_html=True)
            center = city_cfg["map_center"]
            markers_data = []
            for r in all_rows:
                tcode, ward_n, r_lat, r_lon, cat, sev, dept, contractor, status, impact = (
                    r[1], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[18], r[17]
                )
                pin_hex = "#16A34A" if status == "Resolved" else ("#DC2626" if sev >= 8 else ("#EA580C" if sev >= 6 else "#2563EB"))
                markers_data.append({
                    "lat": r_lat,
                    "lon": r_lon,
                    "color": pin_hex,
                    "popup": f"<b>{tcode}</b> - {cat}<br>Ward: {ward_n}<br>Severity: {sev}/10 | Reports: {impact}<br>Contractor: {contractor}<br>Status: {status}"
                })

            leaflet_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <style>body {{ margin:0; padding:0; }} #map {{ height: 370px; width: 100%; border-radius: 6px; border: 1px solid #CBD5E1; }}</style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    var map = L.map('map').setView([{center['lat']}, {center['lon']}], {center['zoom']});
                    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                        attribution: '&copy; OpenStreetMap &copy; CARTO'
                    }}).addTo(map);
                    var points = {json.dumps(markers_data)};
                    points.forEach(function(p) {{
                        L.circleMarker([p.lat, p.lon], {{
                            radius: 10,
                            fillColor: p.color,
                            color: "#FFFFFF",
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.9
                        }}).addTo(map).bindPopup(p.popup);
                    }});
                </script>
            </body>
            </html>
            """
            components.html(leaflet_html, height=380)

            st.markdown('<div class="section-heading">Public Advisory Broadcast & RTI Audit Export</div>', unsafe_allow_html=True)
            b_col1, b_col2 = st.columns([1, 1.4])
            b_ward = b_col1.selectbox("Target Ward", [w["name"] for w in city_cfg["wards"]], key="b_ward_sel")
            b_msg = b_col2.text_input("Official Advisory Text", placeholder="Enter public safety notice or traffic diversion alert...")

            act_c1, act_c2 = st.columns(2)
            if act_c1.button("Publish Official Public Notice", use_container_width=True):
                if b_msg.strip():
                    create_broadcast(b_ward, b_msg.strip())
                    st.success("Public Advisory published to Top-10 Notice Ticker.")
                    st.rerun()
                else:
                    st.warning("Please enter advisory text before publishing.")

            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf)
            writer.writerow(["Ticket_ID", "Created_At", "SLA_Deadline", "Ward", "Category", "Severity", "Department", "Contractor", "Warranty_Status", "Citizens_Affected", "Status", "Reopen_Count", "AI_Audit_Note"])
            for r in all_rows:
                writer.writerow([r[1], r[2], r[3], r[4], r[7], r[8], r[9], r[10], r[11], r[17], r[18], r[19], r[16]])

            act_c2.download_button(
                label="Download RTI & Audit Ledger (CSV)",
                data=csv_buf.getvalue(),
                file_name="SarkariSewa_Municipal_Audit_Report.csv",
                mime="text/csv",
                use_container_width=True
            )

        with gov_right:
            st.markdown('<div class="section-heading">Departmental Action Queue & Proof-Based Closure</div>', unsafe_allow_html=True)
            departments = ["All Departments"] + sorted(list({r[9] for r in all_rows}))
            default_idx = departments.index(off["department"]) if off["department"] in departments else 0
            selected_dept = st.selectbox("Filter by Concerned Department", departments, index=default_idx)

            filtered_rows = all_rows if selected_dept == "All Departments" else [r for r in all_rows if r[9] == selected_dept]

            for r in filtered_rows:
                (
                    rid, tcode, created, sla, rward, rlat, rlon, rcat,
                    rsev, rdept, rcontractor, rwarranty, rsum, rwo,
                    rb_img, ra_img, rclosure, rimpact, rstatus, rreopen
                ) = r

                priority_label = "CRITICAL" if rsev >= 8 else ("HIGH" if rsev >= 6 else "STANDARD")
                with st.expander(f"[{priority_label}] {tcode} | {rcat} — {rward} ({rimpact} Reports)"):
                    st.write(f"**Department:** {rdept} &nbsp;|&nbsp; **Severity:** {rsev}/10 &nbsp;|&nbsp; **Status:** `{rstatus}`")
                    st.write(f"**Contractor:** {rcontractor} &nbsp;|&nbsp; **Liability:** `{rwarranty}`")
                    st.write(f"**SLA Deadline:** `{sla}` &nbsp;|&nbsp; **Citizen Re-Opens:** `{rreopen}`")
                    st.write(f"**Technical Summary:** {rsum}")

                    st.text_area("Official Dispatch Order", rwo, height=110, key=f"wo_view_{tcode}")

                    if rstatus != "Resolved":
                        st.markdown("**Mandatory AI-Verified Closure Protocol:**")
                        proof_file = st.file_uploader(
                            f"Upload Post-Repair Site Photograph ({tcode})",
                            type=["jpg", "jpeg", "png"],
                            key=f"proof_up_{tcode}"
                        )
                        if st.button(f"Verify Proof & Close Grievance ({tcode})", key=f"close_btn_{tcode}", type="primary"):
                            if not proof_file:
                                st.warning("Official closure requires uploading a post-repair site photograph for AI verification.")
                            else:
                                proof_bytes = proof_file.read()
                                with st.spinner("Running Anti-Corruption Vision Audit on Before/After Evidence..."):
                                    check = verify_resolution_proof(rb_img, proof_bytes, rcat)
                                if not check["verified"]:
                                    st.error(f"AI Audit Rejected Closure: {check['note']}")
                                else:
                                    after_b64 = bytes_to_b64(proof_bytes)
                                    resolve_complaint_with_proof(tcode, after_b64, check["note"])
                                    st.success(f"Closure Verified & Approved: {check['note']}")
                                    st.rerun()
                    else:
                        if rclosure:
                            st.info(f"Verified Closure Record: {rclosure}")