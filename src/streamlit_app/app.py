"""
Real Estate System — Streamlit Frontend
Main App: Home
"""
import streamlit as st
import httpx
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
import sys
sys.path.append('src/streamlit_app')
from auth import require_auth

st.set_page_config(
    page_title="Nexura Home",
    page_icon="🏠",
    layout="wide",
)
require_auth()

# ── Config ────────────────────────────────────────────────────────────────────
CONCIERGE_URL = "http://localhost:8000"

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, h6, .hero-title { font-family: 'Outfit', sans-serif !important; }
    
    header[data-testid="stHeader"] { visibility: hidden; }
    footer { visibility: hidden; }

    /* Top Navigation Bar Styling */
    .nav-container {
        display: flex; gap: 15px; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 1px solid #E2E8F0;
    }
    .nav-item {
        text-decoration: none; color: #475569; font-weight: 500; padding: 8px 16px; border-radius: 8px; transition: 0.2s;
    }
    .nav-item:hover { background: #F1F5F9; color: #4F46E5; }
    .nav-item.active { background: #EEF2FF; color: #4F46E5; font-weight: 600; }

    /* Custom CSS Classes */
    .hero-container {
        background: linear-gradient(135deg, #4F46E5 0%, #0D9488 100%);
        padding: 60px 40px; border-radius: 24px; color: white; text-align: center;
        margin-bottom: 40px; box-shadow: 0 10px 30px -10px rgba(79, 70, 229, 0.4);
    }
    .hero-title { font-size: 3.5rem; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.5px; }
    .hero-sub { font-size: 1.2rem; opacity: 0.9; font-weight: 300; max-width: 600px; margin: 0 auto; }

    .section-title { font-size: 1.8rem; font-weight: 600; color: #1E293B; margin-bottom: 24px; }

    .glass-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px;
        transition: all 0.3s ease; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); height: 100%;
    }
    .glass-card:hover { transform: translateY(-5px); box-shadow: 0 15px 20px -5px rgba(0,0,0,0.08); border-color: #CBD5E1; }
    
    .agent-icon {
        font-size: 2.5rem; margin-bottom: 16px; background: #F1F5F9;
        width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 14px;
    }
    .agent-name { font-size: 1.1rem; font-weight: 600; color: #0F172A; margin-bottom: 4px; }

    .badge-online { background: #DCFCE7; color: #166534; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-block;}
    .badge-offline { background: #FEE2E2; color: #991B1B; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-block;}

</style>
""", unsafe_allow_html=True)


# ── Top Navigation ────────────────────────────────────────────────────────────
cols = st.columns(5)
with cols[0]: st.page_link("app.py", label="🏠 Home")
with cols[1]: st.page_link("pages/1_Customer_Onboarding.py", label="👤 Client Registration")
with cols[2]: st.page_link("pages/2_Deal_Onboarding.py", label="🏘️ Add Property")
with cols[3]: st.page_link("pages/3_Market_Intelligence.py", label="📊 Market Insights")
with cols[4]: st.page_link("pages/4_Concierge_Chat.py", label="💬 Smart Assistant")
st.divider()

# ── Helpers ───────────────────────────────────────────────────────────────────
def check_agent_health(url: str) -> bool:
    try:
        from shared import config
        headers = {"X-Internal-Token": config.INTERNAL_API_TOKEN}
        r = httpx.get(f"{url}/health", headers=headers, timeout=3.0)
        return r.status_code == 200
    except:
        return False

AGENTS = {
    "Smart Assistant (Main)": ("http://localhost:8000", "💬"),
    "Client Manager": ("http://localhost:8001", "👤"),
    "Property Manager": ("http://localhost:8002", "🏘️"),
    "Market Analyst": ("http://localhost:8003", "📊"),
}

# ── Layout ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Welcome to Nexura</div>
    <div class="hero-sub">Your intelligent real estate companion. Easily manage clients, list properties, and get market insights all in one place.</div>
</div>
""", unsafe_allow_html=True)

# ── System Health ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">System Status</div>', unsafe_allow_html=True)

cols = st.columns(4)
all_healthy = True

for i, (name, (url, icon)) in enumerate(AGENTS.items()):
    healthy = check_agent_health(url)
    if not healthy: all_healthy = False
    
    status_class = "badge-online" if healthy else "badge-offline"
    status_text = "● ONLINE" if healthy else "● OFFLINE"
    
    with cols[i]:
        st.markdown(f"""
        <div class="glass-card">
            <div class="agent-icon">{icon}</div>
            <div class="agent-name">{name}</div>
            <div class="{status_class}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
if all_healthy:
    st.success("✅ All systems are online and running smoothly.")
else:
    st.error("⚠️ Some systems are currently offline. Please ensure the background services are running.")

st.markdown("<br><br>", unsafe_allow_html=True)

# ── Getting Started ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">What would you like to do?</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="glass-card" style="padding:20px">
        <h4 style="margin-top:0;color:#0F172A">👤 Add a New Client</h4>
        <p style="color:#475569;font-size:0.95rem;margin-bottom:0">Click on <b>Client Registration</b> at the top to add a new buyer or investor to your database.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="glass-card" style="padding:20px">
        <h4 style="margin-top:0;color:#0F172A">🏘️ Add a Property</h4>
        <p style="color:#475569;font-size:0.95rem;margin-bottom:0">Click on <b>Add Property</b> to list a new home or commercial space. We'll automatically analyze its market value!</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="glass-card" style="padding:20px">
        <h4 style="margin-top:0;color:#0F172A">💬 Ask a Question</h4>
        <p style="color:#475569;font-size:0.95rem;margin-bottom:0">Head over to the <b>Smart Assistant</b> to type out what you need in plain English.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:0.85rem;padding:20px 0;border-top:1px solid #E2E8F0'>"
    "Nexura Real Estate Platform · 2026"
    "</div>",
    unsafe_allow_html=True,
)
