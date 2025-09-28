from pydantic import BaseModel, Field
from typing import Literal, Optional
from dataclasses import dataclass
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
import streamlit as st
from pydantic_ai.messages import UserPromptPart, TextPart
from agents.summarizer_agent import Link

class GraphState(BaseModel):
  agent: Literal["summarizer_agent", "generator_agent"] = Field(
    ...,
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
  count: int = Field(default = 0)
  orchestrator_messages: list = Field(default_factory = list)
  summarizer_messages: list = Field(default_factory = list)
  generator_messages: list = Field(default_factory = list)
  job_summary: str = Field(default=None)

  
@dataclass
class OrchestratorAgent(BaseNode[GraphState]):

  def run(self, ctx: GraphRunContext[GraphState]) -> "SummarizerAgent" | "GeneratorAgent":
    ctx.state.orchestrator_messages.append(UserPromptPart(content=f"{st.session_state["user_input"]}"))
    result = st.session_state.orchestrator_agent.run_sync(
      user_prompt = st.session_state["user_input"],
      message_history = ctx.state.orchestrator_messages
    )
    ctx.state.orchestrator_messages.append(result)
    ctx.state.agent = result.output.agent
    ctx.state.link = result.output.link
    ctx.state.message = result.output.message
    if ctx.state.agent == "summarizer_agent":
      return SummarizerAgent()
    else:
      return GeneratorAgent()
    
@dataclass
class SummarizerAgent(BaseNode[GraphState]):

  def run(self, ctx: GraphRunContext[GraphState]):
    ctx.state.summarizer_messages.append(UserPromptPart(content=f"{ctx.state.link}"))
    agent_link = Link(url=ctx.state.link)
    result = st.session_state.summarizer_agent.run_sync(
      user_prompt = ctx.state.link,
      message_history = ctx.state.summarizer_messages,
      deps = agent_link,
    )
    ctx.state.summarizer_messages.append(result)
    ctx.state.job_summary = result.output
    print(result.output)
    return GeneratorAgent()
  
@dataclass
class GeneratorAgent(BaseNode[GraphState, None, str]):

  def run(self, ctx: GraphRunContext[GraphState]):

    # Create the markdown string using an f-string for clarity
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
    ctx.state.generator_messages.append(UserPromptPart(content=combined_prompt))
    try:
      result = st.session_state.generator_agent.run_sync(
        user_prompt = combined_prompt,
        message_history = ctx.state.generator_messages,
      )
      ctx.state.generator_messages.extend(result.messages)
      return End(result.output)
    except Exception as e:
      error_message = f"An error occurred in GeneratorAgent: {e}"
      st.session_state.error_message = error_message
      ctx.state.generator_messages.append(TextPart(content=error_message))
      raise
  
graph = Graph(nodes=[OrchestratorAgent, SummarizerAgent, GeneratorAgent])