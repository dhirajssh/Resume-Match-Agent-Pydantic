from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional
from dataclasses import dataclass
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
import streamlit as st
from pydantic_ai.messages import UserPromptPart, TextPart, ModelResponse, ModelRequest
from agents.summarizer_agent import Link
import logging

class GraphState(BaseModel):
  agent: Optional[Literal["summarizer_agent", "generator_agent"]] = Field(
    default="generator_agent",
    description="""
    Specifies which agent should handle the request.
    The orchestrator agent decides which agent gets the message.
    """,
    examples=[
      "summarizer_agent",
      "generator_agent",
    ]
  )
  link: Optional[str] = Field(default = None)
  message: Optional[str] = Field(default = None)
  count: Optional[int] = Field(default = 0)
  orchestrator_messages: list = Field(default_factory = list)
  summarizer_messages: list = Field(default_factory = list)
  generator_messages: list = Field(default_factory = list)
  feedback_messages: list = Field(default_factory=list)
  job_summary: Optional[str] = Field(default=None)

  
@dataclass
class OrchestratorAgent(BaseNode[GraphState]):

  async def run(self, ctx: GraphRunContext[GraphState]) -> SummarizerAgent | GeneratorAgent:
    ctx.state.orchestrator_messages.append(ModelRequest(
      parts=[UserPromptPart(content=f"{st.session_state["user_input"]}")]
    ))
    with st.status("Orchestrator Agent Thinking", expanded=True) as status:
      try:
        result = await st.session_state.orchestrator_agent.run(
          user_prompt = st.session_state["user_input"],
          message_history = ctx.state.orchestrator_messages
        )
        formatted_string = f"""
        #### 🎯 Orchestrator Decision
        **Route:** `{result.output.agent}`\n

        **Link:** {result.output.link}\n
        **Message:** {result.output.message}\n
        """
        ctx.state.orchestrator_messages.append(ModelResponse(
          parts=[
            TextPart(content=formatted_string)
          ]
        ))
        st.markdown(formatted_string)
        ctx.state.agent = result.output.agent
        ctx.state.link = result.output.link
        ctx.state.message = result.output.message
        status.update(label="✅ Orchestrator decision", state="complete")
        if ctx.state.agent == "summarizer_agent":
          return SummarizerAgent()
        else:
          return GeneratorAgent()
      except Exception as e:
        error_message = f"An error occurred in OrchestratorAgent: {e}"
        logging.exception(error_message)
        st.session_state.error_message = error_message
        ctx.state.orchestrator_messages.append(
          ModelResponse(parts=[TextPart(content=error_message)])
        )
        st.markdown(error_message)
        status.update(label="❌ Failed Orchestrator Agent", state="error")
        raise

    
@dataclass
class SummarizerAgent(BaseNode[GraphState]):

  async def run(self, ctx: GraphRunContext[GraphState]) -> GeneratorAgent:
    ctx.state.summarizer_messages.append(
      ModelRequest(
        parts=[UserPromptPart(content=f"{ctx.state.link}")]
      )
    )
    with st.status("Generating Job Summary", expanded=True) as status:
      try:
        result = await st.session_state.summarizer_agent.run(
          user_prompt = ctx.state.link,
          message_history = ctx.state.summarizer_messages,
        )
        ctx.state.summarizer_messages.append(
          ModelResponse(
            parts=[TextPart(content=result.output)]
          )
        )
        ctx.state.job_summary = result.output
        st.markdown(result.output)
        status.update(label="✅ Job Summary", state="complete")
        return GeneratorAgent()
      except Exception as e:
        error_message = f"An error occurred in SummarizerAgent: {e}"
        logging.exception(error_message)
        st.session_state.error_message = error_message
        ctx.state.summarizer_messages.append(
          ModelResponse(parts=[TextPart(content=error_message)])
        )
        st.markdown(error_message)
        status.update(label="❌ Failed Summarizer Agent", state="error")
        raise
  
@dataclass
class GeneratorAgent(BaseNode[GraphState]):
  feedback: str | None = None

  async def run(self, ctx: GraphRunContext[GraphState]) -> FeedbackAgent:

    # Create the markdown string using an f-string for clarity
    combined_prompt = ""
    if ctx.state.count == 0:
      combined_prompt = f"""
      **CONTEXT: JOB SUMMARY**
      ---
      {ctx.state.job_summary}
      ---

      **USER REQUEST**
      ---
      {ctx.state.message}
      ---

      Based on the provided job summary, please fulfill the user's request. Draw from the user's resume to tailor the response.
      """
    else:
      combined_prompt = f"""
      **CONTEXT: JOB SUMMARY**
      ---
      {ctx.state.job_summary}
      ---

      **USER REQUEST**
      ---
      {ctx.state.message}
      ---

      **FEEDBACK**
      {self.feedback}

      Based on the provided job summary, please fulfill the user's request. Draw from the user's resume to tailor the response.
      """
    ctx.state.generator_messages.append(
      ModelRequest(parts=[UserPromptPart(content=combined_prompt)])
    )
    with st.status("Generating Answer", expanded=True) as status:
      try:
        result = await st.session_state.generator_agent.run(
          user_prompt = combined_prompt,
          message_history = ctx.state.generator_messages,
        )
        ctx.state.generator_messages.append(
          ModelResponse(parts=[TextPart(content=result.output)])
        )
        st.markdown(result.output)
        status.update(label="✅ Answer Generated", state="complete")
        return FeedbackAgent(result.output)
      except Exception as e:
        error_message = f"An error occurred in GeneratorAgent: {e}"
        logging.exception(error_message)
        st.session_state.error_message = error_message
        ctx.state.generator_messages.append(
          ModelResponse(parts=[TextPart(content=error_message)])
        )
        status.update(label="❌ Failed Generator Agent", state="error")
        raise

@dataclass
class FeedbackAgent(BaseNode[GraphState, None, str]):
  message: str | None = None

  async def run(self, ctx: GraphRunContext[GraphState]) -> End[str] | GeneratorAgent:
    combined_prompt = f"""
    **CONTEXT: JOB SUMMARY**
    --
    {ctx.state.job_summary}
    --

    **USER REQUEST**
    --
    {ctx.state.message}
    --

    **ANSWER GENERATED**
    --
    {self.message}
    --
    Give feedback on the answer generated and points to improve on and how to make the answer generated better.
    """
    ctx.state.feedback_messages.append(
      ModelRequest(parts=[UserPromptPart(content=combined_prompt)])
    )

    with st.status("Generating Feedback", expanded=True) as status:
      try:
        result = await st.session_state.feedback_agent.run(
          user_prompt = combined_prompt,
          message_history = ctx.state.feedback_messages,
        )
        ctx.state.feedback_messages.append(
          ModelResponse(parts=[TextPart(content=result.output)])
        )

        st.markdown(result.output)
        status.update(label="✅ Feedback generated", state="complete")
        ctx.state.count += 1
        if ctx.state.count >=2:
          return End(self.message)
        return GeneratorAgent(result.output)
      except Exception as e:
        error_message = f"An error occurred in FeedbackAgent: {e}"
        logging.exception(error_message)
        st.session_state.error_message = error_message
        ctx.state.feedback_messages.append(
          ModelResponse(parts=TextPart(content=error_message))
        )
        status.update(label="❌ Failed Feedback Agent", state="error")
        raise

  
graph = Graph(nodes=[OrchestratorAgent, SummarizerAgent, GeneratorAgent, FeedbackAgent])