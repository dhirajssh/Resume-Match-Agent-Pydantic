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
  st.session_state["display"] = []
  state = GraphState()
  state.generator_messages = []
  state.orchestrator_messages = []
  state.summarizer_messages = []
  state.count = 0
  state.feedback_messages = []
  st.session_state.graph_state = state

# Callback functions described here
def chat_input_callback():
  st.session_state["display"].append(
    {"role": "user", "content": st.session_state["user_input"]}
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
        st.session_state.graph_state.count = 0
        result = graph.run_sync(start_node=OrchestratorAgent(), state=st.session_state.graph_state)
        # print(result.output)
        # formatted_string = f"""
        # #### 🎯 Orchestrator Decision
        # **Route:** `{result.output.agent}`\n

        # **Link:** {result.output.link}\n
        # **Message:** {result.output.message}\n
        # """
        # st.session_state["display"].append(
        #   {"role": "assistant", "content": formatted_string}
        # )
        # st.session_state["messages"].append(
        #   ModelResponse(
        #     parts=[
        #       TextPart(content=formatted_string)
        #     ]
        #   )
        # )
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
  for msg in st.session_state["display"]:
    if msg["role"] == "assistant":
      with st.chat_message(msg["role"]):
        with st.status("✅ Summary complete", expanded=False, state="complete"):
          st.markdown(msg["content"])
    else:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


st.chat_input("Paste a job URL", key="user_input", on_submit=chat_input_callback)