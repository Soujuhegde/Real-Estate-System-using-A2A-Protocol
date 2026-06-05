"""
Page 2: Deal (Property) Onboarding
"""
import streamlit as st
import httpx
import json

st.set_page_config(page_title="Property Onboarding", page_icon="🏘️", layout="wide")

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
    .property-id {
        font-size: 2.5rem; font-weight: 800; color: #15803D; letter-spacing: 2px;
        background: white; padding: 10px 30px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 15px 0;
    }
    
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

st.markdown('<div class="page-header">🏘️ Add Property</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">List a new property. We will automatically analyze its market value.</div>', unsafe_allow_html=True)

PROPERTY_TYPES = ["apartment", "villa", "plot", "commercial", "office",
                  "warehouse", "studio", "penthouse", "row_house", "duplex"]

AMENITIES_OPTIONS = ["Swimming Pool", "Gym", "Clubhouse", "Security", "Power Backup",
                     "Parking", "Lift", "Garden", "Rooftop Terrace", "EV Charging",
                     "Co-working Space", "Concierge", "Spa", "Children's Play Area"]

with st.container():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    with st.form("deal_form", clear_on_submit=False):
        st.markdown("<h4 style='margin-top:0;color:#334155'>Core Specifications</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Property Title *", placeholder="e.g. 3BHK Luxury Apartment in Whitefield")
            location = st.text_input("Location *", placeholder="e.g. Whitefield, Bengaluru")
            property_type = st.selectbox("Property Type *", options=PROPERTY_TYPES)
            price = st.number_input("Asking Price (₹) *", min_value=100000, value=8500000, step=100000, format="%d")

        with col2:
            area_sqft = st.number_input("Area (sq.ft)", min_value=0.0, value=1450.0, step=50.0, format="%.0f")
            bedrooms = st.number_input("Bedrooms", min_value=0, max_value=20, value=3)
            bathrooms = st.number_input("Bathrooms", min_value=0, max_value=20, value=2)

        st.markdown("<hr style='margin:20px 0;border-color:#F1F5F9'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#334155'>Premium Amenities</h4>", unsafe_allow_html=True)
        amenities = st.multiselect(
            "Select Available Amenities",
            options=AMENITIES_OPTIONS,
            default=["Parking", "Security", "Power Backup"],
        )

        st.markdown("<hr style='margin:20px 0;border-color:#F1F5F9'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#334155'>Owner Contact</h4>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            owner_name = st.text_input("Owner Name", placeholder="e.g. Priya Mehta")
        with col4:
            owner_contact = st.text_input("Owner Contact", placeholder="e.g. +91 91234 56789")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 List Property Portfolio", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

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

        with st.spinner("Saving property details..."):
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

                    if property_id:
                        st.markdown(f"""
                        <div class="success-card">
                            <h3>✅ Property Listed Successfully</h3>
                            <div style="color:#166534">The property has been added to the master portfolio.</div>
                            <div class="property-id">{property_id}</div>
                            <div style="color:#22C55E;font-size:0.9rem;font-weight:500">Market intelligence is now generating in the background.</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.info("🔄 We are automatically generating market insights for this property in the background. Check the Market Insights page shortly.")


                else:
                    st.error(f"❌ Listing failed: {msg_text or data.get('status', {}).get('error', 'Unknown error')}")

            except httpx.ConnectError:
                st.error("🔌 Cannot connect to the system. Ensure background services are active.")
            except Exception as e:
                st.error(f"Unexpected system error: {e}")
