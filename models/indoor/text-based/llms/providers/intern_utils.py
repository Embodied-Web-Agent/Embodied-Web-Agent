# intern_utils.py

import asyncio
import logging
import os
import random
import time
from typing import Any, List, Dict, Optional

import aiolimiter
import requests
import json
from tqdm.asyncio import tqdm_asyncio

# Default API URL for InternLM Chat Completions
DEFAULT_INTERN_API_URL = 'https://chat.intern-ai.org.cn/api/v1/chat/completions'


def get_intern_api_key() -> Optional[str]:
    """Retrieves the InternLM API key from the environment variable."""
    return os.environ.get("INTERN_API_KEY")


# def retry_with_exponential_backoff(  # type: ignore
#     func,
#     initial_delay: float = 1,
#     exponential_base: float = 2,
#     jitter: bool = True,
#     max_retries: int = 3,
#     errors: tuple[Any] = (requefmsts.exceptions.RequestException,),
# ):
#     """Retry a function with exponential backoff."""

#     def wrapper(*args, **kwargs):  # type: ignore
#         # Initialize variables
#         num_retries = 0
#         delay = initial_delay

#         # Loop until a successful response or max_retries is hit or an exception is raised
#         while True:
#             try:
#                 return func(*args, **kwargs)
#             # Retry on specified errors
#             except errors as e:
#                 # Increment retries
#                 num_retries += 1

#                 # Check if max retries has been reached
#                 if num_retries > max_retries:
#                     raise Exception(
#                         f"Maximum number of retries ({max_retries}) exceeded."
#                     )

#                 # Increment the delay
#                 delay *= exponential_base * (1 + jitter * random.random())
#                 print(f"Retrying in {delay} seconds.")
#                 # Sleep for the delay
#                 time.sleep(delay)

#             # Raise exceptions for any errors not specified
#             except Exception as e:
#                 raise e

#     return wrapper


async def _throttled_intern_chat_completion_acreate(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    top_p: float,
    api_url: str,
    headers: Dict[str, str],
    limiter: aiolimiter.AsyncLimiter,
) -> Dict[str, Any]:
    async with limiter:
        for _ in range(3):
            try:
                data = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                }
                response = await asyncio.to_thread(
                    requests.post, api_url, headers=headers, json=data
                )
                response.raise_for_status()  # Raise an exception for bad status codes
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.warning(f"InternLM API error: {e}")
                await asyncio.sleep(10)
            except json.JSONDecodeError as e:
                logging.warning(f"JSON decode error: {e}")
                await asyncio.sleep(10)
        return {"choices": [{"message": {"content": ""}}]}


async def agenerate_from_intern_chat_completion(
    messages_list: List[List[Dict[str, str]]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    context_length: int,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    requests_per_minute: int = 300,
) -> List[str]:
    """Generate from InternLM Chat Completion API.

    Args:
        messages_list: list of message list
        model: The name of the InternLM model to use.
        temperature: Temperature to use.
        max_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        context_length: Length of context to use (not directly used in API call).
        api_url: The URL of the InternLM Chat API endpoint. Defaults to DEFAULT_INTERN_API_URL.
        api_key: The API key for authentication. If None, it tries to get it from the environment variable.
        requests_per_minute: Number of requests per minute to allow.

    Returns:
        List of generated responses.
    """
    if model.startswith("intern"):
        if api_key is None:
            api_key = get_intern_api_key()
        if not api_key:
            raise ValueError(
                "The INTERN_API_KEY environment variable must be set when using InternLM models."
            )
        headers = {
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {api_key}"
        }
        target_api_url = api_url if api_url else DEFAULT_INTERN_API_URL
    else:
        headers = {'Content-Type': 'application/json'}
        target_api_url = api_url if api_url else DEFAULT_INTERN_API_URL # You might have a different default or no auth

    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    async_responses = [
        _throttled_intern_chat_completion_acreate(
            model=model,
            messages=message,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            api_url=target_api_url,
            headers=headers,
            limiter=limiter,
        )
        for message in messages_list
    ]
    responses = await tqdm_asyncio.gather(*async_responses)
    return [x["choices"][0]["message"]["content"] for x in responses]


# @retry_with_exponential_backoff
def generate_from_intern_chat_completion(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    context_length: int,
    stop_token: Optional[str] = None,
) -> str:
    """Generate from InternLM Chat Completion API.

    Args:
        messages: List of messages in the conversation.
        model: The name of the model to use.
        temperature: Temperature to use.
        max_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        context_length: Length of context to use (not directly used in API call).
        api_url: The URL of the API endpoint. Defaults to DEFAULT_INTERN_API_URL if the model is InternLM.
        api_key: The API key for authentication. If None and the model is InternLM, it tries to get it from the environment variable.
        stop_token: Optional stop token.

    Returns:
        Generated response.
    """
    api_key = get_intern_api_key()
    if not api_key:
        raise ValueError(
            "The INTERN_API_KEY environment variable must be set when using InternLM models."
        )
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {api_key}"
    }
    target_api_url = DEFAULT_INTERN_API_URL

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
    }
    if stop_token:
        # Note: The InternLM API documentation does not explicitly mention 'stop' parameter.
        pass # Consider logging a warning or removing this if not supported

    response = requests.post(target_api_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# @retry_with_exponential_backoff
# # debug only
def fake_generate_from_intern_chat_completion(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    context_length: int,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    stop_token: Optional[str] = None,
) -> str:
    """Fake generation for debugging purposes."""
    answer = "Let's think step-by-step. This page shows a list of links and buttons. There is a search box with the label 'Search query'. I will click on the search box to type the query. So the action I will perform is \"click [60]\"."
    return answer