import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import io

# --- 1. CONFIGURATION & SECURITY ---
VALID_USER = st.secrets["APP_USER"]
VALID_PASS = st.secrets["APP_PASS"]
API_KEY = st.secrets["GEMINI_API_KEY"]  
MODEL_ID = "gemini-3.0-pro" 

st.set_page_config(page_title="AI Business Hub", page_icon="🏢", layout="wide")

# --- 2. AUTHENTICATION GATE ---
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

# --- 3. BUSINESS CONTEXTS (EXACTLY AS YOU HAD THEM) ---
BUSINESS_CONTEXTS = {
    "🎰 Casino Affiliate Site": {
        "The Math Geek (Strategy)": "You are a probability expert writing for a casino portal. Focus on RTP, variance, and math. No fluff.",
        "The Compliance Auditor": "You are an iGaming compliance auditor. Focus strictly on 2026 licensing, data protection, and terms.",
        "The Showdown Critic": "You are a ruthless casino critic comparing two brands. Focus on payout speeds and bonus terms.",
        "The SEO Content Writer": "You are a senior SEO content writer for an iGaming affiliate network. Write comprehensive, engaging, and highly readable content optimized for 2026 search intent.",
        "The On-Page SEO Optimizer": "You are a technical On-Page SEO specialist. Your only job is to generate highly clickable meta titles, compelling meta descriptions, optimized H1/H2/H3 header outlines, and valid JSON-LD schema markup.",
        "The News & Promo Updater": "You are a fast-paced iGaming news journalist. Your job is to rewrite existing casino reviews or news posts to include the latest 2026 data."
    },
    "🛒 E-Commerce Store (Example)": {
        "Product Description Writer": "You write high-converting, SEO-optimized product descriptions. Highlight benefits over features.",
        "Customer Support Bot": "You are a polite, empathetic customer service rep resolving shipping and refund queries."
    },
    "🔨 Local Service Business (Example)": {
        "Local SEO Blogger": "You write blog posts targeting local neighborhood keywords for home services.",
        "Ad Copywriter": "You write aggressive, high-converting Google Ads copy with strong Calls to Action."
    },
    "🧠 General Use": {
        "Default Assistant": "You are a highly capable, general-purpose AI assistant. Be direct and factual."
    },
}

# --- 4. SIDEBAR & SESSION CONTROL ---
with st.sidebar:
    st.header("🏢 Command Center")
    selected_business = st.selectbox("1. Select Business", list(BUSINESS_CONTEXTS.keys()))
    personas = BUSINESS_CONTEXTS[selected_business]
    selected_persona_name = st.selectbox("2. Select AI Persona", list(personas.keys()))
    current_instruction = personas[selected_persona_name]
    
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# --- 5. HELPER FUNCTIONS ---
def copy_to_clipboard(text):
    js = f"<script>navigator.clipboard.writeText({repr(text)});</script>"
    st.components.v1.html(js, height=0)
    st.toast("Copied to clipboard!", icon="📋")

def get_excel_data(text):
    output = io.BytesIO()
    try:
        if "|" in text and "---" in text:
            clean_text = "\n".join([l.strip() for l in text.split("\n")])
            df = pd.read_markdown(io.StringIO(clean_text))
        else:
            df = pd.DataFrame({"Full AI Report": [text]})
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
    except:
        df = pd.DataFrame({"Content": [text]})
        df.to_excel(output, index=False)
    return output.getvalue()

# --- 6. GEMINI CLIENT SETUP ---
client = genai.Client(api_key=API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle Persona switching
if "active_persona_instr" not in st.session_state or st.session_state.active_persona_instr != current_instruction:
    st.session_state.active_persona_instr = current_instruction
    st.session_state.messages = []
    config = types.GenerateContentConfig(
        system_instruction=current_instruction,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=1.0
    )
    st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)

# --- 7. CHAT UI ---
st.title(f"🏢 {selected_business}")
st.caption(f"Active Persona: {selected_persona_name}")

# History Loop
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("sources"):
                with st.expander("🔍 Verified Sources"):
                    for s in msg["sources"]:
                        st.write(f"- [{s['title']}]({s['url']})")
            
            c1, c2, c3 = st.columns(3)
            c1.button("📋 Copy", key=f"cp_{i}", on_click=copy_to_clipboard, args=(msg["content"],))
            c2.download_button("📄 TXT", msg["content"], f"report_{i}.txt", key=f"tx_{i}")
            c3.download_button("📊 XLS", get_excel_data(msg["content"]), f"data_{i}.xlsx", key=f"xl_{i}")

# Input Logic
if prompt := st.chat_input(f"Message {selected_persona_name}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧠 Processing...", expanded=True) as status:
            try:
                response = st.session_state.chat_session.send_message(prompt)
                full_text = response.text
                
                sources = []
                if response.candidates[0].grounding_metadata:
                    meta = response.candidates[0].grounding_metadata
                    if meta.grounding_chunks:
                        sources = [{"title": c.web.title, "url": c.web.uri} for c in meta.grounding_chunks if c.web]
                
                st.markdown(full_text)
                if sources:
                    with st.expander("🔍 Verified Sources"):
                        for s in sources: st.write(f"- [{s['title']}]({s['url']})")
                
                status.update(label="✅ Ready", state="complete", expanded=False)

                # Current response actions
                c1, c2, c3 = st.columns(3)
                idx = len(st.session_state.messages)
                c1.button("📋 Copy", key=f"cp_now", on_click=copy_to_clipboard, args=(full_text,))
                c2.download_button("📄 TXT", full_text, "report.txt", key=f"tx_now")
                c3.download_button("📊 XLS", get_excel_data(full_text), "data.xlsx", key=f"xl_now")

                st.session_state.messages.append({"role": "assistant", "content": full_text, "sources": sources})
            except Exception as e:
                st.error(f"Error: {e}")