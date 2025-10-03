import os
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from utils import load_system_prompt
from dotenv import load_dotenv
import streamlit as st

def initialize_generator_agent():
  load_dotenv()
  api_key = os.getenv("GOOGLE_API_KEY")
  provider = GoogleProvider(api_key=api_key)
  model = GoogleModel("gemini-2.5-pro", provider=provider)
  resume_path = os.path.join(os.path.dirname(__file__), "..", "resume.md")
  if os.path.exists(resume_path):
    resume = load_system_prompt("resume.md")
    st.session_state.resume = resume
  else:
    resume = st.session_state.resume

  prompt = load_system_prompt("generator.md")
  full_prompt = f"{prompt}\n\n---\n\n{resume}"

  agent = Agent(
    'openai:gpt-4o',
    instructions = full_prompt,
  )
  return agent