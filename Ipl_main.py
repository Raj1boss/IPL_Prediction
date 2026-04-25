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
TIMEOUT = 120  # 2 minutes

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

    # update current user
    users[session_id] = current_time

    # remove inactive users
    users = {
        uid: t for uid, t in users.items()
        if current_time - t < TIMEOUT
    }

    save_users(users)

    return max(len(users), 1)

# unique session id
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

active_users = update_active_users(st.session_state.session_id)

# ------------------ AUTO REFRESH EVERY 2 MIN ------------------

components.html("""
<script>
setInterval(function(){
    window.location.reload();
}, 120000); // 2 minutes
</script>
""", height=0)

# ------------------ TOP RIGHT UI ------------------

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
