"""
Page 1: Customer Onboarding
"""
import streamlit as st
import httpx
import json

import sys
sys.path.append('src/streamlit_app')
from auth import require_auth

st.set_page_config(page_title="Customer Onboarding", page_icon="👤", layout="wide")
require_auth()

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
    
    .form-container {
        background: white; border-radius: 16px; padding: 30px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    
    .success-card {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1px solid #BBF7D0; border-radius: 16px; padding: 24px;
        margin-top: 20px; display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    .success-card h3 { color: #166534; margin: 0 0 8px 0; }
    .customer-id {
        font-size: 2.5rem; font-weight: 800; color: #15803D; letter-spacing: 2px;
        background: white; padding: 10px 30px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 15px 0;
    }
    
    /* Hide default Streamlit headers */
    header[data-testid="stHeader"] { visibility: hidden; }
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

st.markdown('<div class="page-header">👤 Client Registration</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Add a new buyer or investor profile to your database.</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    with st.form("customer_form", clear_on_submit=False):
        st.markdown("<h4 style='margin-top:0;color:#334155'>Personal Information</h4>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            full_name = st.text_input("Full Name *", placeholder="e.g. Rahul Sharma")
        with col2:
            email = st.text_input("Email Address *", placeholder="e.g. rahul@example.com")
        with col3:
            phone = st.text_input("Phone Number", placeholder="e.g. +91 98765 43210")
            
        st.markdown("<hr style='margin:20px 0;border-color:#F1F5F9'>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0;color:#334155'>Investment Profile</h4>", unsafe_allow_html=True)
        
        col4, col5, col6 = st.columns(3)
        with col4:
            buyer_type = st.selectbox(
                "Client Type *", options=["buyer", "investor", "both"],
                format_func=lambda x: {"buyer": "🏡 Primary Home Buyer", "investor": "💼 Real Estate Investor", "both": "🔄 Hybrid / Both"}[x]
            )
        with col5:
            budget_min = st.number_input("Min Budget (₹) *", min_value=0, value=5000000, step=1000000, format="%d")
        with col6:
            budget_max = st.number_input("Max Budget (₹) *", min_value=0, value=25000000, step=1000000, format="%d")

        preferred_locations = st.multiselect(
            "Preferred Locales",
            options=["Whitefield", "Koramangala", "HSR Layout", "Indiranagar", "Electronic City",
                     "Sarjapur Road", "Hebbal", "Yelahanka", "Baner Pune", "Powai Mumbai",
                     "Gurgaon Sector 54", "Noida Sector 137", "Hitech City Hyderabad"],
            default=["Whitefield", "HSR Layout"],
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Securely Register Client", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if submitted:
    if not all([full_name, email, buyer_type]):
        st.error("Please fill in all required fields (marked with *).")
    elif budget_max < budget_min:
        st.error("Maximum budget must be greater than or equal to minimum budget.")
    else:
        payload = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "buyer_type": buyer_type,
            "budget_min": float(budget_min),
            "budget_max": float(budget_max),
            "preferred_locations": preferred_locations,
        }

        with st.spinner("Saving client details..."):
            try:
                resp = httpx.post(
                    f"{CONCIERGE_URL}/agents/customer/onboard",
                    json={"payload": payload},
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()

                state = data.get("status", {}).get("state", "")
                msg = data.get("status", {}).get("message", {})
                msg_text = msg.get("parts", [{}])[0].get("text", "") if msg else ""
                artifacts = data.get("artifacts", [])

                if state == "completed":
                    customer_id = None
                    for art in artifacts:
                        for part in art.get("parts", []):
                            try:
                                art_data = json.loads(part.get("text", "{}"))
                                customer_id = art_data.get("customer_id")
                            except Exception:
                                pass

                    if customer_id:
                        st.markdown(f"""
                        <div class="success-card">
                            <h3>✅ Client Successfully Registered</h3>
                            <div style="color:#166534">The client profile has been securely saved to the database.</div>
                            <div class="customer-id">{customer_id}</div>
                            <div style="color:#22C55E;font-size:0.9rem;font-weight:500">Provide this Reference ID to the client.</div>
                        </div>
                        """, unsafe_allow_html=True)


                else:
                    st.error(f"❌ Registration failed: {msg_text or data.get('status', {}).get('error', 'Unknown error')}")

            except httpx.ConnectError:
                st.error("🔌 Cannot connect to the system. Ensure background services are active.")
            except Exception as e:
                st.error(f"Unexpected system error: {e}")
