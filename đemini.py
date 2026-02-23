import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import io

# --- 1. CONFIGURATION ---
VALID_USER = st.secrets["APP_USER"]
VALID_PASS = st.secrets["APP_PASS"]
API_KEY = st.secrets["GEMINI_API_KEY"]  
MODEL_ID = "gemini-3.1-pro-preview" 

st.set_page_config(page_title="AI Business Hub", page_icon="🏢", layout="wide")

# --- 2. AUTHENTICATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Central AI Hub Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username == VALID_USER and password == VALID_PASS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- 3. BUSINESS CONTEXTS ---
BUSINESS_CONTEXTS = {
    "🎰 Casino Affiliate Site": {
        "The Math Geek (Strategy)": "You are a probability expert. Focus on RTP, variance, and math.",
        "The Compliance Auditor": "You are an iGaming compliance auditor. Focus on 2026 licensing.",
        "The Showdown Critic": "You are a ruthless casino critic comparing two brands.",
        "The SEO Content Writer": "You write comprehensive content optimized for 2026 search intent.",
        "The On-Page SEO Optimizer": "Generate meta titles, descriptions, and JSON-LD schema.",
        "The News & Promo Updater": "Rewrite casino news/reviews with latest 2026 data."
    },
    "🧠 General Use": {
        "Default Assistant": "You are a direct and factual AI assistant."
    },
}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🏢 Command Center")
    selected_business = st.selectbox("1. Business", list(BUSINESS_CONTEXTS.keys()))
    personas = BUSINESS_CONTEXTS[selected_business]
    selected_persona_name = st.selectbox("2. Persona", list(personas.keys()))
    current_instruction = personas[selected_persona_name]
    
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# --- 5. HELPERS ---
def copy_to_clipboard(text):
    js = f"<script>navigator.clipboard.writeText({repr(text)});</script>"
    st.components.v1.html(js, height=0)
    st.toast("Copied!", icon="📋")

def get_excel_data(text):
    output = io.BytesIO()
    try:
        if "|" in text and "---" in text:
            clean_lines = [l.strip() for l in text.split('\n') if "|" in l]
            df = pd.read_csv(io.StringIO('\n'.join(clean_lines)), sep="|", skipinitialspace=True).dropna(axis=1, how='all')
            df.columns = [c.strip() for c in df.columns]
        else:
            df = pd.DataFrame({"Content": [text]})
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
    except:
        pd.DataFrame({"Content": [text]}).to_excel(output, index=False)
    return output.getvalue()

# --- 6. GEMINI SETUP ---
client = genai.Client(api_key=API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_persona" not in st.session_state or st.session_state.active_persona != current_instruction:
    st.session_state.active_persona = current_instruction
    st.session_state.messages = []
    
    st.session_state.chat_session = client.chats.create(
        model=MODEL_ID,
        config=types.GenerateContentConfig(
            system_instruction=current_instruction,
            tools=[{"google_search": {}}]
        )
    )

# --- 7. CHAT UI ---
st.title(f"🏢 {selected_business}")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            c1, c2, c3 = st.columns(3)
            c1.button("📋 Copy", key=f"cp_{i}", on_click=copy_to_clipboard, args=(msg["content"],))
            c2.download_button("📄 TXT", msg["content"], f"file_{i}.txt", key=f"tx_{i}")
            c3.download_button("📊 XLS", get_excel_data(msg["content"]), f"data_{i}.xlsx", key=f"xl_{i}")

if prompt := st.chat_input("How can I help today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧠 Processing...") as status:
            try:
                response = st.session_state.chat_session.send_message(prompt)
                full_text = response.text
                st.markdown(full_text)
                
                c1, c2, c3 = st.columns(3)
                curr_idx = len(st.session_state.messages)
                c1.button("📋 Copy", key=f"cp_now_{curr_idx}", on_click=copy_to_clipboard, args=(full_text,))
                c2.download_button("📄 TXT", full_text, f"report_{curr_idx}.txt", key=f"tx_now_{curr_idx}")
                c3.download_button("📊 XLS", get_excel_data(full_text), f"data_{curr_idx}.xlsx", key=f"xl_now_{curr_idx}")

                st.session_state.messages.append({"role": "assistant", "content": full_text})
                status.update(label="✅ Ready", state="complete")
            except Exception as e:
                st.error(f"Error: {e}")