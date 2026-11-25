# SarkariSewa.gov.in — AI-Powered Civic Triage & Municipal Accountability Platform

**SarkariSewa AI** is a white-label, multi-tenant GovTech platform designed to bridge the transparency gap between citizens and municipal authorities. Built with a responsive `india.gov.in` interface and a WhatsApp-style conversational grievance assistant, it automates civic issue auditing, prevents duplicate tickets via geo-spatial clustering, enforces contractor warranty liability, and requires AI-verified Before/After photographic proof for grievance closure.

---

## Key Features

### 1. Citizen Transparency & WhatsApp-Style Civic Assistant
- **Conversational Reporting:** Citizens report road potholes, uncollected garbage, hanging electric wires, or waterlogging via a simple chat interface in Hindi or English.
- **AI Spam & Authenticity Filter:** Gemini 2.5 Flash Vision verifies uploaded street photos and rejects irrelevant or fake submissions before database entry.
- **Public Ward Accountability Ledger:** Displays the empanelled contractor, sanctioned budget, performance rating, and Defect Liability Warranty expiration date for every ward.
- **Citizen Re-Open Veto:** If an issue is prematurely closed, citizens can contest and re-open the ticket, automatically escalating severity to Level 10/10.

### 2. Multi-Agent AI & Geo-Spatial Intelligence
- **Context-Aware Severity Scoring (1–10):** Automatically boosts priority for hazards near hospitals, schools, and major junctions.
- **150m Geo-Cluster Deduplication:** Merges multiple citizen reports of the same issue within a 150-meter radius using Haversine distance, boosting the **Citizen Impact Count** instead of flooding officers with duplicate tickets.
- **Automated Bilingual Work Orders:** Groq (`llama-3.3-70b-versatile`) generates structured English + Hindi municipal dispatch memos with strict SLA deadlines (`2h` / `24h` / `72h`).

### 3. Secured Government Department Command Center
- **Officer Authentication & Registration:** Role-based sign-in and new departmental officer registration (`SHA-256` credential hashing).
- **Interactive Geo-Spatial Severity Map:** Live color-coded city map showing active, critical, and resolved civic hazards.
- **AI-Verified Before/After Closure:** Officers must upload post-repair site photographs; Vision AI compares Before and After evidence before approving closure.
- **Top-10 Public Notice Ticker & RTI Export:** Live scrolling municipal advisories and one-click CSV export for RTI and audit compliance.

---

## Tech Stack
- **Frontend & UI:** Streamlit, Custom Responsive HTML/CSS (`india.gov.in` Design System), Leaflet.js
- **Vision & Multimodal AI:** Google Gemini API (`gemini-2.5-flash`)
- **Fast Text & Bilingual Dispatch:** Groq API (`llama-3.3-70b-versatile`)
- **Database & Geo-Spatial Engine:** SQLite3, Haversine Spatial Clustering, White-Label JSON Config (`city_config.json`)

---

## Local Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/](https://github.com/)<sahil02171>/sarkarisewa-ai.git
   cd sarkarisewa-ai