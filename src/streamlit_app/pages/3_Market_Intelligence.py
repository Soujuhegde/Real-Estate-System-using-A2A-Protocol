"""
Page 3: Market Intelligence — RAG Query & Insight Generation
"""
import streamlit as st
import httpx
import json

st.set_page_config(page_title="Market Intelligence", page_icon="📊", layout="wide")

CONCIERGE_URL = "http://localhost:8000"

st.markdown("## 📊 Market Intelligence")
st.markdown("Query the RAG pipeline or manually trigger analysis for a property.")
st.divider()

tab1, tab2 = st.tabs(["🔍 Query Insights (RAG)", "⚡ Generate Insights"])

# ── Tab 1: RAG Query ──────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Semantic Search Over Stored Insights")
    st.markdown("Ask any question — the system retrieves the most relevant market insights from the vector database.")

    with st.form("rag_query_form"):
        query = st.text_area(
            "Your Question",
            placeholder="What are the rental yield prospects for apartments in Whitefield?\nWhat are the risk factors for properties in Electronic City?\nWhich properties have the best ROI potential?",
            height=100,
        )
        property_id_filter = st.text_input(
            "Filter by Property ID (optional)",
            placeholder="PROP-XXXXXXXX",
        )
        submitted = st.form_submit_button("🔍 Search Insights", type="primary", use_container_width=True)

    if submitted and query:
        payload: dict = {"query": query}
        if property_id_filter.strip():
            payload["property_id"] = property_id_filter.strip()

        with st.spinner("Searching vector database..."):
            try:
                resp = httpx.post(
                    f"{CONCIERGE_URL}/agents/marketing/insights",
                    json={"payload": payload},
                    timeout=20.0,
                )
                resp.raise_for_status()
                data = resp.json()

                state = data.get("status", {}).get("state", "")
                msg_parts = data.get("status", {}).get("message", {}).get("parts", [])
                msg_text = msg_parts[0].get("text", "") if msg_parts else ""
                artifacts = data.get("artifacts", [])

                if state == "completed":
                    # Try to parse structured results from artifacts
                    results = []
                    for art in artifacts:
                        for part in art.get("parts", []):
                            try:
                                results = json.loads(part.get("text", "[]"))
                            except Exception:
                                pass

                    if results:
                        st.success(f"Found **{len(results)}** relevant insights")
                        for r in results:
                            itype = r.get("insight_type", "insight")
                            content = r.get("content", "")
                            score = r.get("score", 0)
                            pid = r.get("property_id", "")

                            type_config = {
                                "market_trend": ("📈", "#dbeafe", "#1e40af"),
                                "risk_signal": ("⚠️", "#fef3c7", "#92400e"),
                                "opportunity": ("💡", "#dcfce7", "#166534"),
                            }
                            icon, bg, color = type_config.get(itype, ("📌", "#f1f5f9", "#334155"))

                            st.markdown(f"""
                            <div style="background:{bg};border-radius:10px;padding:14px 16px;margin-bottom:10px">
                                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                                    <div>
                                        <span style="background:{color};color:white;padding:2px 10px;
                                                     border-radius:20px;font-size:0.75rem;font-weight:600">
                                            {icon} {itype.replace('_', ' ').title()}
                                        </span>
                                        <span style="color:#94a3b8;font-size:0.75rem;margin-left:10px">
                                            {pid}
                                        </span>
                                    </div>
                                    <span style="color:#94a3b8;font-size:0.75rem">
                                        Score: {score:.3f}
                                    </span>
                                </div>
                                <div style="margin-top:10px;color:#1e293b;font-size:0.95rem;line-height:1.5">
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
                st.error(f"Error: {e}")

# ── Tab 2: Generate Insights ──────────────────────────────────────────────────
with tab2:
    st.markdown("### Manually Trigger Market Analysis")
    st.markdown("If automatic triggering failed, or you want to regenerate insights for a property.")

    with st.form("generate_form"):
        col1, col2 = st.columns(2)
        with col1:
            property_id = st.text_input("Property ID *", placeholder="PROP-XXXXXXXX")
            location = st.text_input("Location *", placeholder="Whitefield, Bengaluru")
        with col2:
            prop_type = st.selectbox("Property Type", ["apartment", "villa", "plot", "commercial", "studio"])
            price = st.number_input("Price (₹)", min_value=0, value=8500000, step=100000, format="%d")

        gen_submitted = st.form_submit_button("⚡ Generate Insights", type="primary", use_container_width=True)

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

            with st.spinner("Generating AI-powered market insights..."):
                try:
                    resp = httpx.post(
                        f"{CONCIERGE_URL}/agents/marketing/insights",
                        json={"payload": payload},
                        timeout=30.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    state = data.get("status", {}).get("state", "")
                    msg_parts = data.get("status", {}).get("message", {}).get("parts", [])
                    msg_text = msg_parts[0].get("text", "") if msg_parts else ""

                    if state == "completed":
                        st.success("✅ Insights generated and stored in vector database!")

                        artifacts = data.get("artifacts", [])
                        insights = []
                        for art in artifacts:
                            for part in art.get("parts", []):
                                try:
                                    insights = json.loads(part.get("text", "[]"))
                                except Exception:
                                    pass

                        if insights:
                            for category, icon in [("market_trend", "📈"), ("risk_signal", "⚠️"), ("opportunity", "💡")]:
                                category_items = [i for i in insights if i.get("type") == category]
                                if category_items:
                                    st.markdown(f"**{icon} {category.replace('_', ' ').title()}**")
                                    for item in category_items:
                                        st.markdown(f"- {item['content']}")
                        else:
                            st.write(msg_text)
                    else:
                        st.warning(msg_text or "Already processed or failed.")

                except httpx.ConnectError:
                    st.error("🔌 Cannot connect to Concierge Agent.")
                except Exception as e:
                    st.error(f"Error: {e}")
