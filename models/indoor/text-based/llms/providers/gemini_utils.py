"""Tools to generate from Gemini prompts.
Adopted from https://github.com/zeno-ml/zeno-build/"""

import asyncio
import logging
import os
import random
import time
from typing import Any, List, Dict, Optional

import aiolimiter
import google.generativeai as genai
from google.api_core import retry
from tqdm.asyncio import tqdm_asyncio


from typing import Any
import google.generativeai as genai

from typing import Any
import google.generativeai as genai
import time
import random

async def _throttled_gemini_generate_content_async(
    model_name: str,
    prompt: str,
    generation_config: Optional[Dict[str, Any]],
    limiter: aiolimiter.AsyncLimiter,
) -> genai.types.GenerateContentResponse:
    async with limiter:
        for _ in range(3):
            try:
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(
                    prompt, generation_config=generation_config
                )
                return response
            except genai.generative_models.APIError as e:
                logging.warning(f"Gemini API error: {e}")
                await asyncio.sleep(10)
            except genai.generative_models.GenerativeModelError as e:
                logging.warning(f"Gemini model error: {e}")
                await asyncio.sleep(10)
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                break
        return genai.types.GenerateContentResponse(candidates=[])


async def agenerate_from_gemini_completion(
    prompts: List[str],
    model_name: str,
    temperature: float,
    max_output_tokens: int,
    top_p: float,
    requests_per_minute: int = 300,
) -> List[str]:
    """Generate from Gemini API.

    Args:
        prompts: list of prompts
        model_name: Name of the Gemini model to use (e.g., "gemini-pro").
        temperature: Temperature to use.
        max_output_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        requests_per_minute: Number of requests per minute to allow.

    Returns:
        List of generated responses.
    """
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError(
            "GOOGLE_API_KEY environment variable must be set when using Gemini API."
        )
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "top_p": top_p
    }

    async_responses = [
        _throttled_gemini_generate_content_async(
            model_name=model_name,
            prompt=prompt,
            generation_config=generation_config,
            limiter=limiter,
        )
        for prompt in prompts
    ]
    responses = await tqdm_asyncio.gather(*async_responses)
    return [
        response.candidates[0].content.parts[0].text
        if response.candidates
        else ""
        for response in responses
    ]


# @retry_with_exponential_backoff
def generate_from_gemini_completion(
    prompt: str,
    model_name: str,
    temperature: float,
    max_output_tokens: int,
    top_p: float,
    stop_sequences: Optional[List[str]] = None,
) -> str:
    """Generate from Gemini API.

    Args:
        prompt: The prompt for generation.
        model_name: Name of the Gemini model to use (e.g., "gemini-pro").
        temperature: Temperature to use.
        max_output_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        stop_sequences: Optional list of stop sequences.

    Returns:
        The generated response.
    """
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError(
            "GOOGLE_API_KEY environment variable must be set when using Gemini API."
        )
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(model_name)
    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "top_p": top_p,
        "stop_sequences": stop_sequences if stop_sequences else [],
    }

    response = model.generate_content(prompt, generation_config=generation_config)
    if response.candidates and response.candidates[0].content.parts:
        return response.candidates[0].content.parts[0].text
    else:
        return ""


async def _throttled_gemini_generate_content_async_multi_turn(
    model_name: str,
    messages: List[Dict[str, str]],
    generation_config: Optional[Dict[str, Any]],
    limiter: aiolimiter.AsyncLimiter,
) -> genai.types.GenerateContentResponse:
    async with limiter:
        for _ in range(3):
            try:
                model = genai.GenerativeModel(model_name)
                chat = model.start_chat(history=[])
                response = await chat.send_message_async(
                    messages, generation_config=generation_config
                )
                return response
            except genai.generative_models.APIError as e:
                logging.warning(f"Gemini API error: {e}")
                await asyncio.sleep(10)
            except genai.generative_models.GenerativeModelError as e:
                logging.warning(f"Gemini model error: {e}")
                await asyncio.sleep(10)
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                break
        return genai.types.GenerateContentResponse(candidates=[])


async def agenerate_from_gemini_chat_completion(
    messages_list: List[List[Dict[str, str]]],
    model_name: str,
    temperature: float,
    max_output_tokens: int,
    top_p: float,
    requests_per_minute: int = 300,
) -> List[str]:
    """Generate from Gemini Chat API.

    Args:
        messages_list: list of message lists, where each inner list represents a conversation.
        model_name: Name of the Gemini model to use (e.g., "gemini-pro").
        temperature: Temperature to use.
        max_output_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        requests_per_minute: Number of requests per minute to allow.

    Returns:
        List of generated responses.
    """
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError(
            "GOOGLE_API_KEY environment variable must be set when using Gemini API."
        )
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "top_p": top_p
    }

    async_responses = [
        _throttled_gemini_generate_content_async_multi_turn(
            model_name=model_name,
            messages=messages,
            generation_config=generation_config,
            limiter=limiter,
        )
        for messages in messages_list
    ]
    responses = await tqdm_asyncio.gather(*async_responses)
    return [
        response.candidates[0].content.parts[0].text
        if response.candidates
        else ""
        for response in responses
    ]


# @retry_with_exponential_backoff
def generate_from_gemini_chat_completion(
    messages: List[Dict[str, Any]],  # Use Any for flexibility with "parts"
    model_name: str,
    temperature: float,
    max_output_tokens: int,
    top_p: float,
    stop_sequences: Optional[List[str]] = None,
) -> str:
    """Generate from Gemini Chat API.

    Args:
        messages: List of messages representing the conversation history.
            Each message should be a dict with "role" and "parts" keys.
            "parts" is a list of dicts, typically with "text" key.
        model_name: Name of the Gemini model to use (e.g., "gemini-pro").
        temperature: Temperature to use.
        max_output_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        stop_sequences: Optional list of stop sequences.

    Returns:
        The generated response.
    """
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError(
            "GOOGLE_API_KEY environment variable must be set when using Gemini API."
        )
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(model_name)

    # Format history for Gemini
    history = []
    for message in messages[:-1]:  # Exclude the last message (current turn)
        role = message.get("role")
        parts = message.get("parts")
        if role and parts:
            gemini_message = {"role": role, "parts": []}  # Initialize for Gemini
            for part in parts:
                if part.get("text"):
                    gemini_message["parts"].append({"text": part["text"]})  # Add text part
            history.append(gemini_message)

    chat = model.start_chat(history=history)

    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "top_p": top_p
    }

    # Extract content from the last message
    last_message = messages[-1]
    last_content = ""
    if last_message.get("parts"):
        for part in last_message["parts"]:
            if part.get("text"):
                last_content += part["text"]

    response = chat.send_message(last_content, generation_config=generation_config)

    if response.candidates and response.candidates[0].content.parts:
        return response.candidates[0].content.parts[0].text
    else:
        return ""

# @retry_with_exponential_backoff
def fake_generate_from_gemini_chat_completion(
    messages: List[Dict[str, str]],
    model_name: str,
    temperature: float,
    max_output_tokens: int,
    top_p: float,
    stop_sequences: Optional[List[str]] = None,
) -> str:
    """Fake generation function for debugging purposes."""
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError(
            "GOOGLE_API_KEY environment variable must be set when using Gemini API."
        )
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    answer = "Let's think step-by-step. This page shows a list of links and buttons. There is a search box with the label 'Search query'. I will click on the search box to type the query. So the action I will perform is \"click [60]\"."
    return answer