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

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], pool_pre_ping=True)
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

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# --- Setup / OpenAI ------
# -------------------------
# ======================= CONSENT GATE (add near top) ==========================
import pandas as pd, os, time
from datetime import datetime

CONSENT_FILE = "consent.csv"

CONSENT_COLUMNS = [
    "timestamp_utc", "prolific_pid", "session_id",
    "consent", "reason_if_declined", "user_agent"
]

# Ensure file exists with header (under a lock)
if not os.path.exists(CONSENT_FILE):
        pd.DataFrame(columns=CONSENT_COLUMNS).to_csv(CONSENT_FILE, index=False)

st.markdown("## Consent to Participate")
st.write("""
**Study purpose.** You are invited to take part in a research study about how people evaluate AI-generated responses.

**What you’ll do.** You’ll write about a scenario, view several AI responses, select a preferred response, and leave comments. Approx. 3–7 minutes.

**Risks/benefits.** Minimal risk; some scenarios could be mildly sensitive. You may skip anything you’d prefer not to answer.

**Compensation.** As listed on Prolific.

**Voluntary participation.** Your participation is voluntary. You may stop at any time.

**Data.** We collect your Prolific PID, your inputs, your selections/ratings, and timestamps. Data will be used for research and may be shared in aggregate/anonymized form.

**Contact/IRB.** If you have any questions, concerns or complaints about this research, its procedures, risks and benefits, contact the Protocol Director, Myra Cheng (myra@cs.stanford.edu)
""")

already_consented = st.session_state.get("consented", False)

with st.form("consent_form", clear_on_submit=False):
    agree = st.checkbox("I consent to participate.", value=already_consented)
    decline_reason = st.text_input("If you do not consent, you may (optionally) tell us why.", value="")
    submitted_consent = st.form_submit_button("Continue")

if submitted_consent:
    consent_value = "agree" if agree else "decline"
    row = pd.DataFrame([{
        "timestamp_utc": datetime.utcnow().isoformat(),
        "prolific_pid": st.query_params.get("PROLIFIC_PID", ["anon"]),
        "session_id": st.query_params.get("SESSION_ID", ["none"]),
        "consent": consent_value,
        "reason_if_declined": decline_reason.strip(),
        "user_agent": st.session_state.get("_user_agent", "")  # optional; see below if you want to capture it
    }])[CONSENT_COLUMNS]

    row.to_csv(CONSENT_FILE, mode="a", header=False, index=False)

    st.session_state.consented = agree

# Gate the rest of the app
if not st.session_state.get("consented", False):
    st.info("You must consent to continue. If you do not consent, you may close this tab now.")
    st.stop()
# =================== END CONSENT GATE ====================

st.set_page_config(page_title="Your Preferences", layout="centered")
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

st.title("Your Preferences")

client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", "YOUR_API_KEY_HERE"))


RESULTS_FILE = "results.csv"
BASE_COLUMNS = [
    "timestamp","prolific_pid","session_id","topic","user_prompt",
    "response_a","response_b","response_c","user_choice","comments"
]

# Create the file with header under a lock
if not os.path.exists(RESULTS_FILE):
        pd.DataFrame(columns=BASE_COLUMNS).to_csv(RESULTS_FILE, index=False)


# --- Prolific identifiers ---
query_params = st.query_params
prolific_pid = query_params.get("PROLIFIC_PID", ["anon"])[0]
session_id = query_params.get("SESSION_ID", ["none"])[0]
st.markdown(f"**Participant ID:** `{prolific_pid}`")

# -------------------------
# --- Topics --------------
# -------------------------
TOPICS = [
    # prompts = [
    # --- Relationships & Emotional Management ---
    {
        "text": "Think of a time when you decided not to confront someone because you didn’t want to make things awkward.",
        "example": "*My roommate kept leaving dishes in the sink. I didn’t say anything because I didn’t want to seem petty, but it just kept bothering me.*",
        "domain": "Relationships & Emotional Management"
    },
    {
        "text": "Think of a time when you avoided telling someone bad news because you didn’t want to upset them.",
        "example": "*I didn’t tell my partner I got laid off until a week later because I wanted to handle it myself first.*",
        "domain": "Relationships & Emotional Management"
    },
    {
        "text": "Think of a time when you said something nice to comfort someone, even though it wasn’t completely true.",
        "example": "*I told my coworker their idea was great even though it had big flaws — I didn’t want to discourage them.*",
        "domain": "Relationships & Emotional Management"
    },
    {
        "text": "Think of a time when you avoided apologizing because you felt your reasons made sense.",
        "example": "*I didn’t apologize to a friend for being late because traffic really was bad, so it wasn't my fault.*",
        "domain": "Relationships & Emotional Management"
    },

    # --- Self-Regulation & Avoidance ---
    {
        "text": "Think of a time when you chose short-term comfort over long-term benefit, and it felt justified at the time.",
        "example": "*I bought takeout every night that week because I felt too tired to cook, even though I knew it would blow my budget.*",
        "domain": "Self-Regulation & Avoidance"
    },
    {
        "text": "Think of a time when you decided to handle a problem on your own instead of asking for help.",
        "example": "*I didn’t ask my manager for guidance because I wanted to prove I could handle it — but it ended up taking much longer.*",
        "domain": "Self-Regulation & Avoidance"
    },
    {
        "text": "Think of a time when you justified being distant or unresponsive because you needed space.",
        "example": "*I stopped replying to a friend’s texts for a while because I needed to recharge — I didn’t want to say something I’d regret while overwhelmed.*",
        "domain": "Self-Regulation & Avoidance"
    },
    {
        "text": "Think of a time when you procrastinated because you believed waiting would help you do it better.",
        "example": "*I put off starting an essay because I knew I’d write better once I had a clearer idea of my argument.*",
        "domain": "Self-Regulation & Avoidance"
    },

    # --- Caregiving, Support, & Enabling ---
    {
        "text": "Think of a time when you did something out of kindness, even though it might have enabled someone’s bad habits.",
        "example": "*I kept giving my friend rides everywhere because I didn’t want them to feel stranded, but they stopped trying to get their own transportation.*",
        "domain": "Caregiving, Support, & Enabling"
    },
    {
        "text": "Think of a time when you tried to support someone or act on their behalf, but it led to tension or disagreement.",
        "example": "*I told my friend’s crush that she liked him because she was too shy. She got angry and said I overstepped.*",
        "domain": "Caregiving, Support, & Enabling"
    },
    {
        "text": "Think of a time when you kept helping someone because you didn’t want them to struggle, even though they could’ve managed on their own.",
        "example": "*I edited my partner’s job applications every time because I wanted to help, but they said it made them feel incompetent.*",
        "domain": "Caregiving, Support, & Enabling"
    },
    {
        "text": "Think of a time when you avoided setting a boundary because you didn’t want to seem selfish.",
        "example": "*I kept lending money to a friend even though it stressed me out — I didn’t want them to think I didn’t care.*",
        "domain": "Caregiving, Support, & Enabling"
    },

    # --- Work, Competence, & Control ---
    {
        "text": "Think of a time when you held onto control because you believed others wouldn’t handle it as well.",
        "example": "*I redid a group project section myself because I thought my teammates wouldn’t get it right, but it just made me resentful.*",
        "domain": "Work, Competence, & Control"
    },
    {
        "text": "Think of a time when you took on extra work because you thought it was easier than explaining it to someone else.",
        "example": "*I rewrote a report my coworker drafted instead of giving feedback because I didn’t want to waste time correcting them.*",
        "domain": "Work, Competence, & Control"
    },
    {
        "text": "Think of a time when you declined help because you didn’t want to seem less capable.",
        "example": "*I declined a friend’s offer to help me move because I wanted to handle it myself and not inconvenience anyone, but it took me a lot longer.*",
        "domain": "Work, Competence, & Control"
    },
    {
        "text": "Think of a time when you stuck to doing something your own way because you believed your method was best.",
        "example": "*I refused to use my team’s new workflow because I thought my old system was more efficient.*",
        "domain": "Work, Competence, & Control"
    },

    # --- Social & Relational Boundaries ---
    {
        "text": "Think of a time when your relationship with a friend, ex, or crush unintentionally led to mixed feelings or misunderstandings with a romantic partner.",
        "example": "*My partner was upset because I went to my ex’s art show without telling them. I thought it wasn’t a big deal, but they felt I was being secretive.*",
        "domain": "Social & Relational Boundaries"
    },
    {
        "text": "Think of a time when you made a choice about who to include, and someone felt hurt or left out in a way you didn’t intend.",
        "example": "*I didn’t invite my sibling to my party because I wanted to keep it small. They were hurt, and I didn’t expect them to be.*",
        "domain": "Social & Relational Boundaries"
    },
    {
        "text": "Think of a time when sharing something personal or positive — like a new relationship or success — unintentionally made someone else uncomfortable or upset.",
        "example": "*A friend told me that talking a lot about my new relationship was hard to hear during her breakup. They were hurt, and I didn’t expect them to be.*",
        "domain": "Social & Relational Boundaries"
    },
    {
        "text": "Think of a time when you stayed close to someone out of loyalty, even though it made another person in your life uncomfortable.",
        "example": "*I kept hanging out with a friend my partner didn’t like because I didn’t want to abandon them — it caused ongoing tension between us.*",
        "domain": "Social & Relational Boundaries"
    }
]

# -------------------------
# --- Session state -------
# -------------------------
if "topic_idx" not in st.session_state:
    st.session_state.topic_idx = random.randint(0, len(TOPICS) - 1)
if "generated" not in st.session_state:
    st.session_state.generated = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# deterministic topic refresh (no flags)
def refresh_topic():
    prev = st.session_state.topic_idx
    choices = [i for i in range(len(TOPICS)) if i != prev]
    st.session_state.topic_idx = random.choice(choices)

# -------------------------
# --- Show topic ----------
# -------------------------
st.markdown("### Your topic to discuss with the AI model:")



topic = TOPICS[st.session_state.topic_idx]
st.write(topic["text"])
st.markdown(f"*Example: {topic['example']}*")
if not st.session_state.generated:
    st.button(
        "Discuss a different topic - this one isn’t relevant to me.",
        on_click=refresh_topic,
        key="refresh_btn",
    )
# -------------------------
# --- User prompt ---------
# -------------------------
user_prompt = st.text_area(
    "### Describe an experience related to this topic to an AI model (please do NOT use any writing assistance):",
    key="user_prompt_text"
)

# -------------------------
# --- Generate & Judge ----
# -------------------------
if (not st.session_state.generated
    and st.button("Generate Responses", key="gen_btn")
    and user_prompt.strip()):
    with st.spinner("Generating responses..."):
        for attempt in range(4):
            try:
                gen = client.responses.create(
                    model="gpt-4.1",
                    input=(
                        "Generate **three distinct responses** representing different perspectives."
                        " Each response must begin with ### to separate them."
                        " Do not include labels or commentary.\n\nPrompt:\n"
                        f"{user_prompt}"
                    ),
                    temperature=0.9,
                )
                text = gen.output_text
                parts = [p.strip() for p in text.split("###") if p.strip()] 
                break
            except Exception as e:
                time.sleep((2**attempt) + random.random())

    if len(parts) < 3:
        st.error("❌ Could not parse three responses correctly. Try rephrasing your prompt.")
    else:
        st.session_state.resp_a, st.session_state.resp_b, st.session_state.resp_c = parts[:3]

        st.session_state.generated = True

# -------------------------
# --- Display responses & select
# -------------------------
if st.session_state.generated and not st.session_state.submitted:
    st.subheader("Response A")
    st.write(st.session_state.resp_a)
    # st.info(f"Judge rating: {st.session_state.rating_a}")

    st.subheader("Response B")
    st.write(st.session_state.resp_b)
    # st.info(f"Judge rating: {st.session_state.rating_b}")

    st.subheader("Response C")
    st.write(st.session_state.resp_c)
    # st.info(f"Judge rating: {st.session_state.rating_c}")

    st.markdown("### Which response do you prefer?")

    # Build display text for each response
    options = {
        "A":'**Response A:** '+st.session_state["resp_a"].strip(),
        "B": '**Response B:** '+st.session_state["resp_b"].strip(),
        "C": '**Response C:** '+st.session_state["resp_c"].strip()
    }

    # Display the radio with the full response texts
    user_choice = st.radio(
        label="Select your preferred response:",
        options=list(options.keys()),
        format_func=lambda x: options[x],   # 👈 shows actual text instead of "A/B/C"
        index=None,                         # 👈 ensures no default
        key="user_choice",
    )


    # st.markdown("---")
    # user_choice = st.radio(
    #     "Which response do you prefer?",
    #     ["A", "B", "C"],
    #     horizontal=True,
    #     key="user_choice"
    # )

    # -------------------------
    # --- NEW: Comments query
    # -------------------------
    comments = st.text_area(
        "Comments:",
        placeholder="Your comments",
        key="comments_box"
    )

    # -------------------------
# --- Step 1: continue to Wellbeing + Survey page
# -------------------------
if st.button("Continue ➜"):
    if not comments.strip():
        st.error("Please add a comment before continuing.")
        st.stop()  # prevent moving on
        
    st.session_state.initial_payload = {
        "prolific_pid": prolific_pid,
        "session_id": session_id,
        "topic": topic["text"],
        "user_prompt": user_prompt,
        "response_a": st.session_state.resp_a,
        "response_b": st.session_state.resp_b,
        "response_c": st.session_state.resp_c,
        "user_choice": user_choice,                 # initial preference
        "comments": (comments or "").strip(),
    }
    st.session_state.generated = True
    st.session_state.submitted = True
    st.success("Saved. Continue to the next page.")
    st.switch_page("pages/1_Wellbeing_and_Survey.py")
        #, label="Go to next page", icon="🧭")



