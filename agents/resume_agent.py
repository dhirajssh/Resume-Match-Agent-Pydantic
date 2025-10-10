from pydantic_ai import Agent
from pydantic import Field, BaseModel
from utils import load_system_prompt
from dotenv import load_dotenv

class MarkdownResponse(BaseModel):
  """Resume returned in markdown format."""
  resume: str = Field(
    description="""
      The complete candidate resume converted into clean, structured Markdown format.

      - Each section (e.g., EDUCATION, SKILLS, EXPERIENCE, PROJECTS) must appear as a Markdown subheading (`### **SECTION NAME**`).
      - Preserve the original section order, bullet points, and formatting from the uploaded resume.
      - Do not summarize, paraphrase, or omit any content.
      - The returned Markdown must be properly formatted, readable, and ready to display or reference in downstream agents (e.g., Summarizer, Generator, Validator).
    """
  )

def initialize_resume_agent():
  agent = Agent(
    'openai:gpt-4o',
    instructions=load_system_prompt("resume.md"),
    output_retries=5,
    output_type=MarkdownResponse
  )
  return agent