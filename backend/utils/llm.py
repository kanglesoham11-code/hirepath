"""
Thin async wrapper around Groq's OpenAI-compatible API.
Uses httpx so we stay fully async without requiring the openai SDK.
Includes retry logic with exponential backoff for rate limits.
"""
import httpx
import json
import re
import asyncio
import logging
from config import settings

logger = logging.getLogger("hirepath.llm")

GROQ_BASE = "https://api.groq.com/openai/v1"

MAX_RETRIES = 4
BASE_DELAY = 1.0  # seconds


async def groq_chat(
    messages: list[dict],
    system: str = "",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    json_mode: bool = False,
) -> str:
    if not settings.GROQ_API_KEY:
        return "[GROQ_API_KEY not set — skipping LLM call]"
    
    payload: dict = {
        "model": settings.GROQ_MODEL,
        "messages": ([{"role": "system", "content": system}] if system else []) + messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(f"{GROQ_BASE}/chat/completions", json=payload, headers=headers)
                
                if resp.status_code == 429:
                    # Rate limited — exponential backoff
                    retry_after = float(resp.headers.get("retry-after", BASE_DELAY * (2 ** attempt)))
                    delay = min(retry_after, 30.0)
                    logger.warning(f"Groq rate limit hit (attempt {attempt+1}/{MAX_RETRIES}). Waiting {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue

                if resp.status_code == 503 or resp.status_code == 500:
                    # Server error — retry with backoff
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning(f"Groq server error {resp.status_code} (attempt {attempt+1}/{MAX_RETRIES}). Waiting {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue
                    
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                if not content or not content.strip():
                    logger.warning(f"Empty response from Groq (attempt {attempt+1}/{MAX_RETRIES})")
                    await asyncio.sleep(BASE_DELAY)
                    continue
                    
                return content
                
        except httpx.TimeoutException as e:
            last_error = e
            delay = BASE_DELAY * (2 ** attempt)
            logger.warning(f"Groq timeout (attempt {attempt+1}/{MAX_RETRIES}). Waiting {delay:.1f}s...")
            await asyncio.sleep(delay)
        except httpx.HTTPStatusError as e:
            last_error = e
            if e.response.status_code in (429, 500, 503):
                delay = BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            raise
        except Exception as e:
            last_error = e
            logger.error(f"Groq unexpected error: {e}")
            raise

    raise Exception(f"Groq API failed after {MAX_RETRIES} retries. Last error: {last_error}")


def _extract_json_from_text(raw: str) -> dict:
    """
    Robust JSON extraction with multiple fallback strategies.
    Handles markdown fences, extra text around JSON, partial responses.
    """
    text = raw.strip()
    
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_pattern = r'```(?:json)?\s*\n?(.*?)\n?\s*```'
    match = re.search(fence_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Find the first { ... } or [ ... ] block
    brace_start = text.find('{')
    bracket_start = text.find('[')
    
    if brace_start >= 0:
        # Find matching closing brace
        depth = 0
        in_string = False
        escape = False
        for i in range(brace_start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\':
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
            if not in_string:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[brace_start:i+1])
                        except json.JSONDecodeError:
                            break
    
    # Strategy 4: Try to fix common JSON issues
    # Remove trailing commas before } or ]
    cleaned = re.sub(r',\s*([}\]])', r'\1', text)
    # Remove any text before first { and after last }
    brace_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass
    
    raise json.JSONDecodeError(f"Could not extract valid JSON from response", text, 0)


async def groq_json(
    messages: list[dict],
    system: str = "",
    max_tokens: int = 4096,
    required_keys: list[str] | None = None,
    **kwargs
) -> dict:
    """
    Calls groq_chat with json_mode=True, parses the result,
    and optionally validates required keys are present.
    Retries once if JSON parsing or validation fails.
    """
    for attempt in range(2):
        raw = await groq_chat(messages, system=system, json_mode=True, max_tokens=max_tokens, **kwargs)
        
        try:
            result = _extract_json_from_text(raw)
        except (json.JSONDecodeError, Exception) as e:
            if attempt == 0:
                logger.warning(f"JSON parse failed, retrying: {e}")
                # Add stronger instruction on retry
                retry_messages = messages.copy()
                retry_messages.append({
                    "role": "user",
                    "content": "Your previous response was not valid JSON. Please respond with ONLY a valid JSON object, no other text."
                })
                messages = retry_messages
                await asyncio.sleep(1)
                continue
            raise
        
        # Validate required keys if specified
        if required_keys:
            missing = [k for k in required_keys if k not in result]
            if missing and attempt == 0:
                logger.warning(f"Missing required keys {missing}, retrying...")
                retry_messages = messages.copy()
                retry_messages.append({
                    "role": "user",
                    "content": f"Your response is missing required keys: {missing}. Please include ALL of these keys in your JSON response."
                })
                messages = retry_messages
                await asyncio.sleep(1)
                continue
            elif missing:
                # Fill missing keys with defaults on last attempt
                for key in missing:
                    result[key] = None
        
        return result
    
    raise Exception("groq_json failed after retries")
