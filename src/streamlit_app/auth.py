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

        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 Nexura Secure Login")
        st.markdown("<p style='color:#64748B;font-size:0.9rem;margin-bottom:20px'>Please log in to access your personalized dashboard and Concierge.</p>", unsafe_allow_html=True)
        
        email = st.text_input("Investor Email", placeholder="investor@example.com", label_visibility="collapsed")
        
        if st.button("Access Dashboard 🚀", type="primary", use_container_width=True):
            if email.strip() and "@" in email:
                st.session_state["user_email"] = email.strip()
                st.rerun()
            else:
                st.error("Please enter a valid email address.")
                
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
