import os
import random
import time
from pathlib import Path

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import requests
except Exception:
    requests = None


def load_dotenv_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv_file()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

API_KEY = GEMINI_API_KEY or OPENAI_API_KEY
API_KEY_SOURCE = "GEMINI_API_KEY" if GEMINI_API_KEY else "OPENAI_API_KEY" if OPENAI_API_KEY else None

openai_client = None
if OpenAI is not None and API_KEY:
    openai_client = OpenAI(api_key=API_KEY, base_url=OPENAI_API_BASE)


def generate_assistant_response(prompt: str) -> str:
    # Prefer Gemini key + REST call if available (user requested Gemini-only usage)
    if GEMINI_API_KEY:
        if requests is None:
            return "Error: `requests` library is required for Gemini HTTP calls. Install with `pip install requests`."

        # Some Gemini models use different RPC names; try both common endpoints.
        params = {"key": GEMINI_API_KEY}
        payload = {"prompt": {"text": prompt}, "temperature": 0.7}

        endpoints = [
            f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateText",
            f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent",
        ]

        last_err = None
        for url in endpoints:
            try:
                resp = requests.post(url, params=params, json=payload, timeout=15)
                if resp.status_code == 404:
                    last_err = f"404 from {url}"
                    continue
                resp.raise_for_status()
                data = resp.json()

                # Try common fields returned by the Generative Language API
                content = None
                if isinstance(data, dict):
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        # candidate may have 'content' or 'output' or 'content[0].text'
                        content = candidate.get("content") or candidate.get("output")
                        if not content and isinstance(candidate.get("content"), list):
                            # look for nested text
                            for item in candidate.get("content"):
                                if isinstance(item, dict) and item.get("text"):
                                    content = item.get("text")
                                    break
                    if not content:
                        content = data.get("output") or data.get("text")

                if content:
                    return content.strip()
                return f"Gemini API returned unexpected response: {data}"
            except Exception as exc:
                last_err = str(exc)
                continue

        return f"Gemini API error: {last_err}"

    # Fallback: use OpenAI client if configured
    if OpenAI is None:
        return "Error: openai package not installed. Install with `pip install openai`"

    if not API_KEY:
        return (
            "Error: OPENAI_API_KEY is not set. "
            "If you want Gemini-only usage, set GEMINI_API_KEY in your .env."
        )

    if openai_client is None:
        return (
            "Error: Could not initialize OpenAI client. "
            "Check your openai package version and OPENAI_API_BASE settings."
        )

    try:
        response = openai_client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"OpenAI API error: {exc}"


def main():
    st.write(
        "Streamlit loves LLMs! 🤖 [Build your own chat app](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps) in minutes, then make it powerful by adding images, dataframes, or even input widgets to the chat."
    )

    st.caption(
        "This app uses a Gemini model via the OpenAI API. "
        f"Reading API key from `{API_KEY_SOURCE or 'none'}`."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            assistant_response = generate_assistant_response(prompt)
            full_response = ""
            for chunk in assistant_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    main()
