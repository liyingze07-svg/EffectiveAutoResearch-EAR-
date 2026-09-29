"""HTTP service wrapper for the rebuttal-quality verifier.

Lets teammates use our DeepSeek V4 Pro verifier WITHOUT ever seeing the DeepSeek
API key: the key stays server-side in this process; callers hit POST /verify with
their own lightweight service token (issued/revoked independently of the DeepSeek
key).

Run:
    cd rebuttal_verifier
    # server-side secrets (or put them in .env, which this reuses):
    #   DEEPSEEK_API_KEY=...   (required)
    #   SERVICE_TOKENS=alice-tok,bob-tok   (optional; if set, callers must present one)
    pip install fastapi uvicorn
    uvicorn serve:app --host 0.0.0.0 --port 8000

Call:
    curl -s http://HOST:8000/verify \
      -H "Authorization: Bearer alice-tok" -H "Content-Type: application/json" \
      -d '{"venue":"emnlp","initial_overall":3,"confidence":4,"soundness":4,
           "review":"## summary_of_weaknesses ...","rebuttal":"We added ..."}'
    # -> {"reaction":"raise","quality":"high","reasoning":"..."}
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

from verify_rebuttal import verify_one, _client_and_model, _load_env, build_messages_auto
import prompt_template
import prompt_template_emnlp
import prompt_template_emnlp_oa3

TEMPLATES = {
    "iclr": prompt_template.build_messages,
    "emnlp": build_messages_auto,                        # auto-route by OA (3 -> diagnoser)
    "emnlp-v2": prompt_template_emnlp.build_messages,    # force general EMNLP
    "emnlp-oa3": prompt_template_emnlp_oa3.build_messages,  # force OA=3 diagnoser
}


def _route_name(venue, case):
    if venue == "emnlp":
        return "emnlp-oa3" if case.get("initial_overall") == 3 else "emnlp-v2"
    return venue

_env = _load_env()
_TOKENS = {t.strip() for t in _env.get("SERVICE_TOKENS", "").split(",") if t.strip()}
_client, _model = None, None   # lazily initialised so the app can boot without a key set yet

app = FastAPI(title="Rebuttal-Quality Verifier", version="1.0")


class VerifyRequest(BaseModel):
    review: str
    rebuttal: str = ""
    venue: str = "iclr"                     # "iclr" or "emnlp"
    title: Optional[str] = None
    reviewer_profile: Optional[str] = None  # free-text persona (overrides fields below)
    initial_rating: Optional[float] = None  # ICLR persona (x/10)
    initial_overall: Optional[float] = None  # EMNLP/ARR persona (x/5) -- REQUIRED for emnlp
    confidence: Optional[float] = None
    soundness: Optional[float] = None
    presentation: Optional[float] = None
    contribution: Optional[float] = None


def _auth(authorization: Optional[str]):
    if not _TOKENS:
        return  # open mode (no tokens configured)
    tok = (authorization or "").removeprefix("Bearer ").strip()
    if tok not in _TOKENS:
        raise HTTPException(status_code=401, detail="invalid or missing service token")


@app.get("/health")
def health():
    return {"status": "ok", "model": _env.get("DEEPSEEK_MODEL", "deepseek-v4-pro"),
            "venues": list(TEMPLATES), "auth": bool(_TOKENS)}


@app.post("/verify")
def verify(req: VerifyRequest, authorization: Optional[str] = Header(default=None)):
    _auth(authorization)
    if req.venue not in TEMPLATES:
        raise HTTPException(status_code=400, detail=f"venue must be one of {list(TEMPLATES)}")
    if req.venue.startswith("emnlp") and req.initial_overall is None and not req.reviewer_profile:
        raise HTTPException(status_code=400,
                            detail="emnlp requires initial_overall (the pre-rebuttal 1-5 score) "
                                   "or a reviewer_profile; without it the model is at chance")
    global _client, _model
    if _client is None:
        _client, _model = _client_and_model()   # raises if DEEPSEEK_API_KEY missing
    case = req.model_dump(exclude_none=True)
    try:
        out = verify_one(case, client=_client, model=_model,
                         build_messages=TEMPLATES[req.venue])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream model error: {e}")
    out["template_used"] = _route_name(req.venue, case)   # transparency: which prompt fired
    return out
