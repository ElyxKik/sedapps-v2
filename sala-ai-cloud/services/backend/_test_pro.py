import json, time, httpx, sys
from app.config import settings
from app.llm_site_generator import _SINGLE_SHOT_PROMPT

t = time.time()
try:
    r = httpx.post(
        f"{settings.deepseek_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-v4-pro",
            "messages": [
                {"role": "system", "content": _SINGLE_SHOT_PROMPT},
                {"role": "user", "content": json.dumps({"brief": {"business_name": "XEEZY STORE", "sector": "Personnalise"}})},
            ],
            "temperature": 0.5,
            "response_format": {"type": "json_object"},
            "max_tokens": 8000,
        },
        timeout=180,
    )
    dt = round(time.time() - t, 1)
    print("status", r.status_code, "in", dt, "s", flush=True)
    data = r.json()
    msg = data["choices"][0]["message"]
    c = msg.get("content") or ""
    rc = msg.get("reasoning_content") or ""
    print("content_len", len(c), "reasoning_len", len(rc), "usage", data.get("usage"), flush=True)
    print("CONTENT_HEAD:", c[:500], flush=True)
    print("REASONING_HEAD:", rc[:500], flush=True)
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:300], "after", round(time.time()-t,1), "s", flush=True)
