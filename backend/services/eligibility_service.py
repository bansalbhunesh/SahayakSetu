"""Lightweight rule hints vs user profile — illustrative, not legal eligibility."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.services.retrieval_service import SearchResult


@dataclass(frozen=True)
class _Rule:
    pattern: str
    needs_woman: bool = False
    needs_business_intent: bool = False
    needs_farmer: bool = False
    reason_ok: str = "Profile matches common scheme focus (heuristic)."
    reason_fail: str = "Rule hint: profile may not match typical scheme focus — verify on the official portal."


_RULES: tuple[_Rule, ...] = (
    _Rule(
        r"stand[\s-]?up\s+india",
        needs_woman=True,
        needs_business_intent=True,
        reason_ok="Stand-Up India often targets women / SC / ST entrepreneurs — your profile aligns with the women + business angle (verify bank norms).",
        reason_fail="Stand-Up India is aimed at SC/ST/women entrepreneurs; add category + business intent or check the official scheme page.",
    ),
    _Rule(
        r"mudra|pm\s*mudra",
        needs_business_intent=True,
        reason_ok="MUDRA supports micro/small business credit — business intent in your profile fits the usual use case (verify with your bank).",
        reason_fail="MUDRA is for business/MSE credit; say you run or plan a small business for sharper matching.",
    ),
    _Rule(
        r"pm[\s-]?kisan|pradhan\s*mantri\s*kisan",
        needs_farmer=True,
        reason_ok="PM-Kisan targets landholding farmers as per land records — farmer-related profile fits the usual lens (confirm with agriculture department).",
        reason_fail="PM-Kisan is farmer/land-record linked; mention farmer status or landholding for clearer fit.",
    ),
    _Rule(
        r"ujjwala|pm\s*ujjwala",
        reason_ok="PMUY supports households without LPG — confirm BPL/state lists on the official portal.",
        reason_fail="Check official eligibility lists for PMUY in your state.",
    ),
)


def _text_profile(profile: dict) -> str:
    parts: list[str] = []
    for k in ("gender", "occupation", "category", "state", "bpl"):
        v = profile.get(k)
        if v is None:
            continue
        parts.append(str(v).lower())
    return " ".join(parts)


def _has_woman_signal(blob: str) -> bool:
    return bool(
        re.search(
            r"\b(woman|women|female|lady|ladies|girl|mahila|stree|nar[iı])\b",
            blob,
            re.I,
        )
    )


def _has_business_intent(blob: str) -> bool:
    return bool(
        re.search(
            r"\b(business|startup|enterprise|msme|self[\s-]?employ|loan|udhyog|vyapar|dukan)\b",
            blob,
            re.I,
        )
    )


def _has_farmer_signal(blob: str) -> bool:
    return bool(re.search(r"\b(farmer|kisan|agriculture|cultivat|crop|land)\b", blob, re.I))


def hints_for_schemes(
    profile: dict | None,
    results: list[SearchResult],
    *,
    query: str = "",
) -> list[dict]:
    """Return small verdict hints for top retrieved schemes (best-effort, not legal advice)."""
    p = profile or {}
    blob = _text_profile(p)
    combined = f"{blob} {(query or '').lower()}".strip()
    out: list[dict] = []
    for r in results[:5]:
        name = (r.scheme_name or "").strip()
        if not name:
            continue
        lower = name.lower()
        matched: _Rule | None = None
        for rule in _RULES:
            if re.search(rule.pattern, lower, re.I):
                matched = rule
                break
        if not matched:
            out.append({"scheme": name, "verdict": "unknown", "reason": "No quick rule card for this scheme."})
            continue
        ok = True
        if matched.needs_woman and not _has_woman_signal(combined):
            ok = False
        if matched.needs_business_intent and not _has_business_intent(combined):
            ok = False
        if matched.needs_farmer and not _has_farmer_signal(combined):
            ok = False
        verdict = "likely_eligible" if ok else "likely_ineligible"
        reason = matched.reason_ok if ok else (matched.reason_fail or matched.reason_ok)
        out.append({"scheme": name, "verdict": verdict, "reason": reason})
    return out
