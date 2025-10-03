import os

def load_system_prompt(filename: str, flag:bool = True)->str:
  """
  Read and return the system prompt stored in a markdown file.

  Args:
    filename: Just the name of the markdown file inside the `prompts/` directory containing the system prompt.

  Returns:
    The file contents as a string. If the file cannot be read, returns a brief error message string.
  """
  base_dir = os.path.dirname(__file__)
  if flag:
    prompts_dir = os.path.join(base_dir, "prompts")
    path = os.path.join(prompts_dir, filename)
  else: path = filename

  try:
    with open(path, "r", encoding="utf-8") as f:
      return f.read()
  except Exception as e:
    return f"[SYSTEM PROMPT NOT FOUND] Could not load prompt from {path}: {e}"