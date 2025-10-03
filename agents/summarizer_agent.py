from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic import Field, BaseModel
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
    'openai:gpt-4o',
    instructions = load_system_prompt("summarizer.md"),
    deps_type = Link,
  )

  @agent.tool_plain
  def scrape_job_url(url:str):
    """
    Fetches a URL using Playwright (headless browser) and returns cleaned text suitable for LLM consumption.

    Args:
      url: The full URL of the job posting or page to fetch.
    """
    from playwright.sync_api import sync_playwright

    try:
      with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
    except Exception as e:
      return f"Error fetching url with Playwright: {e}"
    try:
      soup = BeautifulSoup(html, "html.parser")
      title = (soup.title.string if soup.title and soup.title.string else "").strip()
      for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

      text = soup.get_text(separator="\n", strip=True)
      lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
      cleaned = "\n".join(lines)
      if len(cleaned) > 4000:
        cleaned = cleaned[:4000 - 1] + "\n\n[TRUNCATED]"

      return f"URL: {url}\nTitle: {title}\n\n{cleaned}"
    except Exception as e:
      return f"ERROR: parsing HTML after Playwright fetch: {e}"
  
  return agent