from __future__ import annotations

from math import pow


GOAL_TYPES = ["House", "Retirement", "Emergency"]

GOAL_TYPE_DEFAULTS = {
    "House": {"target_amount": 2500000, "time_years": 8, "current_savings": 200000},
    "Retirement": {"target_amount": 8000000, "time_years": 20, "current_savings": 500000},
    "Emergency": {"target_amount": 600000, "time_years": 3, "current_savings": 50000},
}

RISK_QUESTIONS = [
    {
        "id": "market_drop",
        "prompt": "If your investment falls 10% in one month, what would you most likely do?",
        "options": [
            {"label": "Move most of it to safer options", "score": 1},
            {"label": "Wait and watch calmly", "score": 2},
            {"label": "Invest more because prices are lower", "score": 3},
        ],
    },
    {
        "id": "timeline",
        "prompt": "How long can you stay invested without needing this money?",
        "options": [
            {"label": "Less than 3 years", "score": 1},
            {"label": "3 to 7 years", "score": 2},
            {"label": "More than 7 years", "score": 3},
        ],
    },
    {
        "id": "stability",
        "prompt": "Which statement sounds closest to you?",
        "options": [
            {"label": "I prefer stability over higher returns", "score": 1},
            {"label": "I want a mix of growth and stability", "score": 2},
            {"label": "I can handle volatility for higher growth", "score": 3},
        ],
    },
]

PORTFOLIOS = {
    "conservative": {
        "key": "conservative",
        "label": "Conservative Plan",
        "risk_label": "Low to moderate",
        "expected_return": 0.08,
        "return_range": "7% to 8.5% p.a.",
        "summary": "A steadier path for users who want lower volatility and clearer short-term predictability.",
        "explanation": (
            "This mix leans on debt-oriented funds and keeps a smaller allocation to growth assets. "
            "It is meant for users who value stability and may feel uneasy with sharp market swings."
        ),
        "allocation": [
            {"label": "Liquid Funds", "weight": 25},
            {"label": "Short-Term Debt Funds", "weight": 45},
            {"label": "Index Funds", "weight": 20},
            {"label": "Flexi-Cap Funds", "weight": 10},
        ],
    },
    "moderate": {
        "key": "moderate",
        "label": "Moderate Plan",
        "risk_label": "Balanced",
        "expected_return": 0.11,
        "return_range": "10% to 12% p.a.",
        "summary": "A balanced allocation for users who want growth without taking on too much volatility.",
        "explanation": (
            "This plan blends equity and debt buckets so the portfolio can grow over time while still "
            "keeping some cushion during uncertain periods."
        ),
        "allocation": [
            {"label": "Liquid Funds", "weight": 10},
            {"label": "Short-Term Debt Funds", "weight": 30},
            {"label": "Index Funds", "weight": 35},
            {"label": "Flexi-Cap Funds", "weight": 25},
        ],
    },
    "aggressive": {
        "key": "aggressive",
        "label": "Aggressive Plan",
        "risk_label": "Growth focused",
        "expected_return": 0.13,
        "return_range": "12% to 14% p.a.",
        "summary": "A growth-oriented mix for users with longer timelines and stronger tolerance for market swings.",
        "explanation": (
            "This recommendation keeps more of the portfolio in equity-oriented buckets to pursue higher "
            "long-term growth, while still maintaining a small stability layer."
        ),
        "allocation": [
            {"label": "Liquid Funds", "weight": 5},
            {"label": "Short-Term Debt Funds", "weight": 15},
            {"label": "Index Funds", "weight": 40},
            {"label": "Flexi-Cap Funds", "weight": 40},
        ],
    },
}

NOTIFICATION_TEMPLATES = {
    "welcome": "Welcome to Nivesh X.",
    "otp_sent": "OTP sent.",
    "login_success": "Login verified.",
    "profile_saved": "Profile saved.",
    "risk_saved": "Risk profile saved.",
    "risk_defaulted": "Risk profile defaulted to Conservative.",
    "goal_created": "Goal created.",
    "goal_warning": "One goal may need a high monthly SIP.",
    "portfolio_accepted": "Portfolio recommendation accepted.",
    "kyc_pending": "KYC is pending.",
    "kyc_complete": "KYC completed.",
    "kyc_blocked": "KYC required before SIP setup.",
    "sip_success": "SIP setup successful.",
    "sip_failure": "SIP setup failed.",
    "goal_deleted": "Goal deleted.",
}

KYC_PENDING_COPY = "KYC is still pending. Complete it before starting any investment."
MARKET_DROP_COPY = (
    "If markets become volatile, this prototype keeps the message calm: stay focused on goals, "
    "review your timeline, and avoid panic decisions."
)


def classify_risk_profile(score: int) -> str:
    if score <= 4:
        return "Conservative"
    if score <= 7:
        return "Moderate"
    return "Aggressive"


def get_portfolio_for_risk(risk_profile: str) -> dict:
    mapping = {
        "Conservative": PORTFOLIOS["conservative"],
        "Moderate": PORTFOLIOS["moderate"],
        "Aggressive": PORTFOLIOS["aggressive"],
    }
    return mapping.get(risk_profile, PORTFOLIOS["conservative"])


def calculate_required_sip(
    target_amount: float,
    time_years: int,
    risk_profile: str,
    current_savings: float = 0.0,
) -> float:
    portfolio = get_portfolio_for_risk(risk_profile)
    annual_rate = portfolio["expected_return"]
    months = max(int(time_years * 12), 1)
    monthly_rate = annual_rate / 12
    remaining_target = max(target_amount - current_savings, 0.0)

    if monthly_rate == 0:
        return remaining_target / months

    growth_factor = (pow(1 + monthly_rate, months) - 1) / monthly_rate
    if growth_factor == 0:
        return remaining_target / months
    return remaining_target / growth_factor


def calculate_future_value(
    monthly_investment: float,
    annual_return_rate: float,
    months: int,
    current_savings: float = 0.0,
) -> float:
    total_months = max(months, 0)
    monthly_rate = annual_return_rate / 12
    if total_months == 0:
        return current_savings
    if monthly_rate == 0:
        return current_savings + (monthly_investment * total_months)
    sip_value = monthly_investment * ((pow(1 + monthly_rate, total_months) - 1) / monthly_rate)
    savings_value = current_savings * pow(1 + monthly_rate, total_months)
    return sip_value + savings_value


def is_goal_unrealistic(required_sip: float, monthly_income: float) -> bool:
    if monthly_income <= 0:
        return True
    return required_sip > monthly_income * 0.35


def format_currency(value: float) -> str:
    return f"Rs. {value:,.0f}"
