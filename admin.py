"""
Admin dashboard to view feedback metrics
Run locally: streamlit run admin.py
"""
import streamlit as st
from feedback import get_feedback_stats, load_feedback
import pandas as pd

st.set_page_config(page_title="MustangsAI Analytics", page_icon="📊")

st.title("📊 MustangsAI Feedback Dashboard")

# Overall stats
stats = get_feedback_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Responses", stats['total'])
with col2:
    st.metric("👍 Positive", stats['positive'])
with col3:
    st.metric("👎 Negative", stats['negative'])
with col4:
    st.metric("Satisfaction Rate", f"{stats['satisfaction_rate']}%")

# Recent feedback
st.subheader("Recent Feedback")
data = load_feedback()
if data['responses']:
    df = pd.DataFrame(data['responses'])
    df = df[['timestamp', 'question', 'rating', 'comment']]
    df = df.sort_values('timestamp', ascending=False)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No feedback yet")