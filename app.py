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
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""

# -------------------- FULL-WIDTH RESPONSIVE + ANTI-DARK-MODE CSS --------------------
st.markdown("""
<style>
    /* Force crisp Light Theme across all mobile/desktop browsers */
    header[data-testid="stHeader"] { display: none !important; }
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #F4F6F9 !important;
        color: #0F172A !important;
    }
    .stApp p, .stApp label, .stApp span, .stApp div, .stMarkdown, .stCaption {
        color: #0F172A;
    }
    /* Fix Streamlit inputs on mobile dark browsers */
    input, textarea, select, [data-baseweb="select"] > div, [data-baseweb="input"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: #FFFFFF !important;
        border: 1.5px dashed #94A3B8 !important;
        color: #0F172A !important;
    }
    .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-top: 0rem !important;
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
        padding-bottom: 2.5rem !important;
    }

    /* India.gov.in Top White Navbar */
    .india-nav {
        background: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
        padding: 12px 22px;
        margin-left: -1.4rem;
        margin-right: -1.4rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .india-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .india-logo-text {
        font-size: 1.45rem;
        font-weight: 800;
        color: #1E3A8A !important;
        letter-spacing: -0.3px;
        line-height: 1.1;
    }
    .india-logo-text span { color: #D97706 !important; }
    .india-logo-sub {
        font-size: 0.74rem;
        color: #475569 !important;
        font-weight: 600;
    }
    .india-nav-right {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.8rem;
        color: #334155 !important;
        font-weight: 600;
    }
    .nav-red-btn {
        background: #DC2626;
        color: #FFFFFF !important;
        padding: 5px 12px;
        border-radius: 5px;
        font-weight: 700;
        font-size: 0.76rem;
    }
    .tricolor-accent {
        width: 24px;
        height: 16px;
        background: linear-gradient(180deg, #FF9933 33%, #FFFFFF 33%, #FFFFFF 66%, #138808 66%);
        border: 1px solid #CBD5E1;
        border-radius: 2px;
    }

    /* Search Panel Box */
    .search-banner {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 12px;
        margin-bottom: 12px;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
    }

    /* Hero Banner + Quote Card */
    .hero-banner {
        background: linear-gradient(120deg, #1E1B4B 0%, #312E81 55%, #1E3A8A 100%);
        margin-left: -1.4rem;
        margin-right: -1.4rem;
        padding: 24px 28px 50px 28px;
    }
    .quote-card-wrap {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 18px 24px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.1);
        border: 1px solid #E2E8F0;
        display: flex;
        align-items: center;
        gap: 18px;
        margin-top: -38px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    .quote-avatar {
        width: 66px;
        height: 66px;
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
        font-size: 0.96rem;
        font-weight: 600;
        color: #1E293B !important;
        line-height: 1.5;
        flex: 1;
        min-width: 240px;
    }
    .quote-mark { color: #DC2626 !important; font-size: 1.3rem; font-weight: 900; }
    .quote-meta { font-size: 0.78rem; color: #64748B !important; margin-top: 5px; font-weight: 600; }

    /* Stats Strip */
    .stats-strip {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
        gap: 12px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
        margin-bottom: 14px;
    }
    .stat-item { border-right: 1px solid #F1F5F9; padding: 4px 8px; }
    .stat-item:last-child { border-right: none; }
    .stat-num { font-size: 1.38rem; font-weight: 800; color: #0F172A !important; }
    .stat-lbl { font-size: 0.78rem; color: #475569 !important; font-weight: 600; }

    /* Moving Public Notice Bar */
    .marquee-container {
        background: #FFFBEB;
        border: 1px solid #F59E0B;
        border-left: 6px solid #DC2626;
        border-radius: 6px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .marquee-label {
        background: #DC2626;
        color: #FFFFFF !important;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 4px 9px;
        border-radius: 4px;
        white-space: nowrap;
    }
    .marquee-track { width: 100%; overflow: hidden; white-space: nowrap; }
    .marquee-content {
        display: inline-block;
        padding-left: 100%;
        animation: scrollLeft 34s linear infinite;
        font-size: 0.84rem;
        font-weight: 600;
        color: #7F1D1D !important;
    }
    .marquee-content:hover { animation-play-state: paused; }
    @keyframes scrollLeft {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }

    /* Gateway Cards */
    .services-banner {
        background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
        padding: 18px 22px;
        border-radius: 10px;
        margin-bottom: 14px;
    }
    .services-banner h2 { margin: 0 0 4px 0; font-size: 1.4rem; font-weight: 800; color: #FFFFFF !important; }
    .services-banner p { margin: 0; font-size: 0.86rem; color: #FEE2E2 !important; }
    .portal-box {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-top: 5px solid #1E3A8A;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        margin-bottom: 10px;
        animation: fadeSlideUp 0.45s ease-out;
    }
    .portal-box-gov { border-top-color: #DC2626; }
    .portal-tag { font-size: 0.72rem; font-weight: 800; color: #DC2626 !important; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 5px; }
    .portal-heading { font-size: 1.25rem; font-weight: 800; color: #0F172A !important; margin-bottom: 8px; }
    .portal-body { font-size: 0.88rem; color: #334155 !important; line-height: 1.5; }

    /* Animated Officer Auth Card */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .auth-hero-card {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
        border-bottom: 4px solid #F59E0B;
        animation: fadeSlideUp 0.4s ease-out;
    }
    .auth-hero-card h3 { color: #FFFFFF !important; margin: 0 0 4px 0; font-size: 1.25rem; font-weight: 800; }
    .auth-hero-card p { color: #CBD5E1 !important; margin: 0; font-size: 0.84rem; }

    /* Clean Simple Citizen Form Card */
    .citizen-card {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-top: 5px solid #075E54;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
        animation: fadeSlideUp 0.4s ease-out;
    }
    .warranty-strip {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 4px solid #16A34A;
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 0.82rem;
        color: #14532D !important;
        margin-bottom: 12px;
    }
    .section-heading {
        font-size: 1.08rem;
        font-weight: 800;
        color: #0F172A !important;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
        margin-bottom: 12px;
    }

    @media (max-width: 768px) {
        .block-container { padding-left: 0.7rem !important; padding-right: 0.7rem !important; }
        .india-nav { margin-left: -0.7rem; margin-right: -0.7rem; padding: 10px 12px; }
        .hero-banner { margin-left: -0.7rem; margin-right: -0.7rem; padding: 18px 14px 44px 14px; }
        .quote-card-wrap { padding: 14px; }
        .india-logo-text { font-size: 1.25rem; }
    }
</style>
""", unsafe_allow_html=True)

# -------------------- TOP INDIA.GOV.IN NAVBAR --------------------
st.markdown(f"""
<div class="india-nav">
    <div class="india-brand">
        <svg width="34" height="40" viewBox="0 0 64 76" fill="none" xmlns="http://www.w3.org/2000/svg">
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
        <span class="nav-red-btn">NIC VERIFIED</span>
        <span>अ / A</span>
        <div class="tricolor-accent"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------- WORKING INTERACTIVE SEARCH BAR (TICKET ID OR WARD) --------------------
all_rows = fetch_all_complaints()

with st.container():
    st.markdown('<div class="search-banner">', unsafe_allow_html=True)
    s_col1, s_col2, s_col3 = st.columns([3.2, 1.4, 1])
    q_input = s_col1.text_input(
        "Search Portal",
        value=st.session_state["search_query"],
        placeholder="Search by Ticket ID (e.g., SS-2026-101) or Ward No / Name (e.g., Ward 28, Boring Road)...",
        label_visibility="collapsed"
    )
    ward_filter_options = ["All Wards"] + [w["name"] for w in city_cfg["wards"]]
    quick_ward = s_col2.selectbox("Quick Ward Filter", ward_filter_options, label_visibility="collapsed")
    search_clicked = s_col3.button("Search", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Trigger search if button clicked, text typed, or specific ward chosen from dropdown
    active_search = q_input.strip() if (search_clicked or q_input.strip()) else (quick_ward if quick_ward != "All Wards" else "")
    if active_search:
        st.session_state["search_query"] = q_input.strip()
        matches = [
            r for r in all_rows
            if active_search.lower() in r[1].lower() or active_search.lower() in r[4].lower() or active_search.lower() in r[7].lower()
        ]
        with st.container(border=True):
            sh1, sh2 = st.columns([4, 1])
            sh1.markdown(f"**Search Results for `{active_search}` — Total Complaints Found: `{len(matches)}`**")
            if sh2.button("Clear Search", use_container_width=True):
                st.session_state["search_query"] = ""
                st.rerun()

            if not matches:
                st.info("No complaints matched your search. Try searching `SS-2026-101`, `Ward 28`, `Ward 22`, or `Ward 41`.")
            else:
                m_active = sum(1 for m in matches if m[18] != "Resolved")
                m_resolved = sum(1 for m in matches if m[18] == "Resolved")
                sm1, sm2, sm3 = st.columns(3)
                sm1.metric("Total Complaints", len(matches))
                sm2.metric("Active / Pending", m_active)
                sm3.metric("Resolved", m_resolved)

                for m in matches:
                    st.markdown(
                        f"• **`{m[1]}`** | **{m[7]}** — *{m[4]}* | Status: **`{m[18]}`** | Severity: `{m[8]}/10` | Citizens Affected: `{m[17]}`"
                    )

# Live Stats Calculation
total_tickets = len(all_rows)
active_tickets = sum(1 for r in all_rows if r[18] != "Resolved")
duplicates_prevented = sum(max(0, r[17] - 1) for r in all_rows)
resolved_tickets = sum(1 for r in all_rows if r[18] == "Resolved")
citizen_engagements = sum(r[17] for r in all_rows)

# -------------------- HERO BANNER + OVERLAPPING QUOTE CARD + 6 STATS --------------------
st.markdown(f"""
<div class="hero-banner">
    <div style="font-size:0.76rem; color:#FDBA74 !important; font-weight:700; letter-spacing:1px; text-transform:uppercase;">
        {city_cfg['ministry_header']}
    </div>
    <div style="font-size:1.5rem; font-weight:800; color:#FFFFFF !important; margin-top:4px;">
        Unified Municipal Civic Redressal & Public Accountability Grid
    </div>
</div>

<div class="quote-card-wrap">
    <div class="quote-avatar">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#92400E" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
        </svg>
        <span style="font-size:0.58rem; font-weight:800; color:#78350F !important;">GOV.IN</span>
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
    <div class="stat-item"><div class="stat-num">5</div><div class="stat-lbl">Online Civic Services</div></div>
    <div class="stat-item"><div class="stat-num">{len(city_cfg['wards'])}</div><div class="stat-lbl">Municipal Wards</div></div>
    <div class="stat-item"><div class="stat-num">{citizen_engagements}</div><div class="stat-lbl">Citizen Engagements</div></div>
    <div class="stat-item"><div class="stat-num">{active_tickets}</div><div class="stat-lbl">Active Grievances</div></div>
    <div class="stat-item"><div class="stat-num">{duplicates_prevented}</div><div class="stat-lbl">Duplicates Merged</div></div>
    <div class="stat-item"><div class="stat-num">{resolved_tickets}</div><div class="stat-lbl">AI-Verified Closures</div></div>
</div>
""", unsafe_allow_html=True)

# -------------------- TOP-10 MOVING PUBLIC NOTICE TICKER --------------------
top_notices = get_top_10_broadcasts()
if top_notices:
    ticker_items = " &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; ".join(
        [f"[{idx+1}] {n[2]} ({n[1]}): {n[3]}" for idx, n in enumerate(top_notices)]
    )
    t_col1, t_col2 = st.columns([5.5, 1.2])
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
            <div class="portal-heading">Citizen Civic Grievance & Tracking Portal</div>
            <div class="portal-body">
                Register road potholes, uncollected garbage, hanging electric wires, or waterlogging in 3 simple steps.
                View ward contractor warranty records and track live resolutions with Before/After proof.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Citizen Grievance & Tracking Portal", type="primary", use_container_width=True):
            st.session_state["active_view"] = "citizen"
            st.rerun()

    with g_col2:
        st.markdown("""
        <div class="portal-box portal-box-gov">
            <div class="portal-tag">GOVERNMENT & MUNICIPAL ADMINISTRATION</div>
            <div class="portal-heading">Department Command Center & Audit Dashboard</div>
            <div class="portal-body">
                Secured portal for Municipal Commissioners, Ward Engineers, and Department Officers. Access live geo-spatial
                heatmaps, verify Before/After closure proofs, publish public notices, and export RTI logs.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Government Department Portal (Officer Login / Register)", use_container_width=True):
            st.session_state["active_view"] = "gov"
            st.rerun()

# ==================== VIEW 2: SIMPLE & ATTRACTIVE CITIZEN PORTAL ====================
elif st.session_state["active_view"] == "citizen":
    nav1, nav2 = st.columns([1.2, 5])
    if nav1.button("Back to Home", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    nav2.markdown("#### Online Services > Citizen Civic Grievance & Tracking Portal")
    st.divider()

    c_left, c_right = st.columns([1.15, 1], gap="large")

    # Left: Simple, Clean, Mobile-Friendly Citizen Complaint Card
    with c_left:
        st.markdown('<div class="citizen-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Register a Civic Complaint (3 Simple Steps)</div>', unsafe_allow_html=True)

        ward_names = [w["name"] for w in city_cfg["wards"]]
        selected_ward = st.selectbox("1. Select Your Ward / Area", ward_names)
        ward_meta = get_ward_contractor_info(selected_ward)

        st.markdown(f"""
        <div class="warranty-strip">
            <b>Accountable Contractor:</b> {ward_meta['contractor']} (Rating: {ward_meta['rating']}/5) &nbsp;|&nbsp;
            <b>Warranty Valid Till:</b> <code>{ward_meta['warranty_valid_till']}</code>
        </div>
        """, unsafe_allow_html=True)

        issue_choice = st.selectbox("2. Choose Issue Type", [
            "Pothole & Road Damage",
            "Garbage Overflow",
            "Hanging Electric Wire",
            "Waterlogging & Drain Block",
            "Streetlight Failure"
        ])

        user_note = st.text_area(
            "3. Describe Location / Problem (Hindi or English)",
            height=90,
            placeholder="e.g., Hospital gate ke samne sadak par bada gaddha hai..."
        )

        uploaded_img = st.file_uploader("4. Attach Photo Proof (Optional — JPG / PNG)", type=["jpg", "jpeg", "png"])

        if st.button("Submit Complaint to Municipal AI", type="primary", use_container_width=True):
            final_note = f"{issue_choice}: {user_note.strip()}" if user_note.strip() else f"{issue_choice} reported at {selected_ward}."
            img_bytes = uploaded_img.read() if uploaded_img else None

            with st.spinner("AI Auditor verifying issue & generating official work order..."):
                vision_out, work_order_txt = analyze_civic_issue(img_bytes, final_note, selected_ward)

            if not vision_out.get("is_valid_civic_issue", True):
                st.error(f"Rejected by AI Authenticity Filter: {vision_out.get('rejection_reason', 'Please upload a valid civic photo.')}")
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
                st.session_state["citizen_receipt"] = {
                    "vision": vision_out,
                    "work_order": work_order_txt,
                    "db": db_res,
                    "contractor": ward_meta["contractor"]
                }

        if "citizen_receipt" in st.session_state:
            rec = st.session_state["citizen_receipt"]
            v = rec["vision"]
            d = rec["db"]
            st.success(f"Complaint Registered! Reference ID: {d['ticket_code']} | Routed to: {v['department']}")
            if d["merged"]:
                st.info(f"Merged with nearby report ({d['ticket_code']}). Citizens Affected count is now {d['impact_count']}.")
            st.write(f"**Severity:** `{v['severity']}/10` | **Contractor:** `{rec['contractor']}`")
            with st.expander("View Bilingual Official Work Order"):
                st.code(rec["work_order"], language="markdown")

        st.markdown('</div>', unsafe_allow_html=True)

    # Right: Clean Ticket Tracking & Re-Open Veto
    with c_right:
        st.markdown('<div class="citizen-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Track Your Complaint Status</div>', unsafe_allow_html=True)
        st.caption("Sample IDs: SS-2026-101, SS-2026-102, SS-2026-103, SS-2026-104")
        track_id = st.text_input("Enter Complaint Reference ID", value="SS-2026-104")

        if track_id.strip():
            ticket = get_complaint_by_ticket(track_id)
            if not ticket:
                st.warning("No complaint found with this Reference ID.")
            else:
                (
                    tid, tcode, created, sla, tward, tcat, tsev, tdept,
                    tcontractor, twarranty, tsum, two, tclosure, timpact,
                    tstatus, treopen, b_img, a_img
                ) = ticket

                st.markdown(f"**Ticket ID:** `{tcode}` | **Status:** `{tstatus}` | **Citizens Affected:** `{timpact}`")
                st.write(f"**Ward:** {tward}")
                st.write(f"**Department:** {tdept} | **SLA Deadline:** `{sla}`")
                st.write(f"**Contractor:** {tcontractor}")
                st.write(f"**Details:** {tsum}")

                if tclosure:
                    st.success(f"AI Closure Verification: {tclosure}")

                if b_img or a_img:
                    ic1, ic2 = st.columns(2)
                    if b_img:
                        ic1.image(base64.b64decode(b_img), caption="Before (Citizen Photo)", use_container_width=True)
                    if a_img:
                        ic2.image(base64.b64decode(a_img), caption="After (Officer Proof)", use_container_width=True)

                if tstatus == "Resolved":
                    if st.button(f"Not Satisfied? Re-Open Complaint ({tcode})", key=f"reopen_{tcode}", use_container_width=True):
                        reopen_complaint_by_citizen(tcode)
                        st.error(f"Complaint {tcode} RE-OPENED and escalated to Municipal Commissioner (Severity 10/10).")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== VIEW 3: ANIMATED & SECURED GOVERNMENT PORTAL ====================
elif st.session_state["active_view"] == "gov":
    nav1, nav2 = st.columns([1.2, 5])
    if nav1.button("Back to Home", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()

    if st.session_state["gov_officer"] is None:
        nav2.markdown("#### Online Services > Government Department Portal")

        st.markdown("""
        <div class="auth-hero-card">
            <h3>Municipal Command Center — Secured Officer Gateway</h3>
            <p>Authorized personnel sign-in and departmental onboarding portal (NIC Encryption Standard)</p>
        </div>
        """, unsafe_allow_html=True)

        auth_tab1, auth_tab2 = st.tabs(["Authorized Officer Sign-In", "New Department Officer Registration"])

        with auth_tab1:
            with st.container(border=True):
                st.info("Demo Login Credentials — Officer ID: `PMC-ADMIN-01` | Password: `Gov@2026`")
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

        with auth_tab2:
            with st.container(border=True):
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
                if st.button("Register Departmental Account", type="primary", use_container_width=True):
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
                <style>body {{ margin:0; padding:0; }} #map {{ height: 350px; width: 100%; border-radius: 6px; border: 1px solid #CBD5E1; }}</style>
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
            components.html(leaflet_html, height=360)

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
                    st.write(f"**Department:** {rdept} | **Severity:** {rsev}/10 | **Status:** `{rstatus}`")
                    st.write(f"**Contractor:** {rcontractor} | **Liability:** `{rwarranty}`")
                    st.write(f"**SLA Deadline:** `{sla}` | **Citizen Re-Opens:** `{rreopen}`")
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