import streamlit as st
import navigator as nav
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

ACK_PHRASES = {
    "thanks",
    "thank you",
    "cheers",
    "perfect thanks",
    "perfect, thanks",
    "ok thanks",
    "okay thanks",
    "thanks a lot",
    "thank you very much",
    "many thanks",
    "much appreciated",
    "appreciate it",
    "appreciate you",
    "great, thanks",
    "great thanks",
    "awesome, thanks",
    "awesome thanks",
    "all good, thanks",
    "all good thanks",
    "legend",
    "all good",
    "got it",
    "nice one",
    "sweet",
    "sweet as",
    "no worries",
    "no problem",
    "perfect",
}

ENTRANCE_ONLY = {
    "tory",
    "tory channel",
    "koamaru",
    "cape koamaru",
    "eastern",
    "eastern entrance",
    "northern",
    "north entrance",
}

def normalize_text(text):
    return " ".join(text.strip().lower().split())

def is_acknowledgement(text):
    normalized = normalize_text(text)
    if normalized in ACK_PHRASES:
        return True
    if normalized.startswith("thanks") or normalized.startswith("thank you"):
        return True
    if len(normalized.split()) <= 3 and normalized in ACK_PHRASES:
        return True
    return False

def is_entrance_only(text):
    normalized = normalize_text(text)
    return normalized in ENTRANCE_ONLY

def is_entrance_clarification_message(text):
    lowered = text.lower()
    return "clarification needed" in lowered and "entrance" in lowered

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
if "pending_crossing_query" not in st.session_state:
    st.session_state.pending_crossing_query = None
if "last_assistant_asked_entrance" not in st.session_state:
    st.session_state.last_assistant_asked_entrance = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("e.g., Is it safe to head to the Sounds this Saturday?"):
    if is_acknowledgement(prompt):
        if st.session_state.last_assistant_asked_entrance:
            ack_reply = (
                "All good. When you are ready, just tell me which entrance: "
                "Tory Channel or Cape Koamaru."
            )
        else:
            ack_reply = "You are welcome. If you want another check, just tell me the route or location."
            st.session_state.pending_crossing_query = None
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": ack_reply})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            st.markdown(ack_reply)
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # This prevents the 'NoneType' error by ensuring the executor is created here
        executor = nav.get_updated_executor()
        
        st_callback = StreamlitCallbackHandler(st.container())
        
        prompt_for_agent = prompt
        if st.session_state.last_assistant_asked_entrance and is_entrance_only(prompt):
            if st.session_state.pending_crossing_query:
                prompt_for_agent = (
                    f"{st.session_state.pending_crossing_query} Entrance: {prompt}. "
                    "Please confirm you are using the same timeframe from the original request."
                )
            else:
                prompt_for_agent = (
                    f"Cross to the Marlborough Sounds. Entrance: {prompt}. "
                    "Please confirm you are using the same timeframe from the original request."
                )
            st.session_state.last_assistant_asked_entrance = False
            st.session_state.pending_crossing_query = None

        # Pass the vessel context directly into the question
        full_context = f"Vessel: {boat_size}m. VHF: {vhf}. PFDs: {pfd}. Question: {prompt_for_agent}"
        
        try:
            # ReAct agents MUST be invoked with a dictionary containing 'input'
            response = executor.invoke(
                {"input": full_context},
                {"callbacks": [st_callback]}
            )
            
            final_answer = response["output"]
            st.markdown(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})

            st.session_state.last_assistant_asked_entrance = is_entrance_clarification_message(final_answer)
            if st.session_state.last_assistant_asked_entrance:
                st.session_state.pending_crossing_query = prompt
            else:
                st.session_state.pending_crossing_query = None
            
        except Exception as e:
            st.error(f"Sorry, I ran into a technical hitch: {str(e)}")