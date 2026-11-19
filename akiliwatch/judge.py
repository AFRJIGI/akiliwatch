"""The AI judge. Any backend is a function `prompt -> text`. Two are built in; for any other model use
`--dump-prompts` and paste the prompts yourself, or pass your own callable from Python."""

import json
import re


def parse_result(text):
    """JSON from the judge, even wrapped in ```json fences. None if unreadable."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        result = json.loads(text)
    except ValueError:
        found = re.search(r"\{.*\}", text, flags=re.S)
        if not found:
            return None
        try:
            result = json.loads(found.group(0))
        except ValueError:
            return None
    if not isinstance(result, dict):
        return None
    result.setdefault("problems", [])
    return result


def gemini_backend(model="gemini-2.5-flash", project=None, location="global", api_key=None):
    """Gemini through the Google Gen AI SDK (pip install google-genai). With `project`, uses Vertex AI and
    Application Default Credentials; with `api_key`, uses the Gemini Developer API."""
    from google import genai
    from google.genai import types

    client = (genai.Client(api_key=api_key) if api_key
              else genai.Client(vertexai=True, project=project, location=location))
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)

    def call(prompt):
        return client.models.generate_content(model=model, contents=prompt, config=config).text

    return call


def build_prompt(grid, profile, transcript_text):
    return grid.replace("{profile}", profile or "unknown").replace("{transcript}", transcript_text)


def judge_conversation(call, grid, profile, transcript_text, retries=2):
    """Run the judge, retrying on errors such as 429. Returns (result or None, error text or None)."""
    import time
    prompt = build_prompt(grid, profile, transcript_text)
    last = None
    for attempt in range(retries + 1):
        try:
            result = parse_result(call(prompt))
            if result is not None:
                return result, None
            last = "unreadable answer"
        except Exception as exc:  # network, quota... the audit must keep going
            last = repr(exc)
        time.sleep(2 * (attempt + 1))
    return None, last
