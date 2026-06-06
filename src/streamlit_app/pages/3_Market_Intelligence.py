"""
Page 3: Market Intelligence — RAG Query & Insight Generation
"""
import streamlit as st
import httpx
import json
import sqlite3
import pandas as pd
import plotly.express as px
import sys
import os

# Add src directory to sys.path so we can import from shared and auth
sys.path.append('src')
sys.path.append('src/streamlit_app')

from shared import config
from auth import require_auth

st.set_page_config(page_title="Market Intelligence", page_icon="📊", layout="wide")
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
    
    .insight-card {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04); border: 1px solid #E2E8F0;
        margin-bottom: 16px; transition: transform 0.2s ease;
    }
    .insight-card:hover { transform: translateX(5px); border-color: #CBD5E1; }
    
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

st.markdown('<div class="page-header">📊 Market Insights</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Search through our market data or generate new insights for a property.</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Search Insights", "⚡ Generate Insights", "📈 Market Analytics"])

# ── Tab 1: Search ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0;color:#334155'>Search Market Data</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B;font-size:0.95rem'>Ask any question — we will find the most relevant market insights for you.</p>", unsafe_allow_html=True)

        with st.form("rag_query_form", clear_on_submit=False):
            query = st.text_area(
                "Your Question",
                placeholder="e.g. What are the rental yield prospects for apartments in Whitefield?",
                height=100,
            )
            property_id_filter = st.text_input(
                "Filter by Property ID (optional)",
                placeholder="e.g. PROP-XXXXXXXX",
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍 Search Knowledge Base", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted and query:
        payload: dict = {"query": query}
        if property_id_filter.strip():
            payload["property_id"] = property_id_filter.strip()

        with st.spinner("Searching market data..."):
            try:
                headers = {"X-Internal-Token": config.INTERNAL_API_TOKEN}
                resp = httpx.post(
                    f"{CONCIERGE_URL}/agents/marketing/insights",
                    json={"payload": payload},
                    headers=headers,
                    timeout=20.0,
                )
                resp.raise_for_status()
                data = resp.json()

                state = data.get("status", {}).get("state", "")
                msg_parts = data.get("status", {}).get("message", {}).get("parts", [])
                msg_text = msg_parts[0].get("text", "") if msg_parts else ""
                artifacts = data.get("artifacts", [])

                if state == "completed":
                    results = []
                    artifacts = data.get("artifacts") or []
                    for art in artifacts:
                        parts = art.get("parts") or []
                        for part in parts:
                            try:
                                parsed = json.loads(part.get("text", "[]"))
                                if isinstance(parsed, list):
                                    results = parsed
                                elif isinstance(parsed, dict):
                                    results = [parsed]
                            except Exception:
                                pass

                    if results:
                        st.markdown(f"<div style='margin-bottom:15px;color:#10B981;font-weight:600'>✅ Found {len(results)} relevant insights</div>", unsafe_allow_html=True)
                        for r in results:
                            itype = r.get("insight_type", "insight")
                            content = r.get("content", "")
                            score = r.get("score", 0)
                            pid = r.get("property_id", "")

                            type_config = {
                                "market_trend": ("📈", "#DBEAFE", "#1E40AF"),
                                "risk_signal": ("⚠️", "#FEF3C7", "#92400E"),
                                "opportunity": ("💡", "#DCFCE7", "#166534"),
                            }
                            icon, bg, color = type_config.get(itype, ("📌", "#F1F5F9", "#334155"))

                            st.markdown(f"""
                            <div class="insight-card" style="border-left: 4px solid {color}">
                                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                                    <div>
                                        <span style="background:{bg};color:{color};padding:4px 12px;
                                                     border-radius:20px;font-size:0.75rem;font-weight:700;letter-spacing:0.5px">
                                            {icon} {itype.replace('_', ' ').upper()}
                                        </span>
                                        <span style="color:#64748B;font-size:0.85rem;margin-left:12px;font-family:monospace">
                                            {pid}
                                        </span>
                                    </div>
                                    <span style="color:#94A3B8;font-size:0.75rem;font-weight:600">
                                        Relevance: {score:.2f}
                                    </span>
                                </div>
                                <div style="margin-top:16px;color:#334155;font-size:1rem;line-height:1.6">
                                    {content}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info(msg_text or "No insights found for your query.")
                else:
                    st.error(f"Query failed: {msg_text}")

            except httpx.ConnectError:
                st.error("🔌 Cannot connect to Concierge Agent.")
            except Exception as e:
                st.error(f"System Error: {e}")

# ── Tab 2: Generate Insights ──────────────────────────────────────────────────
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0;color:#334155'>Manually Trigger Analysis</h4>", unsafe_allow_html=True)
        
        with st.form("generate_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                property_id = st.text_input("Property ID *", placeholder="PROP-XXXXXXXX")
                location = st.text_input("Location *", placeholder="e.g. Whitefield, Bengaluru")
            with col2:
                prop_type = st.selectbox("Property Type", ["apartment", "villa", "plot", "commercial", "studio"])
                price = st.number_input("Price (₹)", min_value=0, value=8500000, step=100000, format="%d")

            st.markdown("<br>", unsafe_allow_html=True)
            gen_submitted = st.form_submit_button("⚡ Synthesize Insights", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if gen_submitted:
        if not property_id or not location:
            st.error("Property ID and Location are required.")
        else:
            payload = {
                "property_id": property_id.strip(),
                "location": location,
                "property_type": prop_type,
                "price": float(price),
            }

            with st.spinner("Analyzing market data..."):
                try:
                    headers = {"X-Internal-Token": config.INTERNAL_API_TOKEN}
                    resp = httpx.post(
                        f"{CONCIERGE_URL}/agents/marketing/insights",
                        json={"payload": payload},
                        headers=headers,
                        timeout=30.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    state = data.get("status", {}).get("state", "")
                    msg_parts = data.get("status", {}).get("message", {}).get("parts", [])
                    msg_text = msg_parts[0].get("text", "") if msg_parts else ""

                    if state == "completed":
                        st.success("✅ Insights generated and saved successfully!")

                        artifacts = data.get("artifacts") or []
                        insights = []
                        for art in artifacts:
                            parts = art.get("parts") or []
                            for part in parts:
                                try:
                                    parsed = json.loads(part.get("text", "[]"))
                                    if isinstance(parsed, list):
                                        insights = parsed
                                    elif isinstance(parsed, dict):
                                        insights = [parsed]
                                except Exception:
                                    pass

                        if insights:
                            for category, icon in [("market_trend", "📈"), ("risk_signal", "⚠️"), ("opportunity", "💡")]:
                                category_items = [i for i in insights if i.get("type") == category]
                                if category_items:
                                    st.markdown(f"<h5 style='color:#0F172A;margin-top:20px'>{icon} {category.replace('_', ' ').title()}</h5>", unsafe_allow_html=True)
                                    for item in category_items:
                                        st.markdown(f"<div style='color:#334155;background:white;padding:12px;border-radius:8px;border:1px solid #E2E8F0;margin-bottom:8px'>• {item['content']}</div>", unsafe_allow_html=True)
                        else:
                            st.write(msg_text)
                    else:
                        st.warning(msg_text or "Already processed or failed.")

                except httpx.ConnectError:
                    st.error("🔌 Cannot connect to the system. Ensure background services are active.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── Tab 3: Market Analytics ───────────────────────────────────────────────────
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0;color:#334155'>Global Market Overview</h4>", unsafe_allow_html=True)
        
        try:
            conn = sqlite3.connect(config.DB_PATH)
            df = pd.read_sql_query("SELECT property_id, title, location, property_type, price, area_sqft, bedrooms FROM properties", conn)
            conn.close()
            
            if df.empty:
                st.info("No property data available yet. Please onboard some properties first.")
            else:
                colA, colB = st.columns(2)
                
                with colA:
                    fig1 = px.scatter(df, x="area_sqft", y="price", color="property_type", hover_data=["title", "location"], title="Price vs. Area (sq.ft)")
                    fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig1, use_container_width=True)
                    
                with colB:
                    loc_counts = df.groupby("location").size().reset_index(name="count")
                    fig2 = px.bar(loc_counts, x="location", y="count", color="location", title="Properties by Location")
                    fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)
                    
                st.markdown("<h5 style='color:#334155; margin-top: 20px;'>Raw Market Data</h5>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
                
        except Exception as e:
            st.error(f"Failed to load market analytics: {e}")
            
        st.markdown('</div>', unsafe_allow_html=True)
