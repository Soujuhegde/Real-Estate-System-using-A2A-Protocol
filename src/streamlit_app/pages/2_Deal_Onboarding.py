"""
Page 2: Deal (Property) Onboarding
"""
import streamlit as st
import httpx
import json

st.set_page_config(page_title="Property Onboarding", page_icon="🏘️", layout="wide")

CONCIERGE_URL = "http://localhost:8000"

st.markdown("## 🏘️ Property Onboarding")
st.markdown("List a new property. Market intelligence will be generated automatically.")
st.divider()

PROPERTY_TYPES = ["apartment", "villa", "plot", "commercial", "office",
                  "warehouse", "studio", "penthouse", "row_house", "duplex"]

AMENITIES_OPTIONS = ["Swimming Pool", "Gym", "Clubhouse", "Security", "Power Backup",
                     "Parking", "Lift", "Garden", "Rooftop Terrace", "EV Charging",
                     "Co-working Space", "Concierge", "Spa", "Children's Play Area"]

with st.form("deal_form", clear_on_submit=False):
    st.markdown("### 📋 Property Details")
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Property Title *", placeholder="3BHK Luxury Apartment in Whitefield")
        location = st.text_input("Location *", placeholder="Whitefield, Bengaluru, Karnataka")
        property_type = st.selectbox("Property Type *", options=PROPERTY_TYPES)
        price = st.number_input("Asking Price (₹) *", min_value=100000, value=8500000, step=100000, format="%d")

    with col2:
        area_sqft = st.number_input("Area (sq.ft)", min_value=0.0, value=1450.0, step=50.0, format="%.0f")
        bedrooms = st.number_input("Bedrooms", min_value=0, max_value=20, value=3)
        bathrooms = st.number_input("Bathrooms", min_value=0, max_value=20, value=2)

    st.markdown("### 🏠 Amenities")
    amenities = st.multiselect(
        "Select Available Amenities",
        options=AMENITIES_OPTIONS,
        default=["Parking", "Security", "Power Backup"],
    )

    st.markdown("### 👤 Owner Details")
    col3, col4 = st.columns(2)
    with col3:
        owner_name = st.text_input("Owner Name", placeholder="Priya Mehta")
    with col4:
        owner_contact = st.text_input("Owner Contact", placeholder="+91 91234 56789")

    submitted = st.form_submit_button("🚀 List Property", type="primary", use_container_width=True)

if submitted:
    if not all([title, location, property_type, price]):
        st.error("Please fill in all required fields (marked with *).")
    elif price <= 0:
        st.error("Price must be a positive number.")
    else:
        payload = {
            "title": title,
            "location": location,
            "property_type": property_type,
            "price": float(price),
            "area_sqft": float(area_sqft) if area_sqft else None,
            "bedrooms": int(bedrooms) if bedrooms else None,
            "bathrooms": int(bathrooms) if bathrooms else None,
            "amenities": amenities,
            "owner_name": owner_name,
            "owner_contact": owner_contact,
        }

        with st.spinner("Listing property and triggering market analysis..."):
            try:
                resp = httpx.post(
                    f"{CONCIERGE_URL}/agents/deal/onboard",
                    json={"payload": payload},
                    timeout=20.0,
                )
                resp.raise_for_status()
                data = resp.json()

                state = data.get("status", {}).get("state", "")
                msg = data.get("status", {}).get("message", {})
                msg_text = msg.get("parts", [{}])[0].get("text", "") if msg else ""
                artifacts = data.get("artifacts", [])

                if state == "completed":
                    property_id = None
                    for art in artifacts:
                        for part in art.get("parts", []):
                            try:
                                art_data = json.loads(part.get("text", "{}"))
                                property_id = art_data.get("property_id")
                            except Exception:
                                pass

                    st.success("✅ Property listed successfully!")
                    if property_id:
                        st.markdown(f"""
                        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:16px;margin:12px 0">
                            <div style="font-size:1.1rem;font-weight:700;color:#1e40af">Property ID</div>
                            <div style="font-size:1.8rem;font-weight:800;color:#1d4ed8;letter-spacing:1px">{property_id}</div>
                            <div style="color:#60a5fa;font-size:0.85rem;margin-top:4px">Market intelligence is being generated in the background</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.info("🔄 The **Marketing Intelligence Agent** has been automatically triggered to analyze this property. Check the Market Intelligence page in a few seconds.")

                    with st.expander("📋 Submission Details"):
                        st.write(msg_text)
                        st.json(payload)
                else:
                    st.error(f"❌ Listing failed: {msg_text or data.get('status', {}).get('error', 'Unknown error')}")

            except httpx.ConnectError:
                st.error("🔌 Cannot connect to Concierge Agent. Make sure it's running on port 8000.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

st.divider()
st.caption("* Required fields. After submission, the Marketing Agent will automatically generate insights and store them in the RAG pipeline.")
