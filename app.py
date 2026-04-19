from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from niveshx_config import (
    GOAL_TYPES,
    GOAL_TYPE_DEFAULTS,
    KYC_PENDING_COPY,
    MARKET_DROP_COPY,
    NOTIFICATION_TEMPLATES,
    PORTFOLIOS,
    RISK_QUESTIONS,
    calculate_future_value,
    calculate_required_sip,
    classify_risk_profile,
    format_currency,
    get_portfolio_for_risk,
    is_goal_unrealistic,
)


STEPS = [
    "welcome",
    "profile",
    "risk",
    "goal",
    "portfolio",
    "execution",
    "dashboard",
]

STEP_LABELS = {
    "welcome": "Login",
    "profile": "Profile",
    "risk": "Risk Profiling",
    "goal": "Goal Creation",
    "portfolio": "Recommendation",
    "execution": "Execution",
    "dashboard": "Dashboard",
}


def init_state() -> None:
    defaults: dict[str, Any] = {
        "current_step": "welcome",
        "otp_sent": False,
        "logged_in": False,
        "otp_value": "246810",
        "user_profile": {
            "name": "",
            "phone": "",
            "age": 30,
            "city": "Bengaluru",
            "occupation": "Salaried",
            "annual_income": 900000,
            "monthly_income": 75000,
        },
        "risk_answers": {},
        "risk_profile": None,
        "goals": [],
        "selected_goal_id": None,
        "latest_goal_id": None,
        "kyc_status": "Not Started",
        "sip_setup": {
            "status": "Not Started",
            "amount": 0.0,
            "debit_day": 5,
            "bank_name": "",
            "goal_id": None,
            "auto_debit": False,
            "last_status": None,
        },
        "notifications": [
            notification_item("welcome", "Your guided investing workspace is ready."),
            notification_item("kyc_pending", KYC_PENDING_COPY),
        ],
        "delete_goal_id": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def notification_item(kind: str, message: str) -> dict[str, str]:
    return {
        "kind": kind,
        "message": message,
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }


def push_notification(kind: str, custom_message: str | None = None) -> None:
    message = custom_message or NOTIFICATION_TEMPLATES.get(kind, kind.replace("_", " ").title())
    st.session_state.notifications.insert(0, notification_item(kind, message))
    st.session_state.notifications = st.session_state.notifications[:12]


def go_to(step: str) -> None:
    st.session_state.current_step = step


def progress_index(step: str) -> int:
    return STEPS.index(step) + 1


def current_goal() -> dict[str, Any] | None:
    selected_goal_id = st.session_state.selected_goal_id or st.session_state.latest_goal_id
    for goal in st.session_state.goals:
        if goal["id"] == selected_goal_id:
            return goal
    return st.session_state.goals[-1] if st.session_state.goals else None


def active_goal_count() -> int:
    return len([goal for goal in st.session_state.goals if not goal.get("deleted")])


def update_goal(goal_id: str, updates: dict[str, Any]) -> None:
    for index, goal in enumerate(st.session_state.goals):
        if goal["id"] == goal_id:
            st.session_state.goals[index] = {**goal, **updates}
            return


def render_shell() -> None:
    current_step = st.session_state.current_step
    st.set_page_config(page_title="Nivesh X", page_icon="NX", layout="wide")
    st.markdown(
        """
        <style>
          .stApp {
            background:
              radial-gradient(circle at top right, rgba(5, 150, 105, 0.20), transparent 28%),
              radial-gradient(circle at top left, rgba(59, 130, 246, 0.15), transparent 24%),
              linear-gradient(180deg, #f7fbf9 0%, #eef6f3 100%);
            color: #0f172a;
          }
          .hero-card, .surface-card, .goal-card, .feed-card {
            background: rgba(255,255,255,0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
            padding: 1.25rem;
          }
          .hero-card {
            padding: 1.5rem;
            background: linear-gradient(135deg, #0f766e 0%, #1d4ed8 100%);
            color: white;
          }
          .eyebrow {
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.14em;
            opacity: 0.8;
          }
          .metric-number {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
          }
          .allocation-chip {
            display: inline-block;
            margin: 0.25rem 0.4rem 0 0;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #e8f5ef;
            color: #166534;
            font-size: 0.85rem;
            font-weight: 600;
          }
          .step-pill {
            display: inline-block;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: #dbeafe;
            color: #1d4ed8;
            font-size: 0.8rem;
            font-weight: 700;
          }
          .status-good { color: #166534; font-weight: 700; }
          .status-warn { color: #b45309; font-weight: 700; }
          .status-bad { color: #b91c1c; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    completed_steps = max(progress_index(current_step) - 1, 0)
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="eyebrow">Nivesh X V1</div>
          <h1 style="margin:0.35rem 0 0.45rem 0;">Goal-based investing for everyday Indian families</h1>
          <p style="margin:0; max-width: 860px;">
            Build toward a house, retirement, or an emergency fund with simple guidance,
            clear SIP math, and a calm dashboard that avoids financial jargon.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step_names = " -> ".join(
        [
            f"[{STEP_LABELS[step]}]" if step == current_step else STEP_LABELS[step]
            for step in STEPS
        ]
    )
    st.caption(f"Journey: {step_names}")
    st.progress(completed_steps / (len(STEPS) - 1) if len(STEPS) > 1 else 0.0)


def render_welcome() -> None:
    st.markdown('<div class="step-pill">Step 1 of 7</div>', unsafe_allow_html=True)
    st.subheader("Login with mobile OTP")
    st.write("This prototype simulates OTP verification so we can focus on the product journey.")

    with st.form("login_form"):
        phone = st.text_input("Mobile number", value=st.session_state.user_profile["phone"], max_chars=10)
        submitted = st.form_submit_button("Send OTP", use_container_width=True)

    if submitted:
        cleaned_phone = "".join(character for character in phone if character.isdigit())
        if len(cleaned_phone) != 10:
            st.error("Enter a valid 10-digit mobile number.")
        else:
            st.session_state.user_profile["phone"] = cleaned_phone
            st.session_state.otp_sent = True
            push_notification("otp_sent", f"OTP sent to +91 {cleaned_phone}. Use 246810 for this prototype.")
            st.success("OTP sent. Enter 246810 to continue.")

    if st.session_state.otp_sent:
        with st.form("verify_otp"):
            otp = st.text_input("Enter OTP", max_chars=6)
            verified = st.form_submit_button("Verify and continue", use_container_width=True)
        if verified:
            if otp == st.session_state.otp_value:
                st.session_state.logged_in = True
                push_notification("login_success", "You are signed in and ready to set up your investing plan.")
                go_to("profile")
                st.rerun()
            else:
                st.error("That OTP is incorrect for the prototype.")


def render_profile() -> None:
    st.markdown('<div class="step-pill">Step 2 of 7</div>', unsafe_allow_html=True)
    st.subheader("Tell us a little about yourself")
    profile = st.session_state.user_profile

    with st.form("profile_form"):
        name = st.text_input("Full name", value=profile["name"], placeholder="Aarav Sharma")
        age = st.slider("Age", min_value=23, max_value=45, value=int(profile["age"]))
        city = st.text_input("City", value=profile["city"])
        occupation = st.selectbox(
            "Profile",
            options=["Salaried", "Small Business", "Freelancer", "Other"],
            index=["Salaried", "Small Business", "Freelancer", "Other"].index(profile["occupation"]),
        )
        annual_income = st.number_input(
            "Annual income (Rs.)",
            min_value=300000,
            max_value=2000000,
            step=50000,
            value=int(profile["annual_income"]),
        )
        monthly_income = st.number_input(
            "Monthly take-home income (Rs.)",
            min_value=20000,
            max_value=250000,
            step=5000,
            value=int(profile["monthly_income"]),
        )
        saved = st.form_submit_button("Save profile and continue", use_container_width=True)

    if saved:
        if not name.strip():
            st.error("Please enter your name.")
            return
        st.session_state.user_profile = {
            **profile,
            "name": name.strip(),
            "age": age,
            "city": city.strip() or profile["city"],
            "occupation": occupation,
            "annual_income": annual_income,
            "monthly_income": monthly_income,
        }
        push_notification("profile_saved", "Your investor profile has been saved.")
        go_to("risk")
        st.rerun()

    if st.button("Back to login"):
        go_to("welcome")
        st.rerun()


def render_risk() -> None:
    st.markdown('<div class="step-pill">Step 3 of 7</div>', unsafe_allow_html=True)
    st.subheader("A few simple questions")
    st.write("Your answers help us recommend a portfolio that matches your comfort with risk.")

    with st.form("risk_form"):
        answers: dict[str, int] = {}
        for question in RISK_QUESTIONS:
            options = [option["label"] for option in question["options"]]
            chosen = st.radio(question["prompt"], options=options, index=1, key=f"risk_{question['id']}")
            selected = next(option for option in question["options"] if option["label"] == chosen)
            answers[question["id"]] = selected["score"]

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Save risk profile", use_container_width=True)
        with col2:
            skipped = st.form_submit_button("Skip for now", use_container_width=True)

    if submitted:
        risk_profile = classify_risk_profile(sum(answers.values()))
        st.session_state.risk_answers = answers
        st.session_state.risk_profile = risk_profile
        push_notification("risk_saved", f"Risk profile set to {risk_profile}.")
        go_to("goal")
        st.rerun()

    if skipped:
        st.session_state.risk_answers = {}
        st.session_state.risk_profile = "Conservative"
        push_notification("risk_defaulted", "Risk profiling skipped. Default profile set to Conservative.")
        go_to("goal")
        st.rerun()

    if st.button("Back to profile"):
        go_to("profile")
        st.rerun()


def render_goal_creation() -> None:
    st.markdown('<div class="step-pill">Step 4 of 7</div>', unsafe_allow_html=True)
    st.subheader("Create your first goal")
    st.write("Start with one clear goal. You can add more later from the dashboard.")

    selected_goal_type = st.selectbox("Goal type", options=GOAL_TYPES)
    defaults = GOAL_TYPE_DEFAULTS[selected_goal_type]
    profile = st.session_state.user_profile
    risk_profile = st.session_state.risk_profile or "Conservative"

    with st.form("goal_form"):
        target_amount = st.number_input(
            "Target amount (Rs.)",
            min_value=100000,
            step=50000,
            value=defaults["target_amount"],
        )
        time_years = st.slider(
            "Time horizon (years)",
            min_value=1,
            max_value=30,
            value=defaults["time_years"],
        )
        current_savings = st.number_input(
            "Current savings toward this goal (Rs.)",
            min_value=0,
            step=25000,
            value=defaults["current_savings"],
        )
        submitted = st.form_submit_button("Calculate SIP and continue", use_container_width=True)

    monthly_income = float(profile["monthly_income"])
    monthly_sip = calculate_required_sip(target_amount, time_years, risk_profile, current_savings)
    unrealistic = is_goal_unrealistic(monthly_sip, monthly_income)

    preview_col1, preview_col2, preview_col3 = st.columns(3)
    preview_col1.metric("Recommended monthly SIP", format_currency(monthly_sip))
    preview_col2.metric("Risk profile", risk_profile)
    preview_col3.metric("Time horizon", f"{time_years} years")

    if unrealistic:
        st.warning(
            f"This goal may be ambitious for a monthly income of {format_currency(monthly_income)}. "
            "You may want to increase the timeline or lower the target amount."
        )

    if submitted:
        goal_id = f"goal-{len(st.session_state.goals) + 1}"
        goal = {
            "id": goal_id,
            "type": selected_goal_type,
            "target_amount": float(target_amount),
            "time_years": int(time_years),
            "current_savings": float(current_savings),
            "monthly_sip": float(monthly_sip),
            "risk_profile": risk_profile,
            "portfolio_key": get_portfolio_for_risk(risk_profile)["key"],
            "warning": unrealistic,
            "created_at": datetime.now().strftime("%d %b %Y"),
            "deleted": False,
            "progress_months": min(max(time_years * 12 // 6, 1), 12),
        }
        st.session_state.goals.append(goal)
        st.session_state.selected_goal_id = goal_id
        st.session_state.latest_goal_id = goal_id
        push_notification("goal_created", f"{selected_goal_type} goal created with a SIP of {format_currency(monthly_sip)}.")
        if unrealistic:
            push_notification("goal_warning", "One of your goals needs a high monthly SIP. Review it before investing.")
        go_to("portfolio")
        st.rerun()

    if st.button("Back to risk profile"):
        go_to("risk")
        st.rerun()


def render_portfolio_recommendation() -> None:
    st.markdown('<div class="step-pill">Step 5 of 7</div>', unsafe_allow_html=True)
    goal = current_goal()
    if not goal:
        st.info("Create a goal first.")
        if st.button("Go to goal creation"):
            go_to("goal")
            st.rerun()
        return

    portfolio = PORTFOLIOS[goal["portfolio_key"]]
    st.subheader(f"Recommended plan for your {goal['type'].lower()} goal")
    st.write(portfolio["summary"])

    top_col1, top_col2, top_col3 = st.columns(3)
    top_col1.metric("Goal target", format_currency(goal["target_amount"]))
    top_col2.metric("Monthly SIP", format_currency(goal["monthly_sip"]))
    top_col3.metric("Expected return range", portfolio["return_range"])

    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.markdown('<div class="surface-card">', unsafe_allow_html=True)
        st.markdown(f"### {portfolio['label']}")
        st.caption(f"Risk level: {portfolio['risk_label']}")
        for bucket in portfolio["allocation"]:
            st.markdown(
                f'<span class="allocation-chip">{bucket["label"]}: {bucket["weight"]}%</span>',
                unsafe_allow_html=True,
            )
        st.write("")
        st.write(portfolio["explanation"])
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="surface-card">', unsafe_allow_html=True)
        st.markdown("### Why this fits")
        st.write(f"- Goal type: {goal['type']}")
        st.write(f"- Risk profile: {goal['risk_profile']}")
        st.write(f"- Time horizon: {goal['time_years']} years")
        st.write(f"- Suggested SIP: {format_currency(goal['monthly_sip'])}")
        if goal["warning"]:
            st.warning("This plan is still possible, but the SIP is high for the income shared.")
        st.markdown("</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Accept recommendation", use_container_width=True):
            update_goal(goal["id"], {"accepted": True})
            push_notification("portfolio_accepted", f"You accepted the {portfolio['label']} portfolio for {goal['type']}.")
            go_to("execution")
            st.rerun()
    with col_b:
        if st.button("Back to goal details", use_container_width=True):
            go_to("goal")
            st.rerun()


def render_execution_setup() -> None:
    st.markdown('<div class="step-pill">Step 6 of 7</div>', unsafe_allow_html=True)
    goal = current_goal()
    if not goal:
        st.info("Create a goal first.")
        if st.button("Go to goal creation"):
            go_to("goal")
            st.rerun()
        return

    sip_setup = st.session_state.sip_setup
    kyc_col, sip_col = st.columns([1, 1.2])

    with kyc_col:
        st.markdown('<div class="surface-card">', unsafe_allow_html=True)
        st.markdown("### KYC status")
        status = st.session_state.kyc_status
        st.write(f"Current status: **{status}**")
        if status != "Completed":
            next_status = st.selectbox("Update KYC state", ["Not Started", "Pending", "Completed"], index=["Not Started", "Pending", "Completed"].index(status))
            if st.button("Save KYC status", use_container_width=True):
                st.session_state.kyc_status = next_status
                if next_status == "Pending":
                    push_notification("kyc_pending", KYC_PENDING_COPY)
                elif next_status == "Completed":
                    push_notification("kyc_complete", "KYC completed. You can now set up your SIP.")
                else:
                    push_notification("kyc_pending", "KYC is still needed before investments can start.")
                st.rerun()
        else:
            st.success("KYC is complete. SIP setup is unlocked.")
        st.markdown("</div>", unsafe_allow_html=True)

    with sip_col:
        st.markdown('<div class="surface-card">', unsafe_allow_html=True)
        st.markdown("### SIP setup")
        st.write(f"Recommended amount: **{format_currency(goal['monthly_sip'])} / month**")

        with st.form("sip_setup_form"):
            amount = st.number_input(
                "Monthly SIP amount (Rs.)",
                min_value=500,
                step=500,
                value=int(goal["monthly_sip"]),
            )
            debit_day = st.slider("Auto-debit day", min_value=1, max_value=28, value=max(int(sip_setup["debit_day"]), 1))
            bank_name = st.text_input("Bank nickname", value=sip_setup["bank_name"], placeholder="Salary Account")
            outcome = st.selectbox("Prototype simulation", ["Success", "Failure"], index=0)
            submitted = st.form_submit_button("Set up SIP", use_container_width=True)

        if submitted:
            if st.session_state.kyc_status != "Completed":
                st.error("Complete KYC before setting up the SIP.")
                push_notification("kyc_blocked", "SIP setup is blocked until KYC is completed.")
            elif not bank_name.strip():
                st.error("Please enter a bank nickname.")
            else:
                status = "Active" if outcome == "Success" else "Failed"
                st.session_state.sip_setup = {
                    "status": status,
                    "amount": float(amount),
                    "debit_day": int(debit_day),
                    "bank_name": bank_name.strip(),
                    "goal_id": goal["id"],
                    "auto_debit": True,
                    "last_status": status,
                }
                update_goal(goal["id"], {"sip_amount": float(amount), "sip_status": status})
                if status == "Active":
                    push_notification("sip_success", f"SIP created for {format_currency(amount)} on day {debit_day}.")
                    go_to("dashboard")
                    st.rerun()
                else:
                    push_notification("sip_failure", "SIP setup failed in the prototype. Review details and retry.")
                    st.warning("The SIP simulation failed. You can retry below.")

        if sip_setup["status"] == "Failed" and sip_setup["goal_id"] == goal["id"]:
            if st.button("Retry failed SIP", use_container_width=True):
                st.session_state.sip_setup["status"] = "Active"
                st.session_state.sip_setup["last_status"] = "Active"
                update_goal(goal["id"], {"sip_status": "Active", "sip_amount": st.session_state.sip_setup["amount"]})
                push_notification("sip_success", "Retry successful. Your SIP is now active.")
                go_to("dashboard")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    footer_col1, footer_col2 = st.columns(2)
    with footer_col1:
        if st.button("Back to recommendation", use_container_width=True):
            go_to("portfolio")
            st.rerun()
    with footer_col2:
        if st.button("Go to dashboard", use_container_width=True):
            go_to("dashboard")
            st.rerun()


def render_dashboard() -> None:
    st.markdown('<div class="step-pill">Step 7 of 7</div>', unsafe_allow_html=True)
    st.subheader("Your dashboard")

    goals = [goal for goal in st.session_state.goals if not goal.get("deleted")]
    monthly_total = sum(goal.get("sip_amount", goal["monthly_sip"]) for goal in goals)
    active_sip_count = sum(1 for goal in goals if goal.get("sip_status") == "Active")
    st.info(MARKET_DROP_COPY)

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Monthly SIP total", format_currency(monthly_total))
    metric2.metric("Active goals", str(len(goals)))
    metric3.metric("KYC status", st.session_state.kyc_status)
    metric4.metric("Active SIPs", str(active_sip_count))

    left_col, right_col = st.columns([1.5, 1])
    with left_col:
        st.markdown("### Goal progress")
        if not goals:
            st.info("No goals yet. Create one to begin.")
        for goal in goals:
            portfolio = PORTFOLIOS[goal["portfolio_key"]]
            current_value = calculate_future_value(
                monthly_investment=float(goal.get("sip_amount", goal["monthly_sip"])),
                annual_return_rate=portfolio["expected_return"],
                months=goal["progress_months"],
                current_savings=float(goal["current_savings"]),
            )
            progress = min(current_value / goal["target_amount"], 1.0) if goal["target_amount"] else 0.0
            status_text = goal.get("sip_status", "Pending")
            st.markdown('<div class="goal-card">', unsafe_allow_html=True)
            st.markdown(f"#### {goal['type']} goal")
            st.caption(f"Created on {goal['created_at']} | Portfolio: {portfolio['label']}")
            st.progress(progress)
            info_col1, info_col2, info_col3 = st.columns(3)
            info_col1.metric("Current value", format_currency(current_value))
            info_col2.metric("Target", format_currency(goal["target_amount"]))
            info_col3.metric("Monthly SIP", format_currency(goal.get("sip_amount", goal["monthly_sip"])))
            st.write(f"Progress: **{progress * 100:.1f}%** | SIP status: **{status_text}**")
            if goal["warning"]:
                st.warning("This goal needs a relatively high SIP. Consider extending the timeline if needed.")
            st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("### Recent updates")
        for item in st.session_state.notifications[:6]:
            st.markdown(
                f"""
                <div class="feed-card" style="margin-bottom: 0.8rem;">
                  <div class="eyebrow">{item['kind'].replace('_', ' ')}</div>
                  <div style="font-weight: 600; margin: 0.25rem 0;">{item['message']}</div>
                  <div style="font-size: 0.8rem; color: #475569;">{item['timestamp']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Manage goals")
    goal_options = {f"{goal['type']} ({goal['id']})": goal["id"] for goal in goals}
    if goal_options:
        chosen_label = st.selectbox("Select a goal", list(goal_options.keys()))
        chosen_id = goal_options[chosen_label]
        st.session_state.selected_goal_id = chosen_id
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Create another goal", use_container_width=True):
                go_to("goal")
                st.rerun()
        with action_col2:
            if st.button("Delete selected goal", use_container_width=True):
                st.session_state.delete_goal_id = chosen_id

        if st.session_state.delete_goal_id:
            st.warning("Deleting a goal removes it from your dashboard. Please confirm.")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("Confirm delete", use_container_width=True):
                    update_goal(st.session_state.delete_goal_id, {"deleted": True})
                    push_notification("goal_deleted", "One goal was deleted from the dashboard.")
                    st.session_state.delete_goal_id = None
                    st.rerun()
            with confirm_col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.delete_goal_id = None
                    st.rerun()
    else:
        if st.button("Create your first goal", use_container_width=True):
            go_to("goal")
            st.rerun()

    if st.session_state.sip_setup["status"] == "Failed":
        st.error("A SIP attempt is marked as failed.")
        if st.button("Retry failed SIP from dashboard", use_container_width=False):
            st.session_state.sip_setup["status"] = "Active"
            goal_id = st.session_state.sip_setup["goal_id"]
            if goal_id:
                update_goal(goal_id, {"sip_status": "Active"})
            push_notification("sip_success", "Retry successful. Your SIP is now active.")
            st.rerun()


def main() -> None:
    init_state()
    render_shell()

    current_step = st.session_state.current_step
    if current_step == "welcome":
        render_welcome()
    elif current_step == "profile":
        render_profile()
    elif current_step == "risk":
        render_risk()
    elif current_step == "goal":
        render_goal_creation()
    elif current_step == "portfolio":
        render_portfolio_recommendation()
    elif current_step == "execution":
        render_execution_setup()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
