from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic import Field, field_validator, BaseModel
from typing import Optional, Literal
import os
from utils import load_system_prompt
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests

class Link(BaseModel):
  url: str = Field(description="url if provided by the user")

def initialize_summarizer_agent():
  load_dotenv()
  api_key = os.getenv("GOOGLE_API_KEY")
  provider = GoogleProvider(api_key=api_key)
  model = GoogleModel("gemini-2.5-pro", provider=provider)
  agent = Agent(
    model = model,
    instructions = load_system_prompt("summarizer.md"),
    deps_type = Link,
  )

  @agent.tool
  def scrape_job_url(ctx: RunContext):
    """
    Fetches a URL and returns cleaned text suitable for LLM consumption.

    Args:
      url: The full URL of the job posting or page to fetch.
    """
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
      "Accept-Language": "en-US,en;q=0.9",
    }
    try:
      response = requests.get(ctx.deps.url, headers=headers, timeout=8)
      response.raise_for_status()  # Raise an exception for bad status codes
      html = response.text
    except requests.exceptions.RequestException as e:
      return f"Error fetching url: {e}"
    
    try:
      soup = BeautifulSoup(html, "html.parser")
      title = (soup.title.string if soup.title and soup.title.string else "").strip()
      main = soup
      for tag in main(["script", "style", "noscript", "iframe"]):
        tag.decompose()

      text = main.get_text(separator="\n", strip=True)
      # collapse and clean lines
      lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
      cleaned = "\n".join(lines)

      if len(cleaned) > 4000:
          cleaned = cleaned[: 4000 - 1] + "\n\n[TRUNCATED]"

      return f"URL: {ctx.deps.url}\nTitle: {title}\n\n{cleaned}"
    except Exception as e:
      return f"ERROR: parsing HTML: {e}"