import requests
import streamlit as st


st.set_page_config(page_title="Fraud Risk Pipeline", layout="wide")
st.title("Fraud Risk Pipeline")

api_url = st.sidebar.text_input("API URL", "http://localhost:8000")
amount = st.number_input("Amount", min_value=0.0, value=250.0, step=10.0)
merchant = st.text_input("Merchant", "new_electronics")
country = st.text_input("Country", "US")
hour = st.slider("Hour", 0, 23, 23)

if st.button("Score transaction", type="primary"):
    payload = {
        "transaction": {
            "amount": amount,
            "merchant": merchant,
            "country": country,
            "hour": hour,
        }
    }
    response = requests.post(f"{api_url}/predict", json=payload, timeout=15)
    response.raise_for_status()
    result = response.json()
    st.metric("Fraud probability", f"{result['fraud_probability']:.1%}")
    st.write(result["decision"])
    st.write(result["analyst_summary"])
    st.dataframe(result["top_features"], use_container_width=True)
