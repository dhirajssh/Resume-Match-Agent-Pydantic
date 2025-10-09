import streamlit as st
from agents.orchestrator_agent import initialize_orchestrator_agent
from agents.summarizer_agent import initialize_summarizer_agent
from agents.generator_agent import initialize_generator_agent
from agents.feedback_agent import initialize_feedback_agent
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
from agents.graph import graph, OrchestratorAgent, GraphState

def initialize_session_state():
  st.session_state["messages"] = []
  st.session_state.resume = ""
  st.session_state.orchestrator_agent = initialize_orchestrator_agent()
  st.session_state.summarizer_agent = initialize_summarizer_agent()
  st.session_state.generator_agent = initialize_generator_agent()
  st.session_state.feedback_agent = initialize_feedback_agent()
  st.session_state.display = []
  state = GraphState()
  state.generator_messages = []
  state.orchestrator_messages = []
  state.summarizer_messages = []
  state.count = 0
  state.feedback_messages = []
  st.session_state.graph_state = state

# Callback functions described here
def chat_input_callback():
  st.session_state.display.append(
    {"role": "user", "content": st.session_state["user_input"], "thinking": False}
  )
  st.session_state["messages"].append(
    ModelRequest(
      parts = [
        UserPromptPart(content=st.session_state["user_input"])
      ]
    )
  )
  display_messages()
  with st.chat_message("assistant"):
    with st.status("Generating Summary...", expanded=True) as status:
      try:
        with st.status("Thinking", expanded=False) as status:
          st.session_state.graph_state.count = 0
          result = graph.run_sync(start_node=OrchestratorAgent(), state=st.session_state.graph_state)
          status.update(state="complete")
        st.markdown(result.output)
        status.update(label="✅ Summary complete", state="complete")
      except Exception as e:
        with st.status("Thinking", expanded=False) as status:
          error_msg = f"❌ Error: {e}"
          st.session_state["messages"].append(
              {"role": "assistant", "content": error_msg}
          )
          st.error(error_msg)
          st.session_state["messages"].append(
            {"role": "assistant", "content": error_msg}
          )
          status.update(label="❌ Thinking", state="error")
        st.markdown(error_msg)
        status.update(label="❌ Failed to generate summary", state="error")


if "messages" not in st.session_state:
  initialize_session_state()

def display_messages():
  n = len(st.session_state.display)
  i = 0
  while i<n:
    msg = st.session_state.display[i]
    if msg["role"] != "user":
      with st.chat_message("assistant"):
        with st.status("Thinking", expanded=False):
          while msg["role"]!="F" and msg.get("iteration", 0) != 2:
            msg = st.session_state.display[i]
            if msg["role"] == "O":
              with st.status("✅ Orchestrator Decision", expanded=False, state="complete"):
                st.markdown(msg["content"])
            elif msg["role"]=="S":
              with st.status("✅ Job Summary", expanded=False, state="complete"):
                st.markdown(msg["content"])
            elif msg["role"]=="G":
              with st.status(f"✅ Answer Generated {msg["iteration"]}", expanded=False, state="complete"):
                st.markdown(msg["content"])
            elif msg["role"]=="F":
              with st.status(f"✅ Feedback Generated {msg["iteration"]}", expanded=False, state="complete"):
                st.markdown(msg["content"])
            i+=1
          if msg["role"]=="F":
            with st.status(f"✅ Feedback Generated {msg["iteration"]}", expanded=False, state="complete"):
              st.markdown(msg["content"])
        temp = i-1
        generator_msg = st.session_state.display[temp]
        st.markdown(generator_msg["content"])
        
    else:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
    i+=1

with st.sidebar:
  st.markdown("Resume here")
st.chat_input("Paste a job URL", key="user_input", on_submit=chat_input_callback)