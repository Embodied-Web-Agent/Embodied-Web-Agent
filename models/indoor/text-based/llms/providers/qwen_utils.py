"""Tools to generate from Qwen prompts."""

import asyncio
import logging
import os
import random
import time
from typing import Any, List, Dict

import dashscope
from dashscope import Generation
# from dashscope.common.error import RateLimitError as DashscopeRateLimitError
from tqdm.asyncio import tqdm_asyncio
import aiolimiter

# def retry_with_exponential_backoff(  # type: ignore
#     func,
#     initial_delay: float = 1,
#     exponential_base: float = 2,
#     jitter: bool = True,
#     max_retries: int = 3,
#     errors: tuple[Any] = (DashscopeRateLimitError,),
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


async def _throttled_qwen_chat_completion_acreate(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    top_p: float,
    limiter: aiolimiter.AsyncLimiter,
) -> Dict[str, Any]:
    async with limiter:
        for _ in range(3):
            try:
                response = await Generation.acall(
                    model=model,
                    messages=messages,
                    temperature=0,
                    max_tokens=max_tokens,
                    top_p=top_p,
                )
                if response.status_code == 200:
                    return {"choices": [{"message": {"content": response.output.choices[0].message.content}}]}
                else:
                    logging.warning(f"Qwen API error: {response}")
                    break
            except DashscopeRateLimitError:
                logging.warning(
                    "Qwen API rate limit exceeded. Sleeping for 10 seconds."
                )
                await asyncio.sleep(10)
            except Exception as e:
                logging.warning(f"Qwen API error: {e}")
                break
        return {"choices": [{"message": {"content": ""}}]}


async def agenerate_from_qwen_chat_completion(
    messages_list: List[List[Dict[str, str]]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    context_length: int,
    requests_per_minute: int = 300,
) -> List[str]:
    """Generate from Qwen Chat Completion API.

    Args:
        messages_list: list of message list
        model: The Qwen model to use.
        temperature: Temperature to use.
        max_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        context_length: Length of context to use (not directly used by Qwen API).
        requests_per_minute: Number of requests per minute to allow.

    Returns:
        List of generated responses.
    """
    if "DASHSCOPE_API_KEY" not in os.environ:
        raise ValueError(
            "DASHSCOPE_API_KEY environment variable must be set when using Qwen API."
        )
    dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]

    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    async_responses = [
        _throttled_qwen_chat_completion_acreate(
            model=model,
            messages=message,
            temperature=0,
            max_tokens=max_tokens,
            top_p=top_p,
            limiter=limiter,
        )
        for message in messages_list
    ]
    responses = await tqdm_asyncio.gather(*async_responses)
    return [x["choices"][0]["message"]["content"] for x in responses]


# @retry_with_exponential_backoff(errors=(DashscopeRateLimitError,))
def generate_from_qwen_chat_completion(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    context_length: int,
    stop_token: str | None = None,
) -> str:
    """Generate from Qwen Chat Completion API (synchronous).

    Args:
        messages: list of messages
        model: The Qwen model to use.
        temperature: Temperature to use.
        max_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        context_length: Length of context to use (not directly used by Qwen API).
        stop_token: Stop token to use.

    Returns:
        Generated response.
    """
    if "DASHSCOPE_API_KEY" not in os.environ:
        raise ValueError(
            "DASHSCOPE_API_KEY environment variable must be set when using Qwen API."
        )
    dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]

    response = Generation.call(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=max_tokens,
        top_p=top_p,
        stop=([stop_token] if stop_token else None),
    )
    print (response)
    if response.status_code == 200:
        return response.output.text
    else:
        raise Exception(f"Qwen API error: {response}")


# @retry_with_exponential_backoff(errors=(DashscopeRateLimitError,))
# # debug only
def fake_generate_from_qwen_chat_completion(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    context_length: int,
    stop_token: str | None = None,
) -> str:
    """Fake generation from Qwen Chat Completion API for debugging."""
    if "DASHSCOPE_API_KEY" not in os.environ:
        raise ValueError(
            "DASHSCOPE_API_KEY environment variable must be set when using Qwen API."
        )
    dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]
    answer = "Let's think step-by-step. This page shows a list of links and buttons. There is a search box with the label 'Search query'. I will click on the search box to type the query. So the action I will perform is \"click [60]\"."
    return answer