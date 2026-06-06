import streamlit as st

def require_auth():
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = None

    if not st.session_state["user_email"]:
        st.markdown("""
        <style>
            .login-container {
                max-width: 400px;
                margin: 100px auto;
                padding: 30px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
                text-align: center;
                border: 1px solid #E2E8F0;
            }
            header[data-testid="stHeader"] { visibility: hidden; }
            [data-testid="stSidebar"] { display: none; }
        </style>
        """, unsafe_allow_html=True)

        _, col, _ = st.columns([1, 2, 1])
        
        with col:
            st.markdown("""
            <style>
                .stTextInput > div > div > input {
                    border-radius: 8px;
                }
                .stButton > button {
                    border-radius: 8px;
                    font-weight: 600;
                }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center;'>🔐 Nexura Secure Login</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color:#64748B; font-size:0.95rem; margin-bottom:30px'>Please log in to access your personalized dashboard and Concierge.</p>", unsafe_allow_html=True)
            
            email = st.text_input("Investor Email", placeholder="investor@example.com", label_visibility="collapsed")
            
            if st.button("Access Dashboard 🚀", type="primary", use_container_width=True):
                if email.strip() and "@" in email:
                    st.session_state["user_email"] = email.strip()
                    st.rerun()
                else:
                    st.error("Please enter a valid email address.")
            st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.stop()
