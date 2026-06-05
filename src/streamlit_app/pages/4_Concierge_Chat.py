"""
Page 4: Concierge Chat — Natural Language Interface
"""
import streamlit as st
import httpx
import json
import time

st.set_page_config(page_title="Concierge Chat", page_icon="🎯", layout="wide")

CONCIERGE_URL = "http://localhost:8000"

st.markdown("## 🎯 Concierge Chat")
st.markdown("Talk to the AI concierge in natural language. It will route your request to the right agent.")
st.divider()

# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your real estate AI concierge. I can help you with:\n\n"
                "- 👤 **Register as a buyer/investor** — just tell me your details\n"
                "- 🏘️ **List a property** — share the property information\n"
                "- 📊 **Market insights** — ask about trends, ROI, or risks\n\n"
                "How can I assist you today?"
            ),
            "intent": None,
            "artifacts": [],
        }
    ]

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{int(time.time())}"

# ── Sidebar: Quick Prompts ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💬 Quick Prompts")
    st.caption("Click to populate the input:")

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

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

    st.markdown("### 🔗 Session")
    st.caption(f"ID: `{st.session_state.session_id}`")

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
                st.caption(f"**Routed to:** {badge}")

            # Show artifacts
            if artifacts:
                with st.expander("📦 Response Data"):
                    for art in artifacts:
                        art_name = art.get("name", "artifact")
                        parts = art.get("parts", [])
                        for part in parts:
                            try:
                                data = json.loads(part.get("text", "{}"))
                                st.json(data)
                            except Exception:
                                st.text(part.get("text", ""))

# ── Input ──────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("_prefill", "")
user_input = st.chat_input("Type your message...", key="chat_input")

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
    with st.chat_message("assistant", avatar="🎯"):
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
                    st.caption(f"**Routed to:** {intent_labels.get(intent, intent)}")

                if artifacts:
                    with st.expander("📦 Response Data"):
                        for art in artifacts:
                            parts = art.get("parts", [])
                            for part in parts:
                                try:
                                    d = json.loads(part.get("text", "{}"))
                                    st.json(d)
                                except Exception:
                                    st.text(part.get("text", ""))

                if error:
                    st.warning(f"⚠️ Note: {error}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "intent": intent,
                    "artifacts": artifacts,
                })

            except httpx.ConnectError:
                err_msg = "🔌 I can't reach the backend. Please make sure all agents are running."
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
