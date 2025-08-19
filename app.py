import streamlit as st
import json

st.set_page_config(page_title="AI Readiness (Demo)", page_icon="💞", layout="centered")
st.title("💞 AI Readiness & Compatibility Tool — Demo")

# Weights for the 5 readiness dimensions (must add up to 1.0)
READINESS_WEIGHTS = {
    "emotional_maturity": 0.25,
    "faith_values": 0.25,
    "family_of_origin": 0.15,
    "practical_readiness": 0.15,
    "relational_skills": 0.20,
}

# Two nudges per dimension (shown for your lowest dimensions)
NUDGES = {
    "emotional_maturity": [
        "Apologize once this week without any qualifiers, and journal what you learned.",
        "Name your feeling before reacting in a tough conversation."
    ],
    "faith_values": [
        "Schedule one weekly practice (worship/study/service).",
        "Write your top 3 convictions and how they shape daily choices."
    ],
    "family_of_origin": [
        "List 2 patterns from your parents you want to repeat, and 2 you will avoid.",
        "Write a letter (not sent) to a family member expressing how a past event affected you."
    ],
    "practical_readiness": [
        "Track every expense for 14 days and tag needs vs wants.",
        "Create a simple monthly budget and try it for one pay cycle."
    ],
    "relational_skills": [
        "In your next 3 conversations, ask two clarifying questions before offering advice.",
        "Practice reflecting back what you heard before you respond."
    ]
}

# 10 simple questions → each maps to a dimension
QUESTIONS = [
    ("Q_EMO_01","emotional_maturity","scale","I can acknowledge my mistakes without blaming others.", [1,2,3,4,5]),
    ("Q_EMO_02","emotional_maturity","choice","When hurt, I typically:", ["withdraw","attack","seek_repair","adapt"]),
    ("Q_VAL_01","faith_values","scale","My faith/values guide my daily decisions.", [1,2,3,4,5]),
    ("Q_VAL_02","faith_values","choice","I would marry someone outside my core faith convictions:", ["yes","no","unsure"]),
    ("Q_FAM_01","family_of_origin","choice","Conflict in my family growing up was:", ["avoided","explosive","resolved","mixed"]),
    ("Q_FAM_02","family_of_origin","scale","I have processed wounds from my family of origin.", [1,2,3,4,5]),
    ("Q_PRA_01","practical_readiness","choice","Do you track a monthly budget?", ["none","sometimes","yes"]),
    ("Q_PRA_02","practical_readiness","bool","Are you financially independent from your family?", ["No","Yes"]),
    ("Q_REL_01","relational_skills","scale","I practice active listening in conversations.", [1,2,3,4,5]),
    ("Q_REL_02","relational_skills","scale","I can disagree without disrespect.", [1,2,3,4,5]),
]

def normalize_scale(v, maxv=5.0):
    try:
        vv = float(v)
        vv = max(1.0, min(maxv, vv))
        return vv/maxv
    except Exception:
        return 0.5

def score_readiness(responses_dict):
    subs = {k:0.0 for k in READINESS_WEIGHTS}
    counts = {k:0.0 for k in READINESS_WEIGHTS}
    for qid, dim, qtype, _prompt, choices in QUESTIONS:
        if qid not in responses_dict:
            continue
        val = str(responses_dict[qid]).lower()
        s = 0.5
        if qtype == "scale":
            s = normalize_scale(val)
        elif qtype == "bool":
            s = 1.0 if val in ("yes","true","1") else 0.0
        elif qtype == "choice":
            good = ("seek_repair","adapt","resolved","yes")
            bad  = ("withdraw","attack","avoided","none","no","mismatch")
            if any(k in val for k in good):
                s = 0.8
            if any(k in val for k in bad):
                s = 0.2
            if val == "unsure":
                s = 0.5
        subs[dim] += s; counts[dim] += 1.0
    for k in subs:
        subs[k] = (subs[k]/counts[k]) if counts[k] > 0 else 0.5
    overall = sum(subs[k]*READINESS_WEIGHTS[k] for k in subs)
    # pick 2 lowest dimensions for nudges
    gaps = sorted(subs.items(), key=lambda kv: kv[1])[:2]
    nudges = []
    for dim, _ in gaps:
        nudges.extend(NUDGES.get(dim, [])[:1])
    return overall, subs, nudges

st.caption("Answer honestly — this is for your growth and discernment.")
name = st.text_input("Your name (optional)", "")

answers = {}
col1, col2 = st.columns(2)
half = len(QUESTIONS)//2
with col1:
    for qid, dim, qtype, prompt, choices in QUESTIONS[:half]:
        if qtype == "scale":
            answers[qid] = st.slider(prompt, min_value=1, max_value=5, value=3, key=qid)
        elif qtype == "bool":
            answers[qid] = st.radio(prompt, ["No","Yes"], horizontal=True, key=qid)
        else:
            answers[qid] = st.selectbox(prompt, choices, key=qid)
with col2:
    for qid, dim, qtype, prompt, choices in QUESTIONS[half:]:
        if qtype == "scale":
            answers[qid] = st.slider(prompt, min_value=1, max_value=5, value=3, key=qid)
        elif qtype == "bool":
            answers[qid] = st.radio(prompt, ["No","Yes"], horizontal=True, key=qid)
        else:
            answers[qid] = st.selectbox(prompt, choices, key=qid)

if st.button("Compute Readiness", type="primary"):
    overall, subs, nudges = score_readiness(answers)
    st.success(f"Overall Readiness: **{round(overall*100,1)}%**")
    st.write("**Subscores**")
    for k, v in subs.items():
        st.write(f"- {k.replace('_',' ').title()}: {round(v*100,1)}%")
    if nudges:
        st.write("**Growth Nudges (next steps)**")
        for n in nudges:
            st.write(f"• {n}")

    # downloadable JSON report
    report = {
        "type": "readiness_report",
        "name": name or "anonymous",
        "overall": round(overall*100,1),
        "subscores": {k: round(v*100,1) for k,v in subs.items()},
        "nudges": nudges
    }
    st.download_button(
        "Download Readiness Report (JSON)",
        data=json.dumps(report, indent=2),
        file_name=f"{(name or 'readiness').replace(' ','_')}_report.json",
        mime="application/json"
    )

