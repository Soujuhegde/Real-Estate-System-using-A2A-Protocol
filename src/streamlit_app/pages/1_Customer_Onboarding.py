"""
Page 1: Customer Onboarding
"""
import streamlit as st
import httpx
import json

st.set_page_config(page_title="Customer Onboarding", page_icon="👤", layout="wide")

CONCIERGE_URL = "http://localhost:8000"

st.markdown("## 👤 Customer Onboarding")
st.markdown("Register a new buyer or investor profile.")
st.divider()

with st.form("customer_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name *", placeholder="Rahul Sharma")
        email = st.text_input("Email Address *", placeholder="rahul@example.com")
        phone = st.text_input("Phone Number", placeholder="+91 98765 43210")
    with col2:
        buyer_type = st.selectbox(
            "Buyer Type *", options=["buyer", "investor", "both"],
            format_func=lambda x: {"buyer": "🏡 Buyer", "investor": "💼 Investor", "both": "🔄 Both"}[x]
        )
        budget_min = st.number_input("Minimum Budget (₹) *", min_value=0, value=5000000, step=500000, format="%d")
        budget_max = st.number_input("Maximum Budget (₹) *", min_value=0, value=15000000, step=500000, format="%d")

    preferred_locations = st.multiselect(
        "Preferred Locations",
        options=["Whitefield", "Koramangala", "HSR Layout", "Indiranagar", "Electronic City",
                 "Sarjapur Road", "Hebbal", "Yelahanka", "Baner Pune", "Powai Mumbai",
                 "Gurgaon Sector 54", "Noida Sector 137", "Hitech City Hyderabad"],
        default=["Whitefield", "HSR Layout"],
    )

    submitted = st.form_submit_button("🚀 Register Customer", type="primary", use_container_width=True)

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

        with st.spinner("Registering customer profile..."):
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
                    # Extract customer ID
                    customer_id = None
                    for art in artifacts:
                        for part in art.get("parts", []):
                            try:
                                art_data = json.loads(part.get("text", "{}"))
                                customer_id = art_data.get("customer_id")
                            except Exception:
                                pass

                    st.success("✅ Customer registered successfully!")
                    if customer_id:
                        st.markdown(f"""
                        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:16px;margin-top:12px">
                            <div style="font-size:1.1rem;font-weight:700;color:#166534">Customer ID</div>
                            <div style="font-size:1.8rem;font-weight:800;color:#15803d;letter-spacing:1px">{customer_id}</div>
                            <div style="color:#4ade80;font-size:0.85rem;margin-top:4px">Save this ID for future reference</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with st.expander("📋 Full Response"):
                        st.write(msg_text)
                        st.json(payload)
                else:
                    st.error(f"❌ Registration failed: {msg_text or data.get('status', {}).get('error', 'Unknown error')}")

            except httpx.ConnectError:
                st.error("🔌 Cannot connect to Concierge Agent. Make sure it's running on port 8000.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

st.divider()
st.caption("Fields marked with * are required. Customer data is stored securely in SQLite.")
