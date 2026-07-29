import os
import time
from pathlib import Path

import requests
import streamlit as st


# ---------------------------------------------------------
# Load environment variables from .env
# ---------------------------------------------------------
def load_dotenv_file(path: str | None = None) -> None:
    base_dir = Path(__file__).resolve().parent
    env_paths = []

    if path:
        provided_path = Path(path).expanduser()
        env_paths.append(
            provided_path
            if provided_path.is_absolute()
            else (base_dir / provided_path)
        )

    env_paths.extend([
        base_dir / ".env",
        Path.cwd() / ".env",
    ])

    seen_paths = set()

    for env_path in env_paths:
        resolved_path = env_path.resolve()

        if resolved_path in seen_paths:
            continue

        seen_paths.add(resolved_path)

        if not resolved_path.is_file():
            continue

        for raw_line in resolved_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value

        break


# Load .env file
load_dotenv_file()


# ---------------------------------------------------------
# Gemini Configuration
# ---------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3.6-flash"


# ---------------------------------------------------------
# Gemini API
# ---------------------------------------------------------
def generate_assistant_response(prompt: str) -> str:

    if not GEMINI_API_KEY:
        return (
            "Error: GEMINI_API_KEY is not configured.\n\n"
            "Add GEMINI_API_KEY to your .env file."
        )

    # Remove "models/" if accidentally provided in .env
    model_name = GEMINI_MODEL.removeprefix("models/")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model_name}:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        },
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60,
        )

        # Handle API errors
        if not response.ok:
            try:
                error_data = response.json()

                error_message = (
                    error_data
                    .get("error", {})
                    .get("message", response.text)
                )

            except Exception:
                error_message = response.text

            return (
                f"Gemini API error ({response.status_code}): "
                f"{error_message}"
            )

        data = response.json()

        # -------------------------------------------------
        # Extract response
        # -------------------------------------------------
        candidates = data.get("candidates", [])

        if not candidates:
            return (
                "Gemini did not return a response.\n\n"
                f"API response: {data}"
            )

        content = candidates[0].get("content", {})

        parts = content.get("parts", [])

        text_parts = [
            part.get("text", "")
            for part in parts
            if part.get("text")
        ]

        if not text_parts:
            return (
                "Gemini returned a response but no text "
                "was available."
            )

        return "".join(text_parts).strip()

    except requests.exceptions.Timeout:
        return (
            "Gemini API error: Request timed out. "
            "Please try again."
        )

    except requests.exceptions.ConnectionError:
        return (
            "Gemini API error: Unable to connect to "
            "Google Gemini API."
        )

    except requests.exceptions.RequestException as exc:
        return f"Gemini API request failed: {exc}"

    except Exception as exc:
        return f"Unexpected error: {exc}"


# ---------------------------------------------------------
# Streamlit Application
# ---------------------------------------------------------
def main():

    st.set_page_config(
        page_title="Gemini Chat",
        page_icon="🤖",
    )

    st.title("Gemini Chat 🤖")

    st.caption(
        f"Powered by Google Gemini • Model: {GEMINI_MODEL}"
    )

    # -----------------------------------------------------
    # Validate API key
    # -----------------------------------------------------
    if not GEMINI_API_KEY:
        st.error(
            "GEMINI_API_KEY is not configured. "
            "Please add it to your .env file."
        )
        st.stop()

    # -----------------------------------------------------
    # Initialize chat history
    # -----------------------------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! How can I help you today? 👋",
            }
        ]

    # -----------------------------------------------------
    # Display previous messages
    # -----------------------------------------------------
    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # -----------------------------------------------------
    # User input
    # -----------------------------------------------------
    prompt = st.chat_input("Ask me anything...")

    if prompt:

        # Save user message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # -------------------------------------------------
        # Generate Gemini response
        # -------------------------------------------------
        with st.chat_message("assistant"):

            message_placeholder = st.empty()

            with st.spinner("Thinking..."):
                assistant_response = (
                    generate_assistant_response(prompt)
                )

            # -------------------------------------------------
            # Streaming-style display
            # -------------------------------------------------
            full_response = ""

            for word in assistant_response.split():

                full_response += word + " "

                message_placeholder.markdown(
                    full_response + "▌"
                )

                time.sleep(0.02)

            full_response = full_response.strip()

            message_placeholder.markdown(full_response)

        # -------------------------------------------------
        # Save assistant response
        # -------------------------------------------------
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_response,
            }
        )


# ---------------------------------------------------------
# Run application
# ---------------------------------------------------------
if __name__ == "__main__":
    main()