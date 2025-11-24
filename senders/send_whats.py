import time
import re
import pandas as pd
import requests
from typing import Tuple, List, Dict, Any

# ===== Helpers =====

def _normalize_phone(raw: str) -> str:
    """
    Normalize to E.164-like: keep leading + if exists, then digits only.
    Remove spaces, dashes, parentheses.
    """
    raw = str(raw or "").strip()
    if not raw:
        return ""
    plus = raw.startswith("+")
    digits = re.sub(r"[^\d]", "", raw)
    return f"+{digits}" if plus else digits

def _build_session(total_retries: int = 3, backoff: float = 0.8) -> requests.Session:
    """
    Reuse a Session with retry on 429/5xx.
    """
    s = requests.Session()
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retry = Retry(
            total=total_retries,
            backoff_factor=backoff,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
    except Exception:
        # لو المكتبات مش متاحة، نكمل بدون Retry Adapter
        pass
    return s

def _safe_error_text(resp: requests.Response) -> str:
    try:
        j = resp.json()
        if isinstance(j, dict):
            # Graph API عادة بترجع error.message
            return j.get("error", {}).get("message") or str(j)
        return str(j)
    except Exception:
        return resp.text[:500]


# ===== Main sending =====

def send_whatsapp_messages_from_excel(input_file: str, phone_number_id: str, access_token: str) -> str:
    """
    Reads an Excel/CSV file with columns: Phone, WhatsApp_Message
    Sends text messages via WhatsApp Cloud API.
    Returns a human-readable summary string (kept for backward compatibility).
    """
    df = pd.read_excel(input_file) if input_file.lower().endswith(".xlsx") else pd.read_csv(input_file)

    required_columns = ["Phone", "WhatsApp_Message"]
    for col in required_columns:
        if col not in df.columns:
            return f"❌ Missing required column: {col}"

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # إعداد Session + مهلة افتراضية
    session = _build_session()
    timeout = 15  # seconds

    success = 0
    failed = 0
    failed_numbers: List[str] = []
    failed_reasons: List[str] = []

    # واتساب بيقبل نص حتى ~4096 حرف
    MAX_LEN = 4096

    for _, row in df.iterrows():
        phone = _normalize_phone(row.get("Phone"))
        message = str(row.get("WhatsApp_Message", "") or "").strip()

        if not phone or not message:
            failed += 1
            failed_numbers.append(str(row.get("Phone", "")))
            failed_reasons.append("Empty phone or message")
            continue

        if len(message) > MAX_LEN:
            message = message[:MAX_LEN]

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message},
        }

        try:
            resp = session.post(url, headers=headers, json=payload, timeout=timeout)
            if 200 <= resp.status_code < 300:
                success += 1
            else:
                failed += 1
                failed_numbers.append(phone)
                failed_reasons.append(_safe_error_text(resp))
        except requests.RequestException as e:
            failed += 1
            failed_numbers.append(phone)
            failed_reasons.append(str(e))

        # تهدئة بسيطة لتجنب rate limits (عدّلها لو بعتك كبير)
        time.sleep(0.15)

    summary = [
        "📨 WhatsApp Message Sending Summary:",
        f"✅ Success: {success}",
        f"❌ Failed: {failed}",
        f"📋 Total: {len(df)}",
    ]

    if failed_numbers:
        summary.append("\n📌 Failed Numbers (first 10):")
        for p in failed_numbers[:10]:
            summary.append(p)
    if failed_reasons:
        summary.append("\n🧯 Error samples (first 5):")
        for r in failed_reasons[:5]:
            summary.append(f"- {r}")

    return "\n".join(summary)


def verify_whatsapp_credentials(phone_number_id: str, access_token: str) -> Tuple[bool, str]:
    """
    Quick sanity check by calling business profile endpoint.
    """
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/whatsapp_business_profile"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if 200 <= resp.status_code < 300:
            return True, "✅ Verified and ready to send messages."
        return False, f"❌ Invalid credentials: {_safe_error_text(resp)}"
    except requests.RequestException as e:
        return False, f"❌ Error: {e}"
