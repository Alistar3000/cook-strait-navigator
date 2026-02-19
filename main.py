import streamlit as st
from navigator import agent # Import the agent we built

st.set_page_config(page_title="Cook Strait Navigator", page_icon="⚓")

# --- SIDEBAR: BOAT SPECIFICATIONS ---
with st.sidebar:
    st.header("🚢 Boat Profile")
    boat_size = st.slider("Boat Length (meters)", 4.0, 15.0, 6.0)
    engine_hp = st.number_input("Engine Power (HP)", 50, 600, 115)
    fuel_capacity = st.number_input("Fuel Capacity (L)", 20, 500, 100)
    
    st.divider()
    st.header("📋 Safety Checklist")
    vhf = st.checkbox("VHF Radio Working")
    epirb = st.checkbox("PLB/EPIRB Onboard")
    lifejackets = st.checkbox("Lifejackets for all")
    trip_report = st.checkbox("Coastguard Trip Report Logged")

# --- MAIN INTERFACE ---
st.title("Cook Strait Boating Assistant")
st.markdown(f"**Current Vessel:** {boat_size}m / {engine_hp}HP")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Plan a trip (e.g., 'Mana to Ship Cove tomorrow')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with AI
    with st.chat_message("assistant"):
        # Inject boat specs into the prompt context automatically
        full_context = (
            f"USER BOAT SPECS: {boat_size}m, {engine_hp}HP. "
            f"SAFETY STATUS: VHF={vhf}, EPIRB={epirb}. "
            f"QUERY: {prompt}"
        )
        response = agent.run(full_context)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})