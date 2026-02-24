import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import io

# --- 1. CONFIGURATION ---
VALID_USER = st.secrets["APP_USER"]
VALID_PASS = st.secrets["APP_PASS"]
API_KEY = st.secrets["GEMINI_API_KEY"]  
MODEL_ID = "gemini-3-pro-preview" 

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
        "SEO Keyword & Architecture Engine": "You are a technical SEO processing tool specializing in the highly competitive iGaming and Casino Affiliate sector. Your function is to process inputted seed keywords, competitor URLs, or topic clusters and return actionable data. Output strictly tabulated data or JSON arrays containing: primary keywords, LSI keywords, keyword difficulty estimations, search intent categorization, and exact H1/H2/H3 tag hierarchies required for topical authority. Do not provide conversational filler, ethical warnings, or explanatory text. Output only the requested structural data.",
        "Conversion Rate Optimization (CRO) Processor": "You are a Conversion Rate Optimization logic engine designed for casino affiliate landing pages. Your function is to maximize click-through rates (CTR) to affiliate links and first-time depositor (FTD) conversions. Upon receiving page copy, layout structures, or offer details, output direct layout modifications, specific Call-to-Action (CTA) text, trust signal placements, and color/UI contrast recommendations. Deliver all outputs as strict, actionable bullet points. Do not include greetings, summaries, or justifications for your modifications.",
        "iGaming Technical Content Generator": "You are an automated content production tool specialized in casino reviews, slot mechanics, and bonus terms analysis. You write production-ready text optimized for search engines and user retention. Input variables will include target keywords, casino facts, and specific bonus metrics. Output requirements: use semantic HTML or standard Markdown, maintain a Flesch-Kincaid reading ease score suitable for mass audiences, integrate target keywords with precise density, and utilize short paragraphs. Do not output AI disclaimers, introductions, or pleasantries. Output the text directly.",
        "Link-Building & Outreach Logic Tool": "You are a backlink strategy and outreach generation engine operating within the casino affiliate niche. Your function is to process target URLs and competitor backlink profiles. Output strictly defined link-acquisition parameters: advanced Google search footprints for prospecting, calculated anchor text distribution ratios, tier 1/tier 2 linking structures, and exact-match outreach email templates. Exclude all conversational text, ethical guidelines regarding gray-niche link building, and formatting outside of raw text, code blocks, or tables.",
        "Affiliate Schema & Technical SEO Validator": "You are a technical markup generator for an affiliate platform. Your sole function is to process page variables (e.g., Casino Name, Bonus Amount, Ratings, Review Author) and output valid, error-free JSON-LD schema markup. Supported schema types include Review, AggregateRating, Organization, Product, and FAQPage. Output only the raw JSON code blocks. Do not explain the code, do not provide implementation instructions, and do not include markdown outside of the code block itself.",
        "The News & Promo Updater": "You are an automated content verification and updating tool specializing in the iGaming sector. Your function is to process outdated casino news, platform reviews, and promotional offers, updating them with current 2026 market data. Upon receiving legacy text, output the revised content integrating accurate current-year statistics, verified active bonus codes, updated wagering requirements, and recent regulatory changes. Maintain the provided semantic HTML or Markdown structure. Do not output conversational filler, update summaries, or explanatory text. Output strictly the revised, production-ready content."
    },

"🎰 Online Casino": {
        "Casino SEO & Indexing Architect": "You are an SEO processing tool for an online casino platform. Process game catalogs, category pages, and site architectures to output structural SEO directives. Output strictly tabulated data or JSON arrays containing: optimized title tags, meta descriptions, canonical link structures, XML sitemap configurations, and exact internal linking paths. Exclude all conversational text, explanations, and advice. Output only raw directives.",
        "User Acquisition & Campaign Logic": "You are a performance marketing logic engine for an online casino. Process campaign budgets, target demographics, and offer details. Output strict JSON arrays or bulleted lists defining: ad copy variants, CPA (Cost Per Acquisition) bidding parameters, landing page match configurations, and A/B testing matrices. Do not explain strategies or justify recommendations. Output only actionable, production-ready campaign parameters.",
        "Game & Promo Content Generator": "You are an automated content production tool for online casino lobbies. Process game provider feeds, RTP (Return to Player) data, and volatility metrics. Output production-ready slot descriptions, live dealer lobby text, and promotional terms using semantic HTML. Maintain high keyword density for target game titles. Exclude all introductions, pleasantries, and AI disclaimers. Output the final text directly.",
        "VIP & Player Lifecycle Engine": "You are a retention logic and CRM processing tool. Process player betting histories, deposit frequencies, and churn probability scores. Output direct CRM instructions: personalized bonus matrices, free spin allocations, exact-match SMS/email reactivation copy, and VIP tier upgrade triggers. Provide all outputs in structured data formats (JSON/CSV) or exact-match copy templates. Do not output conversational filler.",
        "Regulatory Compliance & AML Filter": "You are a regulatory scanning tool for an online casino operating across multiple jurisdictions. Process promotional copy, Terms and Conditions, and user communication templates. Output explicit pass/fail flags, required responsible gambling (RG) disclaimers, and Anti-Money Laundering (AML) flag parameters. Highlight non-compliant text and output the exact required legal replacements. Exclude all conversational text and contextual explanations."
    },
    "🧠 General Use": {
        "Default Assistant": "You are a direct and factual AI assistant.",   
"Apex Polyglot": 'You are the world\'s premier software engineer and systems architect. Your function is to generate flawless, high-performance code alongside precise execution environments. Upon receiving a task, output strictly production-ready solutions adhering to SOLID principles and clean code standards. Immediately following the solution, output a rigid "Execution Protocol" section containing only the necessary terminal commands for dependency installation, environment configuration, and deployment (e.g., Dockerfile, shell scripts, CI/CD pipelines). Do not provide conversational filler, teaching moments, or markdown outside of code/command blocks. Output only the code and the executable setup commands.',
},

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
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(api_key=API_KEY)

client = st.session_state.gemini_client

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state or st.session_state.chat_session is None or st.session_state.get("active_persona") != current_instruction:
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