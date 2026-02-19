import streamlit as st
import navigator as nav
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.set_page_config(page_title="Cook Strait Navigator", page_icon="⚓", layout="wide")

# --- SIDEBAR (Restored Layout) ---
with st.sidebar:
    st.title("🚢 Vessel Profile")
    st.info("Settings here influence the Agent's 'Go/No-Go' logic.")
    
    boat_size = st.slider("Boat Length (m)", 4.0, 12.0, 12.0, step=0.5)
    vhf = st.checkbox("VHF Radio Working", value=True)
    pfd = st.checkbox("Lifejackets for all", value=True)
    
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("⚓ Cook Strait Navigator")
st.markdown(f"**Current Vessel:** {boat_size}m | **Safety Status:** {'✅ Ready' if vhf and pfd else '⚠️ Check Equipment'}")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ready for the crossing. Where are we heading?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("e.g., Is it safe to head to the Sounds this Saturday?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # This prevents the 'NoneType' error by ensuring the executor is created here
        executor = nav.get_updated_executor()
        
        st_callback = StreamlitCallbackHandler(st.container())
        
        # Pass the vessel context directly into the question
        full_context = f"Vessel: {boat_size}m. VHF: {vhf}. PFDs: {pfd}. Question: {prompt}"
        
        try:
            # ReAct agents MUST be invoked with a dictionary containing 'input'
            response = executor.invoke(
                {"input": full_context},
                {"callbacks": [st_callback]}
            )
            
            final_answer = response["output"]
            st.markdown(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
            
        except Exception as e:
            st.error(f"Sorry, I ran into a technical hitch: {str(e)}")