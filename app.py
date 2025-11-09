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

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], pool_pre_ping=True)
from datetime import datetime
import uuid
from sqlalchemy import text

def _s(val):
    # stringify with empty string for None
    return "" if val is None else str(val)

def insert_result(row):
    # Minimal validation — make comments mandatory if that's desired
    required_keys = ["prolific_pid", "session_id", "topic", "user_prompt",
                     "response_a", "response_b", "response_c",
                     "user_choice", "comments"]
    missing = [k for k in required_keys if k not in row or row[k] in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    eng = get_engine()
    with eng.begin() as conn:
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
              comments TEXT,
              wellbeing_choice TEXT,
              comments_wellbeing TEXT,
              ai_freq TEXT,
              aias_life TEXT,
              aias_work TEXT,
              aias_future TEXT,
              aias_humanity TEXT,
              aias_attention TEXT,
              tipi_reserved TEXT,
              tipi_trusting TEXT,
              tipi_lazy TEXT,
              tipi_relaxed TEXT,
              tipi_few_artistic TEXT,
              tipi_outgoing TEXT,
              tipi_fault_finding TEXT,
              tipi_thorough TEXT,
              tipi_nervous TEXT,
              tipi_imagination TEXT
            );
        """))

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

            pid=_s(row.get("prolific_pid")),
            sid=_s(row.get("session_id")),
            topic=_s(row.get("topic")),
            up=_s(row.get("user_prompt")),

            ra=_s(row.get("response_a")),
            rb=_s(row.get("response_b")),
            rc=_s(row.get("response_c")),
            choice=_s(row.get("user_choice")),
            comments=_s(row.get("comments")),

            wellbeing_choice=_s(row.get("wellbeing_choice")),
            comments_wellbeing=_s(row.get("comments_wellbeing")),

            ai_freq=_s(row.get("ai_freq")),
            aias_life=_s(row.get("aias_life")),
            aias_work=_s(row.get("aias_work")),
            aias_future=_s(row.get("aias_future")),
            aias_humanity=_s(row.get("aias_humanity")),
            aias_attention=_s(row.get("aias_attention")),

            tipi_reserved=_s(row.get("tipi_reserved")),
            tipi_trusting=_s(row.get("tipi_trusting")),
            tipi_lazy=_s(row.get("tipi_lazy")),
            tipi_relaxed=_s(row.get("tipi_relaxed")),
            tipi_few_artistic=_s(row.get("tipi_few_artistic")),
            tipi_outgoing=_s(row.get("tipi_outgoing")),
            tipi_fault_finding=_s(row.get("tipi_fault_finding")),
            tipi_thorough=_s(row.get("tipi_thorough")),
            tipi_nervous=_s(row.get("tipi_nervous")),
            tipi_imagination=_s(row.get("tipi_imagination")),
        ))




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
prolific_pid = query_params.get("PROLIFIC_PID", ["anon"])
session_id = query_params.get("SESSION_ID", ["none"])
st.markdown(f"**Participant ID:** `{prolific_pid}`")
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
        "Try a different topic – this one isn’t relevant to me.",
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
    and st.button("Get AI Response", key="gen_btn")
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

    # -------------------------
    # --- NEW: Comments query
    # -------------------------
    comments = st.text_area(
        "Comments:",
        placeholder="Your comments",
        key="comments_box"
    )

    st.markdown("---")
    st.markdown("### Now, which response is most beneficial to your <u>long-term wellbeing</u>?", unsafe_allow_html=True)

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
            key="comments_box_wellbeing"
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


    if st.button("Submit"):
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
            "prolific_pid": prolific_pid,
            "session_id": session_id,
            "topic": topic["text"],
            "user_prompt": user_prompt,
            "response_a": st.session_state.resp_a,
            "response_b": st.session_state.resp_b,
            "response_c": st.session_state.resp_c,
            # "rating_a": st.session_state.rating_a,
            # "rating_b": st.session_state.rating_b,
            # "rating_c": st.session_state.rating_c,
            "user_choice": user_choice,
            "comments": (comments or "").strip(),
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


        st.session_state.submitted = True

# -------------------------
# --- Thank-you / redirect
# -------------------------
if st.session_state.submitted:
    st.success("✅ Response logged successfully! Redirecting you to Prolific...")

    completion_code = "C1I7QVTN"  # Replace with your real Prolific completion code
    redirect_url = f"https://app.prolific.com/submissions/complete?cc={completion_code}"

    st.markdown(f"[Click here to return to Prolific immediately]({redirect_url})")
    components.html(f"""
        <script>
            setTimeout(function() {{
                window.location.href = "{redirect_url}";
            }}, 2000);
        </script>
    """, height=0, width=0)