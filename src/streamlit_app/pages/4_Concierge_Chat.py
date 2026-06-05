"""
Page 4: Concierge Chat — Natural Language Interface
"""
import streamlit as st
import httpx
import json
import time

st.set_page_config(page_title="Concierge Chat", page_icon="🎯", layout="wide")

# Inject Global CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, h6, .page-header { font-family: 'Outfit', sans-serif !important; }
    
    .page-header {
        font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 5px;
        display: flex; align-items: center; gap: 12px;
    }
    .page-sub { color: #64748B; font-size: 1.05rem; margin-bottom: 30px; font-weight: 400; }
    
    /* Hide default Streamlit headers */
    header[data-testid="stHeader"] { visibility: hidden; }

    /* Chat Customizations */
    [data-testid="stChatMessage"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #F8FAFC;
    }
    
    .intent-badge {
        background: #E0E7FF; color: #3730A3; padding: 4px 10px; border-radius: 12px;
        font-size: 0.75rem; font-weight: 600; margin-top: 10px; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

CONCIERGE_URL = "http://localhost:8000"

# ── Top Navigation ────────────────────────────────────────────────────────────
cols = st.columns(5)
with cols[0]: st.page_link("app.py", label="🏠 Home")
with cols[1]: st.page_link("pages/1_Customer_Onboarding.py", label="👤 Client Registration")
with cols[2]: st.page_link("pages/2_Deal_Onboarding.py", label="🏘️ Add Property")
with cols[3]: st.page_link("pages/3_Market_Intelligence.py", label="📊 Market Insights")
with cols[4]: st.page_link("pages/4_Concierge_Chat.py", label="💬 Smart Assistant")
st.divider()

st.markdown('<div class="page-header">💬 Smart Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Talk to our intelligent assistant in natural English. It will automatically understand what you need and help you get it done.</div>', unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Welcome to Nexura! I'm your AI concierge. I can assist you with:\n\n"
                "- 👤 **Registering clients or investors**\n"
                "- 🏘️ **Listing new properties to the portfolio**\n"
                "- 📊 **Generating market insights and ROI projections**\n\n"
                "What would you like to do today?"
            ),
            "intent": None,
            "artifacts": [],
        }
    ]

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{int(time.time())}"

# ── Sidebar: Quick Prompts ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💬 Quick Prompts", unsafe_allow_html=True)
    st.caption("Click to auto-fill the chat input:")

    prompts = {
        "👤 Register me as investor": (
            "I want to register as an investor. My name is Arjun Nair, "
            "email arjun@example.com, phone 9876543210. Budget is ₹50 lakhs to ₹1.5 crore. "
            "I'm looking in Whitefield and Sarjapur Road."
        ),
        "🏘️ List an apartment": (
            "Please list my property: 2BHK Apartment in HSR Layout, Bengaluru. "
            "Asking price ₹75 lakhs, 1100 sqft, 2 bedrooms, 2 bathrooms. "
            "Amenities: parking, gym, 24/7 security. Contact: Meena, 9123456789."
        ),
        "📊 What are the ROI insights?": "What are the ROI and rental yield insights for apartments in Whitefield?",
        "⚠️ What are market risks?": "What are the risk signals for commercial properties in Electronic City?",
        "📈 Market trends in Koramangala": "Tell me about market trends and demand for villas in Koramangala.",
    }

    for label, prompt_text in prompts.items():
        if st.button(label, use_container_width=True):
            st.session_state._prefill = prompt_text

    st.markdown("<hr style='border-color:#E2E8F0'>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

    st.markdown("### 🔗 Session Info")
    st.code(f"{st.session_state.session_id}", language="text")

# ── Chat history ──────────────────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        intent = msg.get("intent")
        artifacts = msg.get("artifacts", [])

        with st.chat_message(role, avatar="🎯" if role == "assistant" else "👤"):
            st.markdown(content)

            # Show intent badge
            if intent and role == "assistant" and intent != "unknown":
                intent_labels = {
                    "customer_onboarding": "👤 Customer Onboarding",
                    "deal_onboarding": "🏘️ Deal Onboarding",
                    "market_insights": "📊 Market Intelligence",
                }
                badge = intent_labels.get(intent, intent)
                st.markdown(f'<div class="intent-badge">Routed to: {badge}</div>', unsafe_allow_html=True)



# ── Input ──────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("_prefill", "")
user_input = st.chat_input("Type your message to the concierge...", key="chat_input")

if prefill and not user_input:
    user_input = prefill

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "intent": None,
        "artifacts": [],
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Call Concierge
    with st.chat_message("assistant", avatar="💬"):
        with st.spinner("Thinking..."):
            try:
                resp = httpx.post(
                    f"{CONCIERGE_URL}/chat",
                    json={"message": user_input, "session_id": st.session_state.session_id},
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()

                response_text = data.get("response", "I couldn't process that request.")
                intent = data.get("intent", "unknown")
                artifacts = data.get("artifacts", [])
                error = data.get("error")

                st.markdown(response_text)

                if intent and intent != "unknown":
                    intent_labels = {
                        "customer_onboarding": "👤 Customer Onboarding",
                        "deal_onboarding": "🏘️ Deal Onboarding",
                        "market_insights": "📊 Market Intelligence",
                    }
                    st.markdown(f'<div class="intent-badge">Routed to: {intent_labels.get(intent, intent)}</div>', unsafe_allow_html=True)



                if error:
                    st.warning(f"⚠️ Notice: {error}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "intent": intent,
                    "artifacts": artifacts,
                })

            except httpx.ConnectError:
                err_msg = "🔌 I can't reach the system. Please make sure the background services are running."
                st.error(err_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_msg,
                    "intent": "error",
                    "artifacts": [],
                })
            except Exception as e:
                err_msg = f"Something went wrong: {e}"
                st.error(err_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_msg,
                    "intent": "error",
                    "artifacts": [],
                })
