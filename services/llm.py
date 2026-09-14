"""Gemini chat client initialized via langchain-google-genai."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_chat_llm(*, temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    model = (os.getenv("GEMINI_MODEL") or "gemini-3.6-flash").strip()

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in .env")

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
    )


def message_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("text"):
                parts.append(str(block["text"]))
            elif hasattr(block, "text"):
                parts.append(str(block.text))
        return "".join(parts)
    return str(content)
