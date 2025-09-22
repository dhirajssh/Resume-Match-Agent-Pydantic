import streamlit as st
from agents.orchestrator_agent import initialize_orchestrator_agent
from agents.summarizer_agent import initialize_summarizer_agent

def initialize_session_state():
  st.session_state["messages"] = []
  st.session_state.orchestrator_agent = initialize_orchestrator_agent()
  st.session_state.summarizer_agent = initialize_summarizer_agent()

# Callback functions described here
def chat_input_callback():
  st.session_state["messages"].append(
    {"role": "user", "content": st.session_state["user_input"]}
  )
  display_messages()

  with st.status("Generating Summary...", expanded=False) as status:
    try:
      result = st.session_state.orchestrator_agent.run_sync(
        user_prompt = st.session_state["user_input"],
        message_history = st.session_state["messages"],
      )
      print(result.output)
      st.session_state["messages"].append(
        {"role": "assistant", "content": result.output}
      )
      st.markdown(result.output)
      status.update(label="✅ Summary complete", state="complete")
    except Exception as e:
      error_msg = f"❌ Error: {e}"
      st.session_state["messages"].append(
          {"role": "assistant", "content": error_msg}
      )
      st.error(error_msg)
      st.session_state["messages"].append(
        {"role": "assistant", "content": error_msg}
      )
      status.update(label="❌ Failed to generate summary", state="error")


if "messages" not in st.session_state:
  initialize_session_state()

def display_messages():
  for msg in st.session_state["messages"]:
    if msg["role"] == "assistant":
      with st.chat_message(msg["role"]):
        with st.status("✅ Summary complete", expanded=False, state="complete"):
          st.markdown(msg["content"])
    else:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


st.chat_input("Paste a job URL", key="user_input", on_submit=chat_input_callback)