# pages/1_Wellbeing_and_Survey.py
import streamlit as st
import os
import random
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from sqlalchemy import create_engine, text
import uuid, streamlit as st
from datetime import datetime

st.set_page_config(page_title="Wellbeing & Survey", page_icon="📝")
# --- Compact Likert row styling (optional) ---
st.markdown("""
<style>
.likert-row { margin-bottom: 0.75rem; }
.likert-q { font-weight: 600; margin-bottom: 0.25rem; }
.likert-anchors { font-size: 0.85rem; color: #555; margin-top: -0.25rem; }
</style>
""", unsafe_allow_html=True)
def likert_row(question: str, left_anchor: str, right_anchor: str, options, key: str):
    # Automatically merge anchors into first/last options
    options = list(options)
    if options and isinstance(options[0], int):
        options[0] = f"{options[0]} {left_anchor}"
        options[-1] = f"{options[-1]} {right_anchor}"

    st.markdown(f"**{question}**")
    choice = st.radio(
        label=question,
        options=options,
        horizontal=True,
        index=None,           # ensure no default selection
        key=key,
        label_visibility="collapsed",
    )
    return choice




st.markdown("""
    <style>
    * {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
    }
    input, textarea {
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
        user-select: text !important;
    }
    </style>
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', event => event.preventDefault());
    document.addEventListener('cut', event => event.preventDefault());
    document.addEventListener('paste', event => event.preventDefault());
    </script>
""", unsafe_allow_html=True)
from sqlalchemy import create_engine, text
import uuid, streamlit as st

# If insert_result is in app.py, import it; otherwise move helpers to db.py and import from there.
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], pool_pre_ping=True)
from sqlalchemy import text
import uuid
from datetime import datetime
from sqlalchemy import text, inspect
import uuid
from datetime import datetime

NEW_COLUMNS = [
    ("wellbeing_choice", "TEXT"),
    ("comments_wellbeing", "TEXT"),
    ("ai_freq", "TEXT"),
    ("aias_life", "INTEGER"),
    ("aias_work", "INTEGER"),
    ("aias_future", "INTEGER"),
    ("aias_humanity", "INTEGER"),
    ("aias_attention", "INTEGER"),
    ("tipi_reserved", "INTEGER"),
    ("tipi_trusting", "INTEGER"),
    ("tipi_lazy", "INTEGER"),
    ("tipi_relaxed", "INTEGER"),
    ("tipi_few_artistic", "INTEGER"),
    ("tipi_outgoing", "INTEGER"),
    ("tipi_fault_finding", "INTEGER"),
    ("tipi_thorough", "INTEGER"),
    ("tipi_nervous", "INTEGER"),
    ("tipi_imagination", "INTEGER"),
]

def _ensure_results_table(conn):
    # Creates baseline if it doesn't exist (old schema compatible)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS results (
          id UUID PRIMARY KEY,
          timestamp TEXT,
          prolific_pid TEXT,
          session_id TEXT,
          topic TEXT,
          user_prompt TEXT,
          response_a TEXT,
          response_b TEXT,
          response_c TEXT,
          user_choice TEXT,
          comments TEXT
        );
    """))

def _ensure_missing_columns(conn):
    inspector = inspect(conn)
    # inspector.get_columns works across dialects when using an Engine/Connection
    existing_cols = {c["name"] for c in inspector.get_columns("results")}

    # Dialect-specific minor tweaks if you ever need them
    dialect = conn.engine.dialect.name  # 'sqlite', 'postgresql', 'mysql', etc.

    for col, coltype in NEW_COLUMNS:
        if col not in existing_cols:
            # SQLite/Postgres/MySQL all accept ALTER ... ADD COLUMN (simple cases)
            conn.execute(text(f'ALTER TABLE results ADD COLUMN {col} {coltype};'))

def insert_result(row):
    eng = get_engine()
    with eng.begin() as conn:
        _ensure_results_table(conn)
        _ensure_missing_columns(conn)

        conn.execute(text("""
            INSERT INTO results (
              id, timestamp, prolific_pid, session_id, topic, user_prompt,
              response_a, response_b, response_c, user_choice, comments,
              wellbeing_choice, comments_wellbeing,
              ai_freq, aias_life, aias_work, aias_future, aias_humanity, aias_attention,
              tipi_reserved, tipi_trusting, tipi_lazy, tipi_relaxed, tipi_few_artistic,
              tipi_outgoing, tipi_fault_finding, tipi_thorough, tipi_nervous, tipi_imagination
            ) VALUES (
              :id, :ts, :pid, :sid, :topic, :up,
              :ra, :rb, :rc, :choice, :comments,
              :wellbeing_choice, :comments_wellbeing,
              :ai_freq, :aias_life, :aias_work, :aias_future, :aias_humanity, :aias_attention,
              :tipi_reserved, :tipi_trusting, :tipi_lazy, :tipi_relaxed, :tipi_few_artistic,
              :tipi_outgoing, :tipi_fault_finding, :tipi_thorough, :tipi_nervous, :tipi_imagination
            )
        """), dict(
            id=str(uuid.uuid4()),
            ts=datetime.utcnow().isoformat(),
            pid=row.get("prolific_pid"),
            sid=row.get("session_id"),
            topic=row.get("topic"),
            up=row.get("user_prompt"),
            ra=row.get("response_a"),
            rb=row.get("response_b"),
            rc=row.get("response_c"),
            choice=row.get("user_choice"),
            comments=row.get("comments"),
            wellbeing_choice=row.get("wellbeing_choice"),
            comments_wellbeing=row.get("comments_wellbeing"),
            ai_freq=row.get("ai_freq"),
            aias_life=row.get("aias_life"),
            aias_work=row.get("aias_work"),
            aias_future=row.get("aias_future"),
            aias_humanity=row.get("aias_humanity"),
            aias_attention=row.get("aias_attention"),
            tipi_reserved=row.get("tipi_reserved"),
            tipi_trusting=row.get("tipi_trusting"),
            tipi_lazy=row.get("tipi_lazy"),
            tipi_relaxed=row.get("tipi_relaxed"),
            tipi_few_artistic=row.get("tipi_few_artistic"),
            tipi_outgoing=row.get("tipi_outgoing"),
            tipi_fault_finding=row.get("tipi_fault_finding"),
            tipi_thorough=row.get("tipi_thorough"),
            tipi_nervous=row.get("tipi_nervous"),
            tipi_imagination=row.get("tipi_imagination"),
        ))

# st.title("Wellbeing Choice & Short Survey")

# --- Guardrail: ensure step 1 exists
if "initial_payload" not in st.session_state:
    st.warning("Please make an initial choice on the main page first.")
    st.page_link("app.py", label="Back to main page", icon="⬅️")
    st.stop()

payload = st.session_state.initial_payload

# Optional: let participants re-open responses for reference
# with st.expander("Show the three responses again"):
#     st.subheader("Response A"); st.write(payload["response_a"])
#     st.subheader("Response B"); st.write(payload["response_b"])
#     st.subheader("Response C"); st.write(payload["response_c"])

# with st.container():
#     st.subheader("Response A"); st.write(payload["response_a"])
#     st.subheader("Response B"); st.write(payload["response_b"])
#     st.subheader("Response C"); st.write(payload["response_c"])

# =========================================
# 1) Wellbeing-aware preference (FIRST)
# =========================================
# =========================================
# 1) Wellbeing-aware preference (FIRST)
# =========================================
st.markdown("### Now, which response is most beneficial to your <u>long-term wellbeing</u>?", unsafe_allow_html=True)

# Build display text for each response
options = {
    "A":'**Response A:** '+payload["response_a"].strip(),
    "B": '**Response B:** '+payload["response_b"].strip(),
    "C": '**Response C:** '+payload["response_c"].strip()
}

# Display the radio with the full response texts
wellbeing_choice = st.radio(
    label="Select the response most beneficial to your long-term wellbeing:",
    options=list(options.keys()),
    format_func=lambda x: options[x],   # 👈 shows actual text instead of "A/B/C"
    index=None,                         # 👈 ensures no default
    key="wellbeing_choice",
)


# st.markdown("### Now, which response is most beneficial to your **long-term wellbeing**?")
# wellbeing_choice = st.radio("",
#     ["A", "B", "C"],
#     horizontal=True,
#     index=None,
#     key="wellbeing_choice",
# )
 # -------------------------
    # --- NEW: Comments query
    # -------------------------
comments_wellbeing = st.text_area(
        "Comments:",
        placeholder="Your comments",
        key="comments_box"
    )

st.markdown("---")

# =========================================
# 2) Survey (AI use, attitudes, TIPI)
# =========================================

# --- AI use frequency
st.subheader("How often do you use AI chatbots?")
ai_freq = st.radio(
    "How often do you use AI chatbots?",
    ["Daily", "A few times a week", "A few times a month", "Once every few months", "Never"],
    index=None,
)

# --- Attitudes toward AI (1–10) with attention check
st.subheader("How much do you agree with the following statements?")

aias_life = likert_row(
    "I believe that AI will improve my life.",
    left_anchor="Not at all",
    right_anchor="Completely agree",
    options=range(1, 11),
    key="aias_life",
)

aias_work = likert_row(
    "I believe that AI will improve my work.",
    left_anchor="Not at all",
    right_anchor="Completely agree",
    options=range(1, 11),
    key="aias_work",
)

aias_future = likert_row(
    "I think I will use AI technology in the future.",
    left_anchor="Not at all",
    right_anchor="Completely agree",
    options=range(1, 11),
    key="aias_future",
)

aias_humanity = likert_row(
    "I think AI technology is positive for humanity.",
    left_anchor="Not at all",
    right_anchor="Completely agree",
    options=range(1, 11),
    key="aias_humanity",
)

aias_attention = likert_row(
    "As an attention check, please select 10 (Completely agree).",
    left_anchor="Not at all",
    right_anchor="Completely agree",
    options=range(1, 11),
    key="aias_attention",
)

# --- TIPI (1–5)
st.subheader("I see myself as someone who...")

tipi_reserved = likert_row("… is reserved",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_reserved")
tipi_trusting = likert_row("… is generally trusting",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_trusting")
tipi_lazy = likert_row("… tends to be lazy",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_lazy")
tipi_relaxed = likert_row("… is relaxed, handles stress well",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_relaxed")
tipi_few_artistic = likert_row("… has few artistic interests",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_few_artistic")
tipi_outgoing = likert_row("… is outgoing, sociable",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_outgoing")
tipi_faultfinding = likert_row("… tends to find fault with others",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_fault_finding")
tipi_thorough = likert_row("… does a thorough job",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_thorough")
tipi_nervous = likert_row("… gets nervous easily",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_nervous")
tipi_imagination = likert_row("… has an active imagination",
    "Disagree strongly", "Agree strongly", range(1, 6), "tipi_imagination")

st.markdown("---")

# =========================================
# Final submit (writes once)
# =========================================
if st.button("Submit survey & finalize"):
    # # Validation
    # if not comments.strip():
    #     st.error("Please add a comment before continuing.")
    #     st.stop()  # prevent moving on
        
    # if wellbeing_choice is None:
    #     st.error("Please select your preference considering wellbeing."); st.stop()
    # if ai_freq is None:
    #     st.error("Please answer how often you use AI chatbots."); st.stop()
    # if aias_attention != 10:
    #     st.error("Attention check not passed. Please set the attention-check item to 10."); st.stop()
 # --- Validation ---
    errors = []

    # Comments box (uses session_state key to be safe)
    comments_value = st.session_state.get("comments_box", "").strip()
    if not comments_value:
        errors.append("Please add a brief comment in the Comments box.")

    # Required radios
    if wellbeing_choice is None:
        errors.append("Please select which response is best for long-term wellbeing (A, B, or C).")
    if ai_freq is None:
        errors.append("Please answer how often you use AI chatbots.")

    # Attitudes toward AI (1–10)
    required_aias = {
        "aias_life": aias_life,
        "aias_work": aias_work,
        "aias_future": aias_future,
        "aias_humanity": aias_humanity,
        "aias_attention": aias_attention,
    }
    for k, v in required_aias.items():
        if v is None:
            errors.append("Please answer all Attitudes Toward AI items (1–10 scale).")
            break

    # TIPI items (1–5)
    required_tipis = {
        "tipi_reserved": tipi_reserved,
        "tipi_trusting": tipi_trusting,
        "tipi_lazy": tipi_lazy,
        "tipi_relaxed": tipi_relaxed,
        "tipi_few_artistic": tipi_few_artistic,
        "tipi_outgoing": tipi_outgoing,
        "tipi_fault_finding": tipi_faultfinding,
        "tipi_thorough": tipi_thorough,
        "tipi_nervous": tipi_nervous,
        "tipi_imagination": tipi_imagination,
    }
    for k, v in required_tipis.items():
        if v is None:
            errors.append("Please answer all personality items (1–5 scale).")
            break

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    insert_result({
        # from step 1
        **payload,

        # wellbeing-aware choice FIRST on this page
        "wellbeing_choice": wellbeing_choice,
        "comments_wellbeing":  (comments_wellbeing or "").strip(),
        # survey fields
        "ai_freq": ai_freq,

        "aias_life": aias_life,
        "aias_work": aias_work,
        "aias_future": aias_future,
        "aias_humanity": aias_humanity,
        "aias_attention": aias_attention,

        "tipi_reserved": tipi_reserved,
        "tipi_trusting": tipi_trusting,
        "tipi_lazy": tipi_lazy,
        "tipi_relaxed": tipi_relaxed,
        "tipi_few_artistic": tipi_few_artistic,
        "tipi_outgoing": tipi_outgoing,
        "tipi_fault_finding": tipi_faultfinding,
        "tipi_thorough": tipi_thorough,
        "tipi_nervous": tipi_nervous,
        "tipi_imagination": tipi_imagination,
    })

    st.success("✅ Thanks! Your responses have been recorded.")
    st.page_link("app.py", label="Back to main page", icon="🏠")



