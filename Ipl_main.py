import os
import time
import uuid
import json

import streamlit as st
import streamlit.components.v1 as components
import pickle
import pandas as pd
import numpy as np

# ------------------ ACTIVE USER TRACKING ------------------

USER_FILE = "active_users.json"
TIMEOUT = 120  # 2 min

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def update_active_users(session_id):
    users = load_users()
    current_time = time.time()

    users[session_id] = current_time

    users = {
        uid: t for uid, t in users.items()
        if current_time - t < TIMEOUT
    }

    save_users(users)

    return max(len(users), 1)

# session id
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

active_users = update_active_users(st.session_state.session_id)

# ------------------ SMART REFRESH (WORKING) ------------------

components.html("""
<script>
let inactivityLimit = 120000; // 2 min
let checkInterval = 60000;    // check every 1 min
let lastActivity = Date.now();

function updateActivity() {
    lastActivity = Date.now();
}

// track user actions
document.onmousemove = updateActivity;
document.onkeypress = updateActivity;
document.onclick = updateActivity;
document.onscroll = updateActivity;

// check every 1 min
setInterval(() => {
    let now = Date.now();
    let inactiveTime = now - lastActivity;

    if (inactiveTime >= inactivityLimit) {
        // show popup
        let count = 5;
        let popup = document.createElement("div");
        popup.style.position = "fixed";
        popup.style.bottom = "20px";
        popup.style.right = "20px";
        popup.style.background = "#262730";
        popup.style.color = "white";
        popup.style.padding = "12px";
        popup.style.borderRadius = "10px";
        popup.style.zIndex = "9999";
        document.body.appendChild(popup);

        let interval = setInterval(() => {
            popup.innerHTML = "⚠️ Inactive. Refreshing in " + count + " sec...";
            count--;

            if (count < 0) {
                clearInterval(interval);
                location.reload();
            }
        }, 1000);

    } else {
        // ACTIVE user → soft refresh every 1 min
        location.reload();
    }

}, checkInterval);
</script>
""", height=0)

# ------------------ UI ------------------

st.markdown(f"""
<div style="position: fixed; top: 70px; right: 20px; 
            background-color: #262730; color: white; 
            padding: 10px 15px; border-radius: 10px;
            z-index: 9999;">
    👁️ {active_users} Views
</div>
""", unsafe_allow_html=True)

# ------------------ MAIN APP ------------------

teams = ['Sunrisers Hyderabad','Mumbai Indians','Royal Challengers Bangalore',
         'Kolkata Knight Riders','Kings XI Punjab','Chennai Super Kings',
         'Rajasthan Royals','Delhi Capitals']

cities = ['Hyderabad','Bangalore','Mumbai','Indore','Kolkata','Delhi',
          'Chandigarh','Jaipur','Chennai','Cape Town','Port Elizabeth',
          'Durban','Centurion','East London','Johannesburg','Kimberley',
          'Bloemfontein','Ahmedabad','Cuttack','Nagpur','Dharamsala',
          'Visakhapatnam','Pune','Raipur','Ranchi','Abu Dhabi',
          'Sharjah','Mohali','Bengaluru']

pipe = pickle.load(open('./pipe.pkl','rb'))

st.title('IPL Win Predictor')

col1, col2 = st.columns(2)

with col1:
    batting_team = st.selectbox('Select the batting team', sorted(teams))
with col2:
    bowling_team = st.selectbox('Select the bowling team', sorted(teams))

selected_city = st.selectbox('Select host city', sorted(cities))
target = st.number_input('Target')

col3, col4, col5 = st.columns(3)

with col3:
    score = st.number_input('Score')
with col4:
    overs = st.number_input('Overs completed')
with col5:
    wickets = st.number_input('Wickets out')

if st.button('Predict Probability'):
    runs_left = target - score
    balls_left = 120 - (overs * 6)
    wickets = 10 - wickets

    crr = score / overs if overs > 0 else 0
    rrr = (runs_left * 6) / balls_left if balls_left > 0 else 0

    input_df = pd.DataFrame({
        'batting_team': [batting_team],
        'bowling_team': [bowling_team],
        'city': [selected_city],
        'runs_left': [runs_left],
        'balls_left': [balls_left],
        'wickets': [wickets],
        'total_runs_x': [target],
        'crr': [crr],
        'rrr': [rrr]
    })

    result = pipe.predict_proba(input_df)
    loss = result[0][0]
    win = result[0][1]

    st.header(batting_team + " - " + str(round(win * 100)) + "%")
    st.header(bowling_team + " - " + str(round(loss * 100)) + "%")