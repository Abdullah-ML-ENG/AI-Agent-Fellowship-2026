import streamlit as st

# Pre-defined mock users for simulation
MOCK_USERS = {
    "admin": {"password": "admin123", "role": "Admin", "name": "System Administrator"},
    "editor": {"password": "editor123", "role": "Editor", "name": "Content Editor"},
    "viewer": {"password": "viewer123", "role": "Viewer", "name": "Guest Viewer"}
}

def init_auth_session():
    """Initialize session state variables for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

def login(username, password):
    """Authenticate a user against mock users."""
    username = username.strip().lower()
    if username in MOCK_USERS and MOCK_USERS[username]["password"] == password:
        st.session_state.authenticated = True
        st.session_state.user_info = {
            "username": username,
            "role": MOCK_USERS[username]["role"],
            "name": MOCK_USERS[username]["name"]
        }
        return True
    return False

def logout():
    """Clear authentication state."""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    # Reset chat history to ensure privacy between sessions
    if "messages" in st.session_state:
        st.session_state.messages = []

def is_authenticated():
    """Check if a user is logged in."""
    init_auth_session()
    return st.session_state.authenticated

def get_current_user():
    """Get information about the logged-in user."""
    init_auth_session()
    return st.session_state.user_info

def check_permission(required_role):
    """Check if the current user has the required permission level."""
    if not is_authenticated():
        return False
    
    current_role = st.session_state.user_info["role"]
    role_hierarchy = {"Viewer": 1, "Editor": 2, "Admin": 3}
    
    return role_hierarchy.get(current_role, 0) >= role_hierarchy.get(required_role, 0)

def show_login_sidebar():
    """Render the login form in the Streamlit sidebar."""
    init_auth_session()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 User Authentication")
    
    if st.session_state.authenticated:
        user = st.session_state.user_info
        st.sidebar.success(f"Logged in as **{user['name']}**")
        st.sidebar.info(f"Role: **{user['role']}**")
        
        if st.sidebar.button("Log Out", key="logout_btn", use_container_width=True):
            logout()
            st.rerun()
    else:
        with st.sidebar.form("login_form"):
            username = st.text_input("Username", value="", placeholder="admin, editor, or viewer")
            password = st.text_input("Password", type="password", placeholder="admin123, editor123, viewer123")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                if login(username, password):
                    st.success("Successfully logged in!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        
        # Display helper credential list
        with st.sidebar.expander("🔑 Simulated Credentials"):
            st.markdown("""
            * **Admin**: `admin` / `admin123`
            * **Editor**: `editor` / `editor123`
            * **Viewer**: `viewer` / `viewer123`
            """)
