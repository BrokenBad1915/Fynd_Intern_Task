import streamlit as st
import json
import os
import re
import pandas as pd
from datetime import datetime
import google.generativeai as genai

# --- CONFIGURATION ---
# Replace with your NEW, SECURE key
# In deployment, use: api_key = st.secrets["GEMINI_API_KEY"]
DATA_FILE = "data.json"

if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Use a placeholder for local development if running without secrets file
    st.error("API Key not found in st.secrets.")
    st.stop()  # Stop the app if the key is missing

# Configure the Gemini library
genai.configure(api_key=GOOGLE_API_KEY)

# --- HELPER FUNCTIONS ---

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(new_entry):
    data = load_data()
    data.append(new_entry)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def analyze_feedback(rating, review):
    """
    Sends the review to Gemini to generate 3 specific outputs.
    """
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )

    prompt = f"""
    You are a customer service AI analysis tool. Your job is to process customer feedback and provide structured insights.

    Input Data:
    - User Rating: {rating}/5
    - User Review: "{review}"

    Task:
    Analyze the input and provide a JSON response with exactly these keys:
    1. "user_response": A polite, empathetic, and specific reply to the user (max 2 sentences). For positive reviews, express appreciation. For negative reviews, apologize and validate their feelings.
    2. "summary": A concise, 5-10 word **root-cause summary** of the feedback (e.g., "Slow service and cold food issue").
    3. "action": A single, concrete, and measurable recommended next step for the admin (e.g., "Schedule retraining for front-of-house staff on order speed.").

    Ensure the final output is ONLY a valid JSON object.
    """
    
    try:
        response = model.generate_content(prompt)
        # Robustly handle potential markdown wrappers (```json...```)
        text = response.text.strip()
        
        # Regex to extract content that looks like JSON, ignoring markdown
        json_match = re.search(r"```json\s*(\{.*\})\s*```|(\{.*\})", text, re.DOTALL)
        
        if json_match:
            json_string = json_match.group(1) or json_match.group(2)
            return json.loads(json_string)
        else:
             # Fallback if no markdown is used (as intended by response_mime_type)
            return json.loads(text)

    except Exception as e:
        st.error(f"Error communicating with Gemini or parsing JSON: {e}")
        return {
            "user_response": "Thank you for sharing your experience. We are currently experiencing a system issue and will address your feedback shortly.",
            "summary": "System/API Error",
            "action": "Check system logs and API usage."
        }

# --- USER DASHBOARD UI ---

st.set_page_config(page_title="Feedback Portal", layout="centered")

st.title("📝 Customer Feedback")
st.write("We value your opinion! Please rate your experience.")

with st.form("feedback_form"):
    rating = st.slider("Rating", 1, 5, 5)
    review = st.text_area("Your Review", placeholder="Tell us what you liked or disliked...")
    submitted = st.form_submit_button("Submit Feedback")

    if submitted and review:
        with st.spinner("AI is analyzing your feedback..."):
            # 1. Call AI
            ai_results = analyze_feedback(rating, review)
            
            # 2. Prepare Data Entry
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rating": rating,
                "review": review,
                "ai_response": ai_results.get('user_response', ''),
                "ai_summary": ai_results.get('summary', ''),
                "ai_action": ai_results.get('action', '')
            }
            
            # 3. Save Data
            save_data(entry)
            
            # 4. Show Response
            st.success("Thank you!")
            st.info(f"**Our Response:** {entry['ai_response']}")