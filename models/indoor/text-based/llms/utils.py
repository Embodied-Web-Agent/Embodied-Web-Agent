import argparse
from typing import Any

from llms import (
    generate_from_huggingface_completion,
    generate_from_openai_chat_completion,
    generate_from_openai_completion,
    generate_from_gemini_chat_completion,
    generate_from_qwen_chat_completion,
    generate_from_intern_chat_completion,
    generate_from_gemini_completion,
    lm_config,
)

APIInput = str | list[Any] | dict[str, Any]


def call_llm(
    lm_config: lm_config.LMConfig,
    prompt: APIInput,
) -> str:
    response: str
    if lm_config.provider == "openai":
        if lm_config.mode == "chat":
            assert isinstance(prompt, list)
            response = generate_from_openai_chat_completion(
                messages=prompt,
                model=lm_config.model,
                temperature=lm_config.gen_config["temperature"],
                top_p=lm_config.gen_config["top_p"],
                context_length=lm_config.gen_config["context_length"],
                max_tokens=lm_config.gen_config["max_tokens"],
                stop_token=None,
            )
        elif lm_config.mode == "completion":
            assert isinstance(prompt, str)
            response = generate_from_openai_completion(
                prompt=prompt,
                engine=lm_config.model,
                temperature=lm_config.gen_config["temperature"],
                max_tokens=lm_config.gen_config["max_tokens"],
                top_p=lm_config.gen_config["top_p"],
                stop_token=lm_config.gen_config["stop_token"],
            )
        else:
            raise ValueError(
                f"OpenAI models do not support mode {lm_config.mode}"
            )
    elif lm_config.provider == "huggingface":
        assert isinstance(prompt, str)
        response = generate_from_huggingface_completion(
            prompt=prompt,
            model_endpoint=lm_config.gen_config["model_endpoint"],
            temperature=lm_config.gen_config["temperature"],
            top_p=lm_config.gen_config["top_p"],
            stop_sequences=lm_config.gen_config["stop_sequences"],
            max_new_tokens=lm_config.gen_config["max_new_tokens"],
        )
    elif lm_config.provider == "gemini":
        if lm_config.mode == "chat":
            assert isinstance(prompt, list)
            response = generate_from_gemini_chat_completion(
                messages=prompt,
                model_name=lm_config.model,
                temperature=lm_config.gen_config["temperature"],
                top_p=lm_config.gen_config["top_p"],
                max_output_tokens=lm_config.gen_config["max_tokens"],
                stop_sequences=None,
            )

        elif lm_config.mode == "completion":
            assert isinstance(prompt, str)
            response = generate_from_gemini_completion(
                prompt=prompt,
                model_name=lm_config.model,
                temperature=lm_config.gen_config["temperature"],
                max_output_tokens=lm_config.gen_config["max_tokens"],
                top_p=lm_config.gen_config["top_p"],
                stop_sequences=lm_config.gen_config.get("stop_sequences"),
            )
        else:
            raise ValueError(
                f"Gemini models do not support mode {lm_config.mode}"
            )
    elif lm_config.provider == "qwen":
        if lm_config.mode == "chat":
            assert isinstance(prompt, list)
            response = generate_from_qwen_chat_completion(
                messages=prompt,
                model=lm_config.model,
                temperature=lm_config.gen_config.get("temperature", 1.0),  # Use get with default
                top_p=lm_config.gen_config.get("top_p", 1.0),  # Use get with default
                context_length=lm_config.gen_config.get("context_length", 2048), # Use get with default
                max_tokens=lm_config.gen_config.get("max_tokens", 1024),  # Use get with default
                stop_token=lm_config.gen_config.get("stop_token"), # Use get (can be None)
            )
        else:
            raise ValueError(
                f"Qwen models only support mode 'chat', not '{lm_config.mode}'"
            )
    elif lm_config.provider == "intern":
        if lm_config.mode == "chat":
            assert isinstance(prompt, list)
            response = generate_from_intern_chat_completion(
                messages=prompt,
                model=lm_config.model,
                temperature=lm_config.gen_config["temperature"],
                top_p=lm_config.gen_config["top_p"],
                context_length=lm_config.gen_config["context_length"],
                max_tokens=lm_config.gen_config["max_tokens"],
                stop_token=None,  # Consider if InternLM API supports stop tokens
            )
        elif lm_config.mode == "completion":
            raise ValueError(
                "InternLM API does not have a direct 'completion' mode similar to OpenAI. Please use 'chat' mode with a single user message."
            )
        else:
            raise ValueError(f"InternLM models do not support mode {lm_config.mode}")
    else:
        raise NotImplementedError(
            f"Provider {lm_config.provider} not implemented"
        )

    return response
