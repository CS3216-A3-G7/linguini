"""Linguini unit-economics model.

Run from any directory with: python3 marketing/business-model/model/cost_model.py
Standard library only. Writes marketing/business-model/model/unit-economics.json and prints
the tables used in marketing/business-model/README.md.

Every price below was checked on 24 September 2026; the source is next to each
constant. Token counts are estimates derived from the backend's prompts, response
schemas and output caps (see "Tokens per call"). Replace them with Langfuse usage once every
AI feature is instrumented.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

OUT = Path(__file__).resolve().parent / "unit-economics.json"

# --- Provider prices, USD per 1M tokens ------------------------------------------
# https://ai.google.dev/gemini-api/docs/pricing (page updated 23 Sep 2026)
# https://developers.openai.com/api/docs/pricing
PRICES = {
    # gemini-3.7-flash is discounted until 31 Dec 2026, then doubles.
    "gemini-3.7-flash@promo": (0.75, 3.75),
    "gemini-3.7-flash@list": (1.50, 7.50),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),  # cheaper fallback for translation
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-5-nano": (0.05, 0.40),
}
MODERATION_PER_IMAGE = 0.0  # omni-moderation-latest is free
TRANSCRIBE_PER_MIN = 0.003  # gpt-4o-mini-transcribe
AZURE_PRON_PER_HOUR = 1.32 + 0.30  # Azure real-time STT + pronunciation add-on (conservative)
TTS_PER_M_CHARS = 12.00  # gpt-4o-mini-tts; browser speechSynthesis is free and used today

# --- Tokens per call ------------------------------------------------------------
# input = system prompt + JSON response schema + request payload (+ image).
# Prompt sizes: backend/app/ai/features/*/prompt.py (≈4 characters per token).
# Output caps: backend/app/ai/registry.py (1,500 default; 4,000 for learning tasks).
# Gemini 3 images cost 1,120 tokens at the default media resolution
# (https://ai.google.dev/gemini-api/docs/media-resolution).
# "expected" is a typical structured answer; "cap" bills the whole output cap,
# which also covers Gemini thinking tokens.


@dataclass(frozen=True)
class Call:
    feature: str
    model: str
    tokens_in: int
    out_expected: int
    out_cap: int
    calls_expected: float = 1
    calls_worst: float = 1


PIPELINES = ("current@promo", "current@list", "optimized")


def session_calls(pipeline: str) -> list[Call]:
    """Calls for one own-photo session.

    current@*: the models in backend/.env.example. optimized: the same features on
    cheaper models, medium image resolution (560 tokens) and translations reused from
    the vocabulary table for half of the words. Optimized quality is unproven until the
    photo evaluation set described in README.md passes.
    """
    if pipeline == "optimized":
        return [
            Call("Scene analysis (vision)", "gemini-3.1-flash-lite", 560 + 2800, 900, 1500),
            Call("Translation", "gemini-2.5-flash-lite", 1000, 500, 1500, 0.5, 1),
            Call("Learning tasks", "gpt-4.1-nano", 3000, 2000, 4000),
            Call("I-Spy clues", "gpt-4.1-nano", 1500, 600, 1500),
            Call("I-Spy guess feedback", "gpt-4.1-nano", 1100, 150, 1500, 3, 5),
        ]
    gemini = pipeline.split("@")[1]
    return [
        Call("Scene analysis (vision)", f"gemini-3.7-flash@{gemini}", 1120 + 2800, 900, 1500),
        Call("Translation", "gemini-3.5-flash-lite", 1000, 500, 1500),
        Call("Learning tasks", "gpt-4o-mini", 3000, 2000, 4000),
        Call("I-Spy clues", "gpt-4o-mini", 1500, 600, 1500),
        Call("I-Spy guess feedback", "gpt-4o-mini", 1100, 150, 1500, 3, 5),
    ]


JOURNAL_FEEDBACK = Call("Journal feedback (planned)", "gpt-4o-mini", 1500, 500, 1500)
RETRY_EXPECTED, RETRY_WORST = 1.10, 2.0  # MAX_RETRIES=1 can double a call


def call_cost(call: Call, worst: bool) -> float:
    price_in, price_out = PRICES[call.model]
    out = call.out_cap if worst else call.out_expected
    n = call.calls_worst if worst else call.calls_expected
    retry = RETRY_WORST if worst else RETRY_EXPECTED
    return n * retry * (call.tokens_in * price_in + out * price_out) / 1e6


def session_cost(pipeline: str, worst: bool) -> float:
    return MODERATION_PER_IMAGE + sum(call_cost(c, worst) for c in session_calls(pipeline))


# A curated (preloaded) scene is analysed once offline, so only guesses are live.
def curated_session_cost(pipeline: str, worst: bool) -> float:
    return call_cost(session_calls(pipeline)[-1], worst)


# Pronunciation: ~15 spoken attempts x 4 s = 1 minute of audio per session.
PRON_SECONDS = 60
PRON_OPTIONS = {
    "Browser speech recognition": 0.0,
    "gpt-4o-mini-transcribe + text compare": TRANSCRIBE_PER_MIN * PRON_SECONDS / 60 + 0.0003,
    "Azure pronunciation assessment": AZURE_PRON_PER_HOUR * PRON_SECONDS / 3600,
}

# --- Storage and bandwidth --------------------------------------------------------
# https://supabase.com/pricing and .../manage-your-usage/storage-size
STORAGE_PER_GB_MONTH = 0.0213  # after 100 GB on Pro
EGRESS_PER_GB = 0.09  # after 250 GB on Pro
MB_STORED_PER_PHOTO = 3.0  # phone JPEG + derivatives; uploads are capped at 10 MB
MB_SERVED_PER_SESSION = 1.5  # signed derivative views during a session

# --- Fixed monthly infrastructure -------------------------------------------------
# Vercel Hobby is non-commercial, so charging users requires Pro ($20/seat).
# Supabase Pro $25 includes Micro compute and 100k MAU. Render Starter $7 / Standard $25.
FIXED = {
    "launch": {"Vercel Pro (landing + app)": 20, "Supabase Pro": 25, "Render Starter API": 7},
    "growth": {"Vercel Pro (landing + app)": 20, "Supabase Pro": 25, "Render Standard API": 25},
}

# --- Payment fees -----------------------------------------------------------------
# Stripe as served to our Singapore account: 3.4% + $0.50, +0.5% international card,
# Billing 0.7%. App stores: 15% (Apple Small Business Program, Google Play subs).


def net_web(price: float) -> float:
    return price * (1 - 0.034 - 0.005 - 0.007) - 0.50


def net_store(price: float) -> float:
    return price * 0.85


# --- Usage profiles, sessions per month -------------------------------------------
@dataclass(frozen=True)
class Profile:
    name: str
    photo_sessions: int
    curated_sessions: int
    journals: int
    spoken_sessions: int


PROFILES = [
    Profile("Free · light", 2, 2, 2, 0),
    Profile("Free · casual", 8, 4, 8, 0),
    Profile("Free · at daily cap", 30, 10, 30, 0),
    Profile("Plus · typical", 30, 10, 30, 30),
    Profile("Plus · heavy (3/day)", 90, 20, 30, 90),
    Profile("Plus · fair-use ceiling (10/day)", 300, 30, 30, 300),
]


BROWSER, TRANSCRIBE, AZURE = PRON_OPTIONS


def profile_cost(p: Profile, pipeline: str, worst: bool, pron: str = TRANSCRIBE) -> float:
    ai = p.photo_sessions * session_cost(pipeline, worst)
    ai += p.curated_sessions * curated_session_cost(pipeline, worst)
    ai += p.journals * call_cost(JOURNAL_FEEDBACK, worst)
    ai += p.spoken_sessions * PRON_OPTIONS[pron]
    storage = p.photo_sessions * MB_STORED_PER_PHOTO / 1024 * STORAGE_PER_GB_MONTH
    egress = (p.photo_sessions + p.curated_sessions) * MB_SERVED_PER_SESSION / 1024 * EGRESS_PER_GB
    return ai + storage + egress


# Free users: 50% light, 35% casual, 15% at the daily cap (mean ≈ 8 photo sessions).
# Payers: 80% typical, 20% heavy. Free users speak through the browser at no cost.
FREE_MIX = ((0, 0.50), (1, 0.35), (2, 0.15))
PLUS_MIX = ((3, 0.80), (4, 0.20))


def free_user_cost(pipeline: str) -> float:
    return sum(w * profile_cost(PROFILES[i], pipeline, False, BROWSER) for i, w in FREE_MIX)


def plus_user_cost(pipeline: str) -> float:
    return sum(w * profile_cost(PROFILES[i], pipeline, False) for i, w in PLUS_MIX)


# --- Pricing options ---------------------------------------------------------------
OPTIONS = {
    "A · Current landing ($6.99 / $59.88)": (6.99, 59.88),
    "B · Recommended ($7.99 / $49.99)": (7.99, 49.99),
    "Founding Plus ($34.99/yr, capped cohort)": (None, 34.99),
}
RECOMMENDED = "B · Recommended ($7.99 / $49.99)"
ANNUAL_SHARE = 0.59  # RevenueCat SOSA 2026, education plan mix


def monthly_net_arpu(monthly: float | None, annual: float, channel=net_web) -> float:
    if monthly is None:
        return channel(annual) / 12
    return ANNUAL_SHARE * channel(annual) / 12 + (1 - ANNUAL_SHARE) * channel(monthly)


# --- Scale scenarios ----------------------------------------------------------------
# Conversion: RevenueCat education download-to-paid median 2.3%; Duolingo's paid
# penetration of MAU (12.7M / 140.6M ≈ 9%) is a mature-product ceiling.
SCENARIOS = [
    ("Beta", 300, 0.023, "launch"),
    ("Launch year", 5_000, 0.023, "launch"),
    ("Traction", 50_000, 0.04, "growth"),
]


def scenario(mau: int, conversion: float, fixed_key: str, pipeline: str, option: str = RECOMMENDED):
    monthly, annual = OPTIONS[option]
    payers = mau * conversion
    free_cost = (mau - payers) * free_user_cost(pipeline)
    plus_cost = payers * plus_user_cost(pipeline)
    fixed = sum(FIXED[fixed_key].values())  # Supabase Pro includes 100k MAU
    revenue = payers * monthly_net_arpu(monthly, annual)
    cost = free_cost + plus_cost + fixed
    return {
        "mau": mau,
        "conversion": conversion,
        "payers": round(payers),
        "net_revenue": round(revenue, 2),
        "free_ai_cost": round(free_cost, 2),
        "plus_ai_cost": round(plus_cost, 2),
        "fixed": fixed,
        "total_cost": round(cost, 2),
        "contribution": round(revenue - cost, 2),
    }


def breakeven_conversion(pipeline: str, option: str = RECOMMENDED) -> float:
    """Paid share of MAU at which net revenue covers all variable AI cost."""
    monthly, annual = OPTIONS[option]
    arpu, free, plus = monthly_net_arpu(monthly, annual), free_user_cost(pipeline), plus_user_cost(pipeline)
    # c * (arpu - plus) = (1 - c) * free  ->  c = free / (arpu - plus + free)
    return free / (arpu - plus + free)


def main():
    result = {"sessions": {}, "breakdown": {}, "profiles": {}, "options": {}, "scenarios": {}, "breakeven_conversion": {}}

    print("Per own-photo session (USD)")
    for pipeline in PIPELINES:
        for worst in (False, True):
            label = f"{pipeline}, {'worst case' if worst else 'expected'}"
            value = session_cost(pipeline, worst)
            result["sessions"][label] = round(value, 5)
            print(f"  {label:32} ${value:.4f}")
        result["breakdown"][pipeline] = {c.feature: round(call_cost(c, False), 5) for c in session_calls(pipeline)}
    for pipeline in ("current@list", "optimized"):
        print(f"  breakdown · {pipeline}")
        for feature, value in result["breakdown"][pipeline].items():
            print(f"    {feature:28} ${value:.4f}")
    result["curated_session"] = round(curated_session_cost("current@list", False), 5)
    result["journal_feedback"] = round(call_cost(JOURNAL_FEEDBACK, False), 5)
    result["pronunciation_per_session"] = {k: round(v, 5) for k, v in PRON_OPTIONS.items()}
    print(f"  curated scene session           ${result['curated_session']:.4f}")
    print(f"  journal feedback                ${result['journal_feedback']:.4f}")
    for name, value in PRON_OPTIONS.items():
        print(f"  pronunciation · {name:38} ${value:.4f}")

    print("\nMonthly variable cost per user")
    for p in PROFILES:
        spoken = p.spoken_sessions > 0
        row = {
            pipeline: round(profile_cost(p, pipeline, False, TRANSCRIBE if spoken else BROWSER), 3)
            for pipeline in PIPELINES
        }
        row["worst"] = round(profile_cost(p, "current@list", True, AZURE if spoken else BROWSER), 3)
        result["profiles"][p.name] = row
        print(f"  {p.name:34} " + "  ".join(f"{k} ${v:5.2f}" for k, v in row.items()))
    for pipeline in PIPELINES:
        result["profiles"].setdefault("_mix", {})[pipeline] = {
            "free": round(free_user_cost(pipeline), 3), "plus": round(plus_user_cost(pipeline), 3)
        }
    print(f"  blended free/plus: {result['profiles']['_mix']}")

    print("\nNet revenue per paying user per month (web / app store)")
    for name, (monthly, annual) in OPTIONS.items():
        web = monthly_net_arpu(monthly, annual, net_web)
        store = monthly_net_arpu(monthly, annual, net_store)
        result["options"][name] = {"monthly": monthly, "annual": annual, "net_web": round(web, 2), "net_store": round(store, 2)}
        print(f"  {name:44} web ${web:4.2f}   store ${store:4.2f}")

    print("\nScenarios (option B)")
    for pipeline in ("current@list", "optimized"):
        for label, mau, conv, fixed_key in SCENARIOS:
            row = scenario(mau, conv, fixed_key, pipeline)
            result["scenarios"].setdefault(pipeline, {})[label] = row
            print(f"  {pipeline:13} {label:12} {row}")

    print("\nBreak-even paid conversion (variable AI cost only)")
    for pipeline in PIPELINES:
        for option in OPTIONS:
            if OPTIONS[option][0] is None:
                continue
            c = breakeven_conversion(pipeline, option)
            result["breakeven_conversion"].setdefault(pipeline, {})[option] = round(c, 4)
            print(f"  {pipeline:13} {option:40} {c:.1%}")

    OUT.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {OUT.name}")


if __name__ == "__main__":
    main()
