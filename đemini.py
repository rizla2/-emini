import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

# --- 1. CONFIGURATION & SECURITY ---
VALID_USER = st.secrets["APP_USER"]
VALID_PASS = st.secrets["APP_PASS"]
API_KEY = st.secrets["GEMINI_API_KEY"]  
MODEL_NAME = "gemini-1.5-pro" # Grounding works best with Pro

st.set_page_config(page_title="AI Business Hub", page_icon="🏢", layout="wide")

# --- 2. AUTHENTICATION GATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Central AI Hub Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            if username == VALID_USER and password == VALID_PASS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- 3. MULTI-BUSINESS STRUCTURE (Original Personas Restored) ---
BUSINESS_CONTEXTS = {
    "🎰 Casino Affiliate Site": {
        "The Math Geek (Strategy)": "You are a probability expert writing for a casino portal. Focus on RTP, variance, and math. No fluff.",
        "The Compliance Auditor": "You are an iGaming compliance auditor. Focus strictly on 2026 licensing, data protection, and terms.",
        "The Showdown Critic": "You are a ruthless casino critic comparing two brands. Focus on payout speeds and bonus terms.",
        "The SEO Content Writer": "You are a senior SEO content writer for an iGaming affiliate network. Write comprehensive, engaging, and highly readable content optimized for 2026 search intent. Naturally weave in LSI keywords, maintain a conversational yet authoritative tone, and prioritize user retention and readability above all else. Avoid generic AI filler words.",
        "The On-Page SEO Optimizer": "You are a technical On-Page SEO specialist. Your only job is to generate highly clickable meta titles, compelling meta descriptions, optimized H1/H2/H3 header outlines, and valid JSON-LD schema markup (Review, FAQ, Breadcrumb) based on the provided topic or text. Do not write full articles.",
        "The News & Promo Updater": "You are a fast-paced iGaming news journalist. Your job is to rewrite existing casino reviews or news posts to include the latest 2026 data, new bonus codes, and recent game launches. Keep the tone urgent, exciting, and conversion-focused."
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

# --- 4. SIDEBAR & SETTINGS ---
with st.sidebar:
    st.header("🏢 Command Center")
    selected_business = st.selectbox("1. Select Business", list(BUSINESS_CONTEXTS.keys()))
    personas_for_business = BUSINESS_CONTEXTS[selected_business]
    selected_persona_name = st.selectbox("2. Select AI Persona", list(personas_for_business.keys()))
    current_instruction = personas_for_business[selected_persona_name]
    
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
        # Check for Markdown table
        if "|" in text and "---" in text:
            # Simple line clean-up to help the parser
            clean_lines = [l.strip() for l in text.split('\n') if "|" in l]
            df = pd.read_csv(io.StringIO('\n'.join(clean_lines)), sep="|").dropna(axis=1, how='all')
            df.columns = [c.strip() for c in df.columns]
        else:
            df = pd.DataFrame({"Full Content": [text]})
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
    except:
        pd.DataFrame({"Content": [text]}).to_excel(output, index=False)
    return output.getvalue()

# --- 6. GEMINI API SETUP ---
genai.configure(api_key=API_KEY)

# Tool for grounding
tools = [{"google_search_retrieval": {}}]

# --- 7. CHAT INTERFACE & MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_persona" not in st.session_state or st.session_state.current_persona != current_instruction:
    st.session_state.messages = []
    st.session_state.current_persona = current_instruction
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=current_instruction,
        tools=tools
    )
    st.session_state.chat_session = model.start_chat(history=[])

# Display History
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            c1, c2, c3 = st.columns(3)
            c1.button("📋 Copy", key=f"cp_{i}", on_click=copy_to_clipboard, args=(message["content"],))
            c2.download_button("📄 TXT", message["content"], f"file_{i}.txt", key=f"tx_{i}")
            c3.download_button("📊 XLS", get_excel_data(message["content"]), f"data_{i}.xlsx", key=f"xl_{i}")

# Input Logic
if prompt := st.chat_input("How can I help today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧠 Searching & Reasoning...") as status:
            try:
                response = st.session_state.chat_session.send_message(prompt)
                full_text = response.text
                st.markdown(full_text)
                
                # Manual Action Row for current message
                c1, c2, c3 = st.columns(3)
                c1.button("📋 Copy", key="cp_now", on_click=copy_to_clipboard, args=(full_text,))
                c2.download_button("📄 TXT", full_text, "report.txt", key="tx_now")
                c3.download_button("📊 XLS", get_excel_data(full_text), "data.xlsx", key="xl_now")

                st.session_state.messages.append({"role": "assistant", "content": full_text})
                status.update(label="✅ Ready", state="complete")
            except Exception as e:
                st.error(f"Error: {str(e)}")