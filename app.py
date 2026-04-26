import streamlit as st

st.title("LoveGuard - Test")
st.write("App is running successfully.")

try:
    import os, sys, json, pandas as pd
    from datetime import datetime
    sys.path.append(os.path.dirname(__file__))
    from app_orchestrator import LoveGuardOrchestrator
    st.success("All imports OK - full app loading...")
    exec(open("app_full.py").read())
except Exception as e:
    import traceback
    st.error(f"Startup error: {e}")
    st.code(traceback.format_exc())
