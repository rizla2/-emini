import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION & SECURITY ---
# Fetch credentials securely from Streamlit Secrets
VALID_USER = st.secrets["APP_USER"]
VALID_PASS = st.secrets["APP_PASS"]
API_KEY = st.secrets["GEMINI_API_KEY"]  
MODEL_NAME = "gemini-3-pro-preview"

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

# --- 3. MULTI-BUSINESS STRUCTURE ---
# Here is where you define every business and their specific AI employees
BUSINESS_CONTEXTS = {
    "🎰 Casino Affiliate Site": {
        "The Math Geek (Strategy)": "You are a probability expert writing for a casino portal. Focus on RTP, variance, and math. No fluff.",
        "The Compliance Auditor": "You are an iGaming compliance auditor. Focus strictly on 2026 licensing, data protection, and terms.",
        "The Showdown Critic": "You are a ruthless casino critic comparing two brands. Focus on payout speeds and bonus terms.", # <--- THIS COMMA IS REQUIRED
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
    
    # Step 1: Choose the Business
    selected_business = st.selectbox("1. Select Business", list(BUSINESS_CONTEXTS.keys()))
    
    # Step 2: Choose the Persona (Dynamically updates based on Business)
    personas_for_business = BUSINESS_CONTEXTS[selected_business]
    selected_persona_name = st.selectbox("2. Select AI Persona", list(personas_for_business.keys()))
    
    # Get the actual prompt
    current_instruction = personas_for_business[selected_persona_name]
    
    st.divider()
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()
        
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# --- 5. GEMINI API SETUP ---
genai.configure(api_key=API_KEY)

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

# Maximize correctness config
generation_config = {
    "temperature": 0.1  # Near-zero temperature forces factual, deterministic outputs
}

# Initialize the Pro model
model = genai.GenerativeModel(
    model_name="gemini-3-pro-preview",
    system_instruction=current_instruction,
    safety_settings=safety_settings,
    generation_config=generation_config,
    tools=[
        genai.protos.Tool(
            google_search=genai.protos.Tool.GoogleSearch()
        )
    ]
)
# --- 6. CHAT INTERFACE & MEMORY ---
st.title(f"🏢 {selected_business}")
st.subheader(f"Active Persona: {selected_persona_name}")

# 1. INITIALIZE ALL STATE VARIABLES AT THE START
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_persona" not in st.session_state:
    st.session_state.current_persona = current_instruction

# 2. HANDLE PERSONA SWITCHING
# If the user changes the persona in the sidebar, clear the chat and reset the session
if st.session_state.current_persona != current_instruction:
    st.session_state.messages = []
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.current_persona = current_instruction

# 3. INITIALIZE THE CHAT SESSION IF IT DOESN'T EXIST
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# 4. DISPLAY MESSAGE HISTORY
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. USER INPUT LOGIC
if prompt := st.chat_input("How can I help with BettingBuddyReviews today?"):
    
    # Save and display user prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate Assistant Response
    with st.chat_message("assistant"):
        with st.status("🧠 Gemini 3.1 Pro is reasoning...", expanded=True) as status:
            try:
                # Use the session that we guaranteed exists above
                response = st.session_state.chat_session.send_message(prompt, stream=True)
                
                placeholder = st.empty()
                full_response = ""
                
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                
                placeholder.markdown(full_response)
                status.update(label="✅ Content Ready", state="complete", expanded=False)
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                status.update(label="❌ API Error", state="error")

                st.error(f"Error: {str(e)}")

