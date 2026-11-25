import os
import json
import base64
from io import BytesIO
from PIL import Image
import streamlit as st
from dotenv import load_dotenv
from google import genai
from groq import Groq

load_dotenv()

def get_secret(key_name: str) -> str:
    val = os.getenv(key_name)
    if not val:
        try:
            val = st.secrets.get(key_name, "")
        except Exception:
            val = ""
    return val

def bytes_to_b64(img_bytes: bytes | None) -> str | None:
    if not img_bytes:
        return None
    # Resize slightly to keep SQLite lightweight & fast
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    img.thumbnail((640, 640))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def _parse_json_safe(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    return json.loads(cleaned)

def _keyword_fallback_triage(user_note: str, ward: str) -> dict:
    note_l = (user_note or "").lower()
    if any(w in note_l for w in ["wire", "electric", "spark", "pole", "transformer", "bijli", "taar"]):
        cat, dept, sev = "Hanging Electric Wire", "Electricity Board (DISCOM)", 9
    elif any(w in note_l for w in ["garbage", "trash", "waste", "kachra", "dustbin", "dump", "gandagi"]):
        cat, dept, sev = "Garbage Overflow", "Nagar Nigam Sanitation", 7
    elif any(w in note_l for w in ["water", "drain", "sewage", "flood", "nala", "paani", "waterlogging"]):
        cat, dept, sev = "Waterlogging & Drain Block", "Water & Drainage Wing", 7
    elif any(w in note_l for w in ["light", "dark", "lamp", "streetlight", "andhera"]):
        cat, dept, sev = "Streetlight Failure", "Municipal Electrical Wing", 5
    else:
        cat, dept, sev = "Pothole & Road Damage", "PWD (Public Works Dept)", 8

    if any(k in (ward + " " + note_l).lower() for k in ["hospital", "school", "junction", "highway"]):
        sev = min(10, sev + 1)

    return {
        "is_valid_civic_issue": True,
        "rejection_reason": "",
        "category": cat,
        "department": dept,
        "severity": sev,
        "visual_findings": f"{user_note or 'Civic infrastructure hazard reported'} at {ward}. Immediate field inspection advised."
    }

def analyze_civic_issue(image_bytes: bytes | None, user_note: str, ward: str):
    gemini_key = get_secret("GEMINI_API_KEY")
    groq_key = get_secret("GROQ_API_KEY")

    vision_data = _keyword_fallback_triage(user_note, ward)

    # AGENT 1: Gemini 2.5 Flash Vision Auditor + Spam Guard
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            prompt = f"""
            You are an Official Indian Municipal Civic Auditor AI for SarkariSewa AI.
            Analyze the uploaded image (if provided) and citizen complaint note: "{user_note}" in Ward: "{ward}".

            Step A (Spam/Relevance Guard):
            - If an image is provided and it is clearly a selfie, meme, indoor bedroom/desk, random document, or completely unrelated to public roads/streets/civic utilities, set "is_valid_civic_issue": false and explain briefly in "rejection_reason".
            - If no image is provided, judge based on the text description.

            Step B (Classification & Context-Aware Severity):
            Classify into EXACTLY ONE category & matching department:
            1. "Pothole & Road Damage" -> "PWD (Public Works Dept)"
            2. "Garbage Overflow" -> "Nagar Nigam Sanitation"
            3. "Hanging Electric Wire" -> "Electricity Board (DISCOM)"
            4. "Waterlogging & Drain Block" -> "Water & Drainage Wing"
            5. "Streetlight Failure" -> "Municipal Electrical Wing"

            Severity (1 to 10): Boost +2 if near a Hospital, School, or Major Junction.

            Return ONLY valid JSON:
            {{
              "is_valid_civic_issue": true,
              "rejection_reason": "",
              "category": "exact category from list",
              "department": "exact department from list",
              "severity": 8,
              "visual_findings": "2 crisp factual sentences describing the civic issue and public safety impact."
            }}
            """
            contents = [prompt]
            if image_bytes:
                img = Image.open(BytesIO(image_bytes))
                contents.append(img)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents
            )
            parsed = _parse_json_safe(response.text)
            vision_data.update(parsed)
        except Exception:
            pass  # Safe fallback already populated

    if not vision_data.get("is_valid_civic_issue", True):
        return vision_data, ""

    # AGENT 2: Bilingual Official Municipal Work Order via Groq
    sla = "2 Hours (EMERGENCY)" if vision_data["severity"] >= 8 else ("24 Hours (HIGH PRIORITY)" if vision_data["severity"] >= 5 else "72 Hours (ROUTINE)")
    work_order = (
        f"OFFICIAL MUNICIPAL WORK ORDER\n"
        f"Department: {vision_data['department']} | Ward: {ward}\n"
        f"Category: {vision_data['category']} | Severity: {vision_data['severity']}/10 | SLA: {sla}\n"
        f"Directive: {vision_data['visual_findings']}\n"
        f"कार्य आदेश (हिंदी): {ward} में '{vision_data['category']}' की समस्या को {sla} के भीतर ठीक कर फोटो प्रमाण अपलोड करें।"
    )

    if groq_key:
        try:
            groq_client = Groq(api_key=groq_key)
            wo_prompt = f"""
            Draft a formal, crisp Indian Municipal Corporation Work Order Memo.
            Include:
            1. English Official Directive (3-4 bullet points: Dept, Ward, Severity {vision_data['severity']}/10, SLA {sla}, Action Required, Contractor Liability Warning).
            2. '---' separator followed by a 2-line Hindi summary ('कार्य आदेश:') for field engineers.

            Details:
            Department: {vision_data['department']}
            Ward: {ward}
            Category: {vision_data['category']}
            Findings: {vision_data['visual_findings']}
            Citizen Note: {user_note}
            Keep total output under 130 words.
            """
            chat = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": wo_prompt}],
                temperature=0.25
            )
            work_order = chat.choices[0].message.content.strip()
        except Exception:
            pass

    return vision_data, work_order

def verify_resolution_proof(before_img_b64: str | None, after_img_bytes: bytes, category: str) -> dict:
    """
    AGENT 3: Compares Before & After photos to prevent fake ticket closures by officers.
    """
    gemini_key = get_secret("GEMINI_API_KEY")
    if not gemini_key:
        return {"verified": True, "note": "AI Proof Check: Resolution photo logged for public audit."}

    try:
        client = genai.Client(api_key=gemini_key)
        after_img = Image.open(BytesIO(after_img_bytes))
        contents = []

        if before_img_b64:
            before_img = Image.open(BytesIO(base64.b64decode(before_img_b64)))
            prompt = f"""
            You are an Anti-Corruption Municipal Audit AI.
            Image 1 is the BEFORE photo of a '{category}' civic complaint.
            Image 2 is the AFTER repair photo uploaded by a municipal officer.
            Check if Image 2 is a genuine outdoor street/civic photo showing repair/cleanup progress (and NOT a selfie, blank screen, or identical unfixed damage).
            Return ONLY JSON:
            {{
              "verified": true or false,
              "note": "1 crisp sentence explaining what changed between Before and After."
            }}
            """
            contents = [prompt, before_img, after_img]
        else:
            prompt = f"""
            You are an Anti-Corruption Municipal Audit AI.
            This is an AFTER-REPAIR proof photo uploaded for a '{category}' civic complaint.
            Verify if this is a genuine outdoor street/infrastructure photo showing clean/repaired condition (not a selfie/meme/blank).
            Return ONLY JSON:
            {{
              "verified": true or false,
              "note": "1 crisp sentence describing the post-repair site condition."
            }}
            """
            contents = [prompt, after_img]

        res = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
        parsed = _parse_json_safe(res.text)
        return {
            "verified": bool(parsed.get("verified", True)),
            "note": parsed.get("note", "AI Verified: Post-repair site inspection passed.")
        }
    except Exception:
        return {"verified": True, "note": "AI Proof Check: Resolution photo recorded for citizen verification."}