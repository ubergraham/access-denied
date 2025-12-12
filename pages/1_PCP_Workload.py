"""PCP Workload Simulation.

Demonstrates the inbox burden a PCP faces when patients are enrolled
in multiple ACCESS programs, each sending weekly outcome updates.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random
import time

# Custom CSS for inbox styling
st.markdown("""
<style>
.inbox-message {
    background-color: #f8f9fa;
    border-left: 4px solid #3498db;
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 0 4px 4px 0;
    font-family: monospace;
    font-size: 13px;
}
.inbox-message.urgent {
    border-left-color: #e74c3c;
    background-color: #fdf2f2;
}
.inbox-message.unread {
    background-color: #ffffff;
    font-weight: bold;
}
.inbox-header {
    color: #2c3e50;
    font-size: 14px;
    margin-bottom: 2px;
}
.inbox-preview {
    color: #7f8c8d;
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.inbox-time {
    color: #95a5a6;
    font-size: 11px;
    float: right;
}
.message-counter {
    font-size: 48px;
    font-weight: bold;
    color: #e74c3c;
    text-align: center;
}
.vendor-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    margin-right: 5px;
}
.vendor-0 { background-color: #e74c3c; color: white; }
.vendor-1 { background-color: #3498db; color: white; }
.vendor-2 { background-color: #9b59b6; color: white; }
.vendor-3 { background-color: #2ecc71; color: white; }
.vendor-4 { background-color: #f39c12; color: white; }
.vendor-5 { background-color: #1abc9c; color: white; }
.vendor-6 { background-color: #e67e22; color: white; }
.vendor-7 { background-color: #34495e; color: white; }
.vendor-8 { background-color: #16a085; color: white; }
.vendor-9 { background-color: #c0392b; color: white; }
.vendor-10 { background-color: #8e44ad; color: white; }
.vendor-11 { background-color: #2980b9; color: white; }
.vendor-12 { background-color: #27ae60; color: white; }
.vendor-13 { background-color: #d35400; color: white; }
.vendor-14 { background-color: #7f8c8d; color: white; }
.vendor-15 { background-color: #2c3e50; color: white; }
.vendor-16 { background-color: #f1c40f; color: black; }
.vendor-17 { background-color: #95a5a6; color: black; }
.vendor-18 { background-color: #d35400; color: white; }
.vendor-19 { background-color: #1e3799; color: white; }
.vendor-20 { background-color: #b71540; color: white; }
.vendor-21 { background-color: #0a3d62; color: white; }
.vendor-22 { background-color: #6a89cc; color: white; }
.vendor-23 { background-color: #38ada9; color: white; }
.vendor-24 { background-color: #78e08f; color: black; }
.vendor-25 { background-color: #fa983a; color: black; }
.vendor-26 { background-color: #eb2f06; color: white; }
.vendor-27 { background-color: #3c6382; color: white; }
.vendor-28 { background-color: #82ccdd; color: black; }
.vendor-29 { background-color: #b8e994; color: black; }
</style>
""", unsafe_allow_html=True)

# 30 different ACCESS organizations with different formatting styles
ACCESS_ORGANIZATIONS = [
    # BP Control programs (10 vendors)
    {"id": 0, "name": "CardioTrack", "program": "BP Control", "metric": "Blood Pressure", "unit": "mmHg",
     "subject_format": "[{vendor}] Weekly {program} Update - {patient}",
     "urgent_phrase": "ACTION REQUIRED", "friendly": False},
    {"id": 1, "name": "HeartWise Health", "program": "Hypertension Mgmt", "metric": "BP Reading", "unit": "mmHg",
     "subject_format": "{patient} - {program} Weekly Summary",
     "urgent_phrase": "URGENT: Needs Review", "friendly": True},
    {"id": 2, "name": "PressurePoint", "program": "BP Monitoring", "metric": "Systolic/Diastolic", "unit": "",
     "subject_format": "Weekly Update: {patient} ({program})",
     "urgent_phrase": "** ACTION NEEDED **", "friendly": False},
    {"id": 3, "name": "CardioFirst", "program": "Blood Pressure", "metric": "BP", "unit": "mmHg",
     "subject_format": "{vendor} | {patient} | Weekly Report",
     "urgent_phrase": "ALERT - Review Required", "friendly": False},
    {"id": 4, "name": "BPCare Plus", "program": "HTN Management", "metric": "Blood Pressure", "unit": "",
     "subject_format": "Patient Update - {patient} - {program}",
     "urgent_phrase": "Action Requested", "friendly": True},
    {"id": 5, "name": "VitalSigns Pro", "program": "Cardiovascular", "metric": "BP Measurement", "unit": "mmHg",
     "subject_format": "[WEEKLY] {patient}: {program} Status",
     "urgent_phrase": "REQUIRES ATTENTION", "friendly": False},
    {"id": 6, "name": "HeartHealth360", "program": "BP Program", "metric": "Blood Pressure", "unit": "",
     "subject_format": "{program} Update for {patient}",
     "urgent_phrase": "Please Review", "friendly": True},
    {"id": 7, "name": "CircuWell", "program": "Hypertension", "metric": "BP Values", "unit": "mmHg",
     "subject_format": "CircuWell Weekly: {patient}",
     "urgent_phrase": "⚠️ Action Required", "friendly": False},
    {"id": 8, "name": "TensionFree", "program": "BP Control", "metric": "Pressure Reading", "unit": "",
     "subject_format": "{patient} Weekly BP Summary - TensionFree",
     "urgent_phrase": "Intervention Recommended", "friendly": True},
    {"id": 9, "name": "CardioMetrics", "program": "Blood Pressure Tracking", "metric": "BP", "unit": "mmHg",
     "subject_format": "RE: {patient} - Weekly {program}",
     "urgent_phrase": "CRITICAL - ACTION REQUIRED", "friendly": False},

    # MSK Pain programs (10 vendors)
    {"id": 10, "name": "PainAway", "program": "MSK Pain", "metric": "Pain Score", "unit": "/10",
     "subject_format": "[{vendor}] Weekly {program} Update - {patient}",
     "urgent_phrase": "ACTION REQUIRED", "friendly": False},
    {"id": 11, "name": "JointCare Health", "program": "Musculoskeletal", "metric": "Pain Level", "unit": "/10",
     "subject_format": "{patient}: Weekly Pain Assessment",
     "urgent_phrase": "High Pain - Please Review", "friendly": True},
    {"id": 12, "name": "MoveWell", "program": "Chronic Pain Mgmt", "metric": "Pain Rating", "unit": "",
     "subject_format": "MoveWell Update | {patient} | {program}",
     "urgent_phrase": "ELEVATED PAIN - ACTION NEEDED", "friendly": False},
    {"id": 13, "name": "SpineAlign", "program": "Back Pain", "metric": "Pain Score", "unit": "/10",
     "subject_format": "Weekly Report: {patient} - SpineAlign",
     "urgent_phrase": "Attention Required", "friendly": True},
    {"id": 14, "name": "FlexHealth", "program": "MSK Program", "metric": "Pain Assessment", "unit": "",
     "subject_format": "[FlexHealth] {patient} Weekly Status",
     "urgent_phrase": "⚠️ High Pain Alert", "friendly": False},
    {"id": 15, "name": "ArthriCare", "program": "Joint Pain", "metric": "Pain Index", "unit": "/10",
     "subject_format": "{program} Weekly - {patient}",
     "urgent_phrase": "Review Recommended", "friendly": True},
    {"id": 16, "name": "PainMetrix", "program": "Chronic Pain", "metric": "Pain Score", "unit": "",
     "subject_format": "PainMetrix | Weekly | {patient}",
     "urgent_phrase": "URGENT REVIEW NEEDED", "friendly": False},
    {"id": 17, "name": "MuscleCare Pro", "program": "MSK Management", "metric": "Pain Rating", "unit": "/10",
     "subject_format": "{patient} - Weekly Pain Update",
     "urgent_phrase": "Action Suggested", "friendly": True},
    {"id": 18, "name": "OrthoTrack", "program": "Orthopedic Pain", "metric": "Pain Level", "unit": "",
     "subject_format": "OrthoTrack Weekly: {patient} Status",
     "urgent_phrase": "** NEEDS ATTENTION **", "friendly": False},
    {"id": 19, "name": "ReliefWorks", "program": "Pain Control", "metric": "Pain Score", "unit": "/10",
     "subject_format": "Weekly Summary for {patient} - {program}",
     "urgent_phrase": "Please Review When Possible", "friendly": True},

    # Depression/Mental Health programs (10 vendors)
    {"id": 20, "name": "MindWell", "program": "Depression", "metric": "PHQ-9", "unit": "score",
     "subject_format": "[{vendor}] Weekly {program} Update - {patient}",
     "urgent_phrase": "ACTION REQUIRED", "friendly": False},
    {"id": 21, "name": "BrightPath Health", "program": "Behavioral Health", "metric": "PHQ-9 Score", "unit": "",
     "subject_format": "{patient} - Weekly Mental Health Check-in",
     "urgent_phrase": "Elevated Score - Please Review", "friendly": True},
    {"id": 22, "name": "MoodTrack", "program": "Depression Mgmt", "metric": "Depression Score", "unit": "",
     "subject_format": "MoodTrack | {patient} | Weekly Assessment",
     "urgent_phrase": "⚠️ CRITICAL - ACTION REQUIRED", "friendly": False},
    {"id": 23, "name": "ThriveWell", "program": "Mental Wellness", "metric": "PHQ-9", "unit": "pts",
     "subject_format": "Weekly Update: {patient} ({program})",
     "urgent_phrase": "Needs Your Attention", "friendly": True},
    {"id": 24, "name": "ClearMind", "program": "Depression Care", "metric": "PHQ Score", "unit": "",
     "subject_format": "[ClearMind] Weekly Report - {patient}",
     "urgent_phrase": "HIGH SCORE - URGENT", "friendly": False},
    {"id": 25, "name": "HopeHealth", "program": "Mood Disorder", "metric": "Depression Index", "unit": "",
     "subject_format": "{patient}: HopeHealth Weekly Summary",
     "urgent_phrase": "Review Suggested", "friendly": True},
    {"id": 26, "name": "PsychMetrics", "program": "BH Monitoring", "metric": "PHQ-9", "unit": "score",
     "subject_format": "PsychMetrics Weekly | {patient}",
     "urgent_phrase": "ALERT - IMMEDIATE REVIEW", "friendly": False},
    {"id": 27, "name": "SerenityNow", "program": "Depression Program", "metric": "Mood Score", "unit": "",
     "subject_format": "Weekly Check-in: {patient} - SerenityNow",
     "urgent_phrase": "Attention Recommended", "friendly": True},
    {"id": 28, "name": "MindMatters", "program": "MH Assessment", "metric": "PHQ-9", "unit": "",
     "subject_format": "RE: Weekly {program} - {patient}",
     "urgent_phrase": "** ACTION NEEDED **", "friendly": False},
    {"id": 29, "name": "WellBeing360", "program": "Behavioral Wellness", "metric": "Depression Score", "unit": "pts",
     "subject_format": "{vendor} Update for {patient}",
     "urgent_phrase": "Please Review at Your Convenience", "friendly": True},
]

st.title("PCP Inbox: The ACCESS Burden")

st.markdown("""
This simulation shows what a **Primary Care Physician's inbox** looks like when their
patients are enrolled in ACCESS programs. Each program sends **weekly updates** about
patient outcomes that the PCP must review.

> **The hidden cost of ACCESS**: Every enrolled patient generates 3x weekly messages
> that PCPs are expected to review, acknowledge, and potentially act on.
""")

st.divider()


def generate_patient_names(n: int, seed: int = 42) -> list[dict]:
    """Generate realistic patient data."""
    random.seed(seed)
    np.random.seed(seed)

    first_names = [
        "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
        "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
        "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
        "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
        "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
        "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
        "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
        "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
        "Frank", "Rachel", "Alexander", "Carolyn", "Patrick", "Janet", "Raymond", "Catherine"
    ]

    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
        "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
        "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
        "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy"
    ]

    patients = []
    age_ranges = [(45, 55), (55, 65), (65, 75), (75, 90)]
    age_probs = [0.15, 0.25, 0.35, 0.25]

    for i in range(n):
        # Pick an age range based on probabilities
        range_idx = np.random.choice(len(age_ranges), p=age_probs)
        age_min, age_max = age_ranges[range_idx]
        age = random.randint(age_min, age_max - 1)

        patients.append({
            "id": i + 1,
            "name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "age": age,
            "mrn": f"MRN-{random.randint(100000, 999999)}",
        })

    return patients


def generate_access_patients(all_patients: list[dict], n_enrolled: int, n_programs: int = 3, seed: int = 42) -> list[dict]:
    """Select patients for ACCESS enrollment and assign programs from different vendors."""
    random.seed(seed)
    np.random.seed(seed)

    # ACCESS programs tend to enroll younger, healthier patients
    # Sort by age and bias toward younger
    sorted_patients = sorted(all_patients, key=lambda p: p["age"])

    # Take mostly from younger half, but some older
    younger_half = sorted_patients[:len(sorted_patients)//2]
    older_half = sorted_patients[len(sorted_patients)//2:]

    n_younger = int(n_enrolled * 0.7)
    n_older = n_enrolled - n_younger

    enrolled = random.sample(younger_half, min(n_younger, len(younger_half)))
    enrolled += random.sample(older_half, min(n_older, len(older_half)))
    enrolled = enrolled[:n_enrolled]

    # Group organizations by type
    bp_orgs = [o for o in ACCESS_ORGANIZATIONS if o["id"] < 10]
    pain_orgs = [o for o in ACCESS_ORGANIZATIONS if 10 <= o["id"] < 20]
    mh_orgs = [o for o in ACCESS_ORGANIZATIONS if o["id"] >= 20]

    for patient in enrolled:
        # Each patient signs up with different random vendors
        # They might have 1-3 programs, each from a DIFFERENT organization
        patient_programs = []

        if n_programs >= 1:
            # BP program from random BP vendor
            patient_programs.append(random.choice(bp_orgs))
        if n_programs >= 2:
            # Pain program from random pain vendor
            patient_programs.append(random.choice(pain_orgs))
        if n_programs >= 3:
            # Mental health from random MH vendor
            patient_programs.append(random.choice(mh_orgs))

        patient["programs"] = patient_programs
        patient["enrolled_date"] = datetime.now() - timedelta(days=random.randint(30, 365))

    return enrolled


def generate_weekly_messages(enrolled_patients: list[dict], week_date: datetime, seed: int = None) -> list[dict]:
    """Generate weekly inbox messages for all enrolled patients with varied formatting."""
    if seed:
        random.seed(seed)
        np.random.seed(seed)

    messages = []

    for patient in enrolled_patients:
        for org in patient["programs"]:
            # Generate outcome data based on program type (BP, Pain, or MH)
            org_id = org["id"]

            if org_id < 10:  # BP Control programs
                systolic = random.randint(110, 180)
                diastolic = random.randint(60, 110)
                controlled = systolic < 140 and diastolic < 90
                value = f"{systolic}/{diastolic}"
                if controlled:
                    status = random.choice(["Controlled", "At Goal", "Within Range", "Normal"])
                else:
                    status = random.choice(["NOT CONTROLLED", "Above Goal", "Elevated", "Out of Range", "High"])
                trend = random.choice(["improving", "stable", "worsening", "trending down", "trending up", "unchanged"])
                action_needed = not controlled

            elif org_id < 20:  # Pain programs
                score = random.randint(1, 10)
                value = str(score)
                if score <= 3:
                    status = random.choice(["Low", "Mild", "Well Controlled", "Minimal"])
                elif score <= 6:
                    status = random.choice(["Moderate", "Medium", "Concerning"])
                else:
                    status = random.choice(["High", "Severe", "Elevated", "Critical"])
                trend = random.choice(["improving", "stable", "worsening", "better", "worse", "no change"])
                action_needed = score >= 7

            else:  # Mental health programs (org_id >= 20)
                phq9 = random.randint(0, 27)
                value = str(phq9)
                if phq9 <= 4:
                    status = random.choice(["Minimal", "None-Minimal", "Low"])
                elif phq9 <= 9:
                    status = random.choice(["Mild", "Mild Symptoms"])
                elif phq9 <= 14:
                    status = random.choice(["Moderate", "Moderate Symptoms"])
                elif phq9 <= 19:
                    status = random.choice(["Moderately Severe", "Mod-Severe", "Significant"])
                else:
                    status = random.choice(["Severe", "Critical", "High Risk"])
                trend = random.choice(["improving", "stable", "worsening", "better", "declining", "unchanged"])
                action_needed = phq9 >= 15

            # Generate subject line using org's format
            subject = org["subject_format"].format(
                vendor=org["name"],
                program=org["program"],
                patient=patient["name"]
            )

            # Add urgent prefix for some organizations when action needed
            if action_needed and not org["friendly"]:
                urgent_prefix = random.choice([
                    org["urgent_phrase"] + ": ",
                    org["urgent_phrase"] + " - ",
                    "*** " + org["urgent_phrase"] + " *** ",
                    ""
                ])
                if urgent_prefix:
                    subject = urgent_prefix + subject

            messages.append({
                "date": week_date,
                "patient_name": patient["name"],
                "patient_mrn": patient["mrn"],
                "patient_age": patient["age"],
                "program": org["program"],
                "vendor": org["name"],
                "vendor_id": org["id"],
                "metric": org["metric"],
                "value": value,
                "unit": org["unit"],
                "status": status,
                "trend": trend,
                "action_needed": action_needed,
                "urgent_phrase": org["urgent_phrase"],
                "friendly": org["friendly"],
                "subject": subject,
            })

    return messages


# Sidebar controls
st.sidebar.header("Panel Settings")

total_panel = st.sidebar.slider(
    "Total Panel Size",
    min_value=500,
    max_value=3000,
    value=1500,
    step=100,
    help="Total number of patients in the PCP's panel"
)

access_enrolled = st.sidebar.slider(
    "ACCESS Enrolled",
    min_value=25,
    max_value=300,
    value=100,
    step=25,
    help="Number of patients enrolled in ACCESS programs"
)

programs_per_patient = st.sidebar.slider(
    "Programs per Patient",
    min_value=1,
    max_value=5,
    value=3,
    step=1,
    help="Number of ACCESS programs each patient is enrolled in"
)

weeks_to_show = st.sidebar.slider(
    "Weeks to Simulate",
    min_value=1,
    max_value=12,
    value=4,
    step=1,
)

st.sidebar.divider()

st.sidebar.subheader("Time Estimate")
seconds_per_message = st.sidebar.select_slider(
    "Seconds per Message",
    options=[30, 60, 90, 120],
    value=90,
    help="Time to open, review, and acknowledge each message"
)

if st.sidebar.button("Generate Inbox", type="primary", use_container_width=True):
    # Generate data
    all_patients = generate_patient_names(total_panel)
    enrolled = generate_access_patients(all_patients, access_enrolled, n_programs=programs_per_patient)

    # Generate messages for each week
    all_messages = []
    today = datetime.now()
    for week in range(weeks_to_show):
        week_date = today - timedelta(weeks=week)
        messages = generate_weekly_messages(enrolled, week_date, seed=42+week)
        all_messages.extend(messages)

    st.session_state["pcp_messages"] = all_messages
    st.session_state["pcp_enrolled"] = enrolled
    st.session_state["pcp_panel_size"] = total_panel
    st.session_state["pcp_weeks"] = weeks_to_show
    st.session_state["pcp_seconds_per_message"] = seconds_per_message
    st.rerun()


# Display results
if "pcp_messages" in st.session_state:
    messages = st.session_state["pcp_messages"]
    enrolled = st.session_state["pcp_enrolled"]
    panel_size = st.session_state["pcp_panel_size"]
    weeks = st.session_state["pcp_weeks"]
    secs_per_msg = st.session_state.get("pcp_seconds_per_message", 90)

    messages_df = pd.DataFrame(messages)

    weekly_messages = len(messages) // weeks
    action_needed = messages_df["action_needed"].sum()
    review_time_weekly = (weekly_messages * secs_per_msg) / 60  # convert to minutes

    # Key metrics
    st.subheader("The Numbers")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Weekly ACCESS Messages",
            f"{weekly_messages:,}",
            help="Messages arriving every week from ACCESS programs"
        )

    with col2:
        st.metric(
            "Monthly Message Volume",
            f"{weekly_messages * 4:,}",
        )

    with col3:
        st.metric(
            "Flagged for Action",
            f"{int(action_needed):,}",
            delta=f"{action_needed/len(messages)*100:.0f}% of total",
            delta_color="inverse"
        )

    with col4:
        st.metric(
            "Weekly Review Time",
            f"{review_time_weekly:.0f} min",
            help=f"Estimated at {secs_per_msg} seconds per message"
        )

    st.divider()

    # ==========================================
    # VISUAL INBOX SIMULATION
    # ==========================================
    st.subheader("Watch the Inbox Fill Up")

    # Day of week selector
    day_col1, day_col2 = st.columns([1, 3])
    with day_col1:
        selected_day = st.selectbox(
            "Simulate which day?",
            options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            index=1,  # Default to Tuesday
        )

    # Daily distribution - Monday gets 70%, other days split the rest
    day_percentages = {
        "Monday": 0.70,
        "Tuesday": 0.08,
        "Wednesday": 0.08,
        "Thursday": 0.08,
        "Friday": 0.06,
    }
    day_pct = day_percentages[selected_day]

    with day_col2:
        if selected_day == "Monday":
            st.warning(f"**Monday**: {int(day_pct * 100)}% of weekly messages arrive today.")
        else:
            st.info(f"**{selected_day}**: {int(day_pct * 100)}% of weekly messages arrive today. Most came Monday.")

    st.markdown("""
    Each message must be opened, reviewed, and acknowledged.
    **Click the button below to watch today's ACCESS messages arrive.**
    """)

    # Filter to most recent week and sample based on day
    recent_messages = messages_df[messages_df["date"] == messages_df["date"].max()].copy()
    recent_messages = recent_messages.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle

    # Take only the percentage for this day
    n_messages_today = max(1, int(len(recent_messages) * day_pct))
    recent_messages = recent_messages.head(n_messages_today)

    # Animation controls
    col_btn1, col_btn2, col_speed = st.columns([1, 1, 2])

    with col_btn1:
        animate_button = st.button("Watch Messages Arrive", type="primary")

    with col_btn2:
        show_all_button = st.button("Show All at Once")

    with col_speed:
        speed = st.select_slider(
            "Animation Speed",
            options=["Slow (realistic)", "Medium", "Fast", "Very Fast"],
            value="Fast"
        )

    speed_map = {"Slow (realistic)": 0.3, "Medium": 0.1, "Fast": 0.03, "Very Fast": 0.01}
    delay = speed_map[speed]

    # Inbox container
    inbox_placeholder = st.empty()
    counter_placeholder = st.empty()

    def render_inbox_message(msg, is_urgent=False):
        """Render a single inbox message as HTML with vendor-specific styling."""
        vendor_id = msg.get("vendor_id", 0)
        urgent_class = "urgent" if is_urgent else ""

        # Use the vendor's urgent phrase if action needed
        if msg["action_needed"]:
            action_text = f'<span style="color: #e74c3c; font-weight: bold;"> {msg.get("urgent_phrase", "ACTION REQUIRED")}</span>'
        else:
            action_text = ""

        return f'<div class="inbox-message {urgent_class}"><span class="inbox-time">{msg["date"].strftime("%I:%M %p")}</span><div class="inbox-header"><span class="vendor-tag vendor-{vendor_id}">{msg["vendor"]}</span> {msg["subject"]}</div><div class="inbox-preview">{msg["metric"]}: {msg["value"]} {msg["unit"]} — {msg["status"]} — Trend: {msg["trend"]}{action_text}</div></div>'

    def render_inbox(messages_to_show):
        """Render the full inbox."""
        html_parts = []
        for _, msg in messages_to_show.iterrows():
            html_parts.append(render_inbox_message(msg, msg["action_needed"]))
        return "".join(html_parts)

    if animate_button:
        # Animated message arrival
        messages_shown = []
        for i, (_, msg) in enumerate(recent_messages.iterrows()):
            messages_shown.append(msg)
            shown_df = pd.DataFrame(messages_shown)

            # Update counter
            action_count = sum(m["action_needed"] for m in messages_shown)
            counter_placeholder.markdown(f"""
            <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px; margin-bottom: 10px;">
                <span style="font-size: 36px; font-weight: bold; color: #2c3e50;">{len(messages_shown)}</span>
                <span style="font-size: 18px; color: #7f8c8d;"> messages</span>
                <span style="margin-left: 20px; font-size: 24px; font-weight: bold; color: #e74c3c;">{action_count}</span>
                <span style="font-size: 14px; color: #e74c3c;"> need action</span>
            </div>
            """, unsafe_allow_html=True)

            # Update inbox (show most recent 30 messages, scrolling)
            display_messages = shown_df.tail(30)
            inbox_html = f"""
            <div style="max-height: 500px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #fff;">
                {render_inbox(display_messages)}
            </div>
            """
            inbox_placeholder.markdown(inbox_html, unsafe_allow_html=True)

            time.sleep(delay)

            # Stop early if too many messages for demo
            if i >= 100:
                remaining = len(recent_messages) - i - 1
                inbox_placeholder.markdown(f"""
                <div style="max-height: 500px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #fff;">
                    {render_inbox(shown_df.tail(30))}
                    <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                        ... and {remaining} more messages ...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                break

        # Final state
        st.balloons()

    elif show_all_button:
        # Show all messages at once
        action_count = recent_messages["action_needed"].sum()
        counter_placeholder.markdown(f"""
        <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px; margin-bottom: 10px;">
            <span style="font-size: 36px; font-weight: bold; color: #2c3e50;">{len(recent_messages)}</span>
            <span style="font-size: 18px; color: #7f8c8d;"> messages</span>
            <span style="margin-left: 20px; font-size: 24px; font-weight: bold; color: #e74c3c;">{int(action_count)}</span>
            <span style="font-size: 14px; color: #e74c3c;"> need action</span>
        </div>
        """, unsafe_allow_html=True)

        inbox_html = f"""
        <div style="max-height: 500px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #fff;">
            {render_inbox(recent_messages.head(50))}
            {"<div style='text-align: center; padding: 20px; color: #7f8c8d;'>... and " + str(len(recent_messages) - 50) + " more messages ...</div>" if len(recent_messages) > 50 else ""}
        </div>
        """
        inbox_placeholder.markdown(inbox_html, unsafe_allow_html=True)

    else:
        # Default state - show empty inbox
        counter_placeholder.markdown(f"""
        <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px; margin-bottom: 10px;">
            <span style="font-size: 36px; font-weight: bold; color: #2c3e50;">0</span>
            <span style="font-size: 18px; color: #7f8c8d;"> messages</span>
            <span style="margin-left: 20px; font-size: 24px; font-weight: bold; color: #e74c3c;">0</span>
            <span style="font-size: 14px; color: #e74c3c;"> need action</span>
        </div>
        """, unsafe_allow_html=True)

        inbox_placeholder.markdown(f"""
        <div style="max-height: 500px; border: 1px solid #ddd; border-radius: 8px; padding: 40px; background: #fff; text-align: center; color: #7f8c8d;">
            <p style="font-size: 18px;">Inbox empty</p>
            <p>Click "Watch Messages Arrive" to see {selected_day}'s {n_messages_today} ACCESS messages flood in</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ==========================================
    # CONTEXT AND STATS
    # ==========================================
    st.markdown(f"""
    ### The Reality

    This PCP has **{panel_size:,} patients** in their panel. Only **{len(enrolled)}** ({len(enrolled)/panel_size*100:.1f}%)
    are enrolled in ACCESS programs.

    Yet those {len(enrolled)} patients generate **{weekly_messages:,} messages per week** —
    that's **{weekly_messages * 52:,} messages per year** from just {len(enrolled)/panel_size*100:.1f}% of the panel.

    At 30 seconds per message, that's **{review_time_weekly * 52 / 60:.0f} hours per year** spent reviewing ACCESS updates.
    """)

    st.divider()

    # ==========================================
    # DAILY BURDEN HEATMAP
    # ==========================================
    st.subheader("When Do Messages Arrive?")

    st.markdown("""
    ACCESS programs batch their weekly updates. Here's what a typical month looks like,
    with messages arriving mostly on Monday mornings when PCPs are trying to catch up.
    """)

    # Generate daily message counts for a month
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weeks_labels = ["Week 1", "Week 2", "Week 3", "Week 4"]

    # Most messages arrive Monday (70%), rest spread across the week
    daily_pattern = [0.70, 0.08, 0.08, 0.08, 0.06, 0.0, 0.0]
    messages_per_week = weekly_messages

    heatmap_data = []
    for week in weeks_labels:
        week_data = [int(messages_per_week * p) for p in daily_pattern]
        heatmap_data.append(week_data)

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=days_of_week,
        y=weeks_labels,
        colorscale=[
            [0, "#f0f9e8"],
            [0.2, "#bae4bc"],
            [0.4, "#7bccc4"],
            [0.6, "#43a2ca"],
            [0.8, "#0868ac"],
            [1, "#084081"]
        ],
        text=[[str(v) for v in row] for row in heatmap_data],
        texttemplate="%{text}",
        textfont={"size": 14},
        hovertemplate="Day: %{x}<br>Week: %{y}<br>Messages: %{z}<extra></extra>",
    ))

    fig_heatmap.update_layout(
        xaxis_title="Day of Week",
        yaxis_title="",
        template="plotly_white",
        height=300,
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)

    monday_messages = int(messages_per_week * 0.70)
    monday_minutes = int((monday_messages * secs_per_msg) / 60)
    st.warning(f"""
    **Monday Morning**: {monday_messages} messages waiting when you start your week.

    That's **{monday_minutes} minutes** of inbox review before you can see your first patient.
    """)

    st.divider()

    # ==========================================
    # VISUALIZATIONS
    # ==========================================

    # Add program type based on vendor_id
    def get_program_type(vendor_id):
        if vendor_id < 10:
            return "Blood Pressure"
        elif vendor_id < 20:
            return "Pain Management"
        else:
            return "Mental Health"

    messages_df["program_type"] = messages_df["vendor_id"].apply(get_program_type)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Messages by Program Type")

        program_counts = messages_df.groupby("program_type").size().reset_index(name="count")
        # Sort by count descending
        program_counts = program_counts.sort_values("count", ascending=False)

        fig_programs = go.Figure(data=[
            go.Bar(
                x=program_counts["program_type"],
                y=program_counts["count"],
                marker_color=["#e74c3c", "#3498db", "#9b59b6"],
            )
        ])

        fig_programs.update_layout(
            xaxis_title="Program Type",
            yaxis_title="Total Messages",
            template="plotly_white",
            height=350,
        )

        st.plotly_chart(fig_programs, use_container_width=True)

    with col2:
        st.markdown("### Action Required by Type")

        action_by_type = messages_df.groupby("program_type").agg({
            "action_needed": ["sum", "count"]
        }).reset_index()
        action_by_type.columns = ["program_type", "action_needed", "total"]
        action_by_type["no_action"] = action_by_type["total"] - action_by_type["action_needed"]

        fig_action = go.Figure()

        fig_action.add_trace(go.Bar(
            x=action_by_type["program_type"],
            y=action_by_type["no_action"],
            name="Routine",
            marker_color="#2ecc71",
        ))

        fig_action.add_trace(go.Bar(
            x=action_by_type["program_type"],
            y=action_by_type["action_needed"],
            name="Action Needed",
            marker_color="#e74c3c",
        ))

        fig_action.update_layout(
            barmode="stack",
            xaxis_title="Program Type",
            yaxis_title="Messages",
            template="plotly_white",
            height=350,
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        )

        st.plotly_chart(fig_action, use_container_width=True)

    # Show vendor diversity
    st.markdown(f"**{messages_df['vendor'].nunique()} different ACCESS vendors** sending messages with inconsistent formats.")

    st.divider()

    # ==========================================
    # THE BURDEN
    # ==========================================
    st.error("""
    ### The Hidden Burden

    **ACCESS programs shift work to PCPs without compensation.**

    - Each message requires the PCP to **open, review, acknowledge**
    - "Action needed" flags create **liability** — the PCP must respond or document why not
    - None of this inbox time is **billable** or reimbursed
    - PCPs already spend **2 hours on EHR work for every 1 hour with patients**

    ACCESS vendors get paid per-member-per-month. The PCP gets more inbox.
    """)

    st.divider()

    # Time comparison
    st.markdown("### Time Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Without ACCESS Programs:**
        - PCP sees patients
        - Documents visits
        - Reviews labs when ordered
        - Responds to patient messages
        """)

    with col2:
        st.markdown(f"""
        **With ACCESS Programs:**
        - All of the above, PLUS:
        - {weekly_messages:,} weekly vendor messages
        - {int(action_needed/weeks):,} "action required" flags per week
        - {review_time_weekly:.0f} minutes/week reviewing reports
        - Liability for every flagged result
        """)

    # Annual burden calculation
    st.divider()
    st.markdown("### Annual ACCESS Burden")

    annual_messages = weekly_messages * 52
    annual_hours = (annual_messages * secs_per_msg) / 3600  # seconds to hours

    fig_annual = go.Figure()

    fig_annual.add_trace(go.Bar(
        x=["ACCESS Inbox Review"],
        y=[annual_hours],
        name="ACCESS Review",
        marker_color="#e74c3c",
        text=[f"{annual_hours:.0f} hrs"],
        textposition="auto",
    ))

    fig_annual.add_trace(go.Bar(
        x=["Typical Admin Time"],
        y=[500],  # ~10 hrs/week admin
        name="Other Admin",
        marker_color="#3498db",
        text=["500 hrs"],
        textposition="auto",
    ))

    fig_annual.add_trace(go.Bar(
        x=["Direct Patient Care"],
        y=[1500],  # ~30 hrs/week
        name="Patient Care",
        marker_color="#2ecc71",
        text=["1,500 hrs"],
        textposition="auto",
    ))

    fig_annual.update_layout(
        yaxis_title="Hours per Year",
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    st.plotly_chart(fig_annual, use_container_width=True)

    st.markdown(f"""
    > ACCESS inbox review adds **{annual_hours:.0f} hours/year** — equivalent to
    > **{annual_hours/8:.0f} full workdays** spent on vendor-generated messages.
    >
    > This is {annual_hours/1500*100:.1f}% of direct patient care time, consumed by messages
    > about just {len(enrolled)/panel_size*100:.1f}% of the panel.
    """)

    # ==========================================
    # COMPENSATION VS BURDEN
    # ==========================================
    st.divider()
    st.markdown("### The Economics: What the PCP Gets Paid")

    st.markdown("""
    Under ACCESS, the **maximum** a PCP can receive for care coordination is **$100/year**
    (paid as $30/quarter, capped at $100). Let's see how that compares to **just the inbox work** —
    not the actual patient care, just reading and acknowledging vendor emails.
    """)

    # Calculate per-patient economics
    n_enrolled = len(enrolled)
    n_programs_avg = len(messages) / weeks / n_enrolled  # average programs per patient
    messages_per_patient_per_year = n_programs_avg * 52
    hours_per_patient_per_year = (messages_per_patient_per_year * secs_per_msg) / 3600  # seconds to hours
    pcp_hourly_rate = 150  # typical PCP hourly rate

    # Value of PCP time spent on ACCESS inbox for this patient
    pcp_time_value = hours_per_patient_per_year * pcp_hourly_rate
    max_pcp_payment = 100  # $100/year max under ACCESS

    col1, col2 = st.columns(2)

    with col1:
        # Bar chart comparing payment vs time value
        fig_econ = go.Figure()

        fig_econ.add_trace(go.Bar(
            x=["ACCESS Payment (max)", "Cost of Email Time"],
            y=[max_pcp_payment, pcp_time_value],
            marker_color=["#2ecc71", "#e74c3c"],
            text=[f"${max_pcp_payment}", f"${pcp_time_value:.0f}"],
            textposition="outside",
        ))

        fig_econ.update_layout(
            title="Per Patient, Per Year (Email Time Only)",
            yaxis_title="Dollars ($)",
            template="plotly_white",
            height=350,
            yaxis=dict(range=[0, max(pcp_time_value * 1.2, 150)]),
        )

        st.plotly_chart(fig_econ, use_container_width=True)

    with col2:
        # Summary metrics
        st.markdown(f"""
        **Per ACCESS Patient Per Year (EMAIL TIME ONLY):**

        | | |
        |---|---:|
        | Vendor emails received | {messages_per_patient_per_year:.0f} |
        | Time reading emails | {hours_per_patient_per_year:.1f} hours |
        | Value of email time @ \\$150/hr | **\\${pcp_time_value:.0f}** |
        | ACCESS pays PCP (max) | **\\${max_pcp_payment}** |
        | **Net loss on emails alone** | **\\${pcp_time_value - max_pcp_payment:.0f}** |
        """)

        deficit_pct = ((pcp_time_value - max_pcp_payment) / pcp_time_value) * 100
        st.error(f"""
        The PCP loses **\\${pcp_time_value - max_pcp_payment:.0f}** per ACCESS patient
        **just reading vendor emails** ({deficit_pct:.0f}% unpaid).

        For {n_enrolled} patients: **\\${(pcp_time_value - max_pcp_payment) * n_enrolled:,.0f}/year** lost on inbox alone.

        This doesn't include time spent actually caring for these patients.
        """)

    # Total panel economics
    st.markdown("### Total Panel Economics (Email Time Only)")

    total_access_revenue = max_pcp_payment * n_enrolled
    total_time_value = pcp_time_value * n_enrolled

    fig_total = go.Figure()

    fig_total.add_trace(go.Bar(
        name="ACCESS Payment (max)",
        x=["Revenue", "Cost of Email Time"],
        y=[total_access_revenue, 0],
        marker_color="#2ecc71",
    ))

    fig_total.add_trace(go.Bar(
        name="PCP Email Time Value",
        x=["Revenue", "Cost of Email Time"],
        y=[0, total_time_value],
        marker_color="#e74c3c",
    ))

    fig_total.update_layout(
        title=f"Annual Email Economics for {n_enrolled} ACCESS Patients",
        yaxis_title="Dollars ($)",
        template="plotly_white",
        height=350,
        barmode="group",
        showlegend=True,
    )

    st.plotly_chart(fig_total, use_container_width=True)

    st.warning(f"""
**The math doesn't work — and this is JUST for reading emails.**

- ACCESS pays the PCP (max): **\\${total_access_revenue:,.0f}/year**
- Value of PCP email time (@ \\$150/hr): **\\${total_time_value:,.0f}/year**
- **Net annual loss on inbox alone: \\${total_time_value - total_access_revenue:,.0f}**

ACCESS vendors get paid \\$50-80/month per patient.
The PCP gets \\$30/quarter max (\\$100/year) — just to read their emails.

**The actual patient visits and care coordination are additional unpaid work.**
""")

else:
    # Initial state
    st.info("Click **Generate Inbox** in the sidebar to simulate the PCP's ACCESS message burden.")

    st.markdown("""
    ### The Setup

    - **Panel size**: 1,500 patients (typical for primary care)
    - **ACCESS enrolled**: 100 patients (6.7% of panel)
    - **Programs per patient**: 3 (each from a different vendor!)
    - **Update frequency**: Weekly per program
    - **Vendors**: 30 different ACCESS organizations, each with their own email format

    ### The Math

    ```
    100 patients × 3 programs × 1 update/week = 300 messages/week
    300 messages × 52 weeks = 15,600 messages/year
    15,600 messages × 90 seconds each = 390 hours/year
    ```

    That's **nearly 10 weeks** of full-time work reviewing vendor messages for 6.7% of patients.

    ### What Each Message Contains

    Each ACCESS program sends weekly updates like:

    | Program | Metric | Example Update |
    |---------|--------|----------------|
    | BP Control | Blood Pressure | "142/88 mmHg - NOT CONTROLLED - Trending up" |
    | MSK Pain | Pain Score | "7/10 - High - Action recommended" |
    | Depression | PHQ-9 | "14 - Moderate - Stable" |

    The PCP must open each message, review the data, and either:
    - Acknowledge (routine)
    - Take action (call patient, adjust meds, order labs)
    - Document why no action taken (liability protection)
    """)

    st.warning("""
    **The perverse incentive**: ACCESS vendors get paid PMPM whether or not the PCP reviews
    these messages. But the PCP bears liability if they miss a "flagged" result.
    """)
