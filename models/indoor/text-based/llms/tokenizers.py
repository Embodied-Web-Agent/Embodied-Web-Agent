from typing import Any
import os

import tiktoken
from transformers import LlamaTokenizer  # type: ignore

try:
    import google.generativeai as genai
    GEN_AI_SDK_AVAILABLE = True
except ImportError:
    print("Warning: google-generativeai library not found. Gemini token counting will not be available.")
    GEN_AI_SDK_AVAILABLE = False


class Tokenizer(object):
    def __init__(self, provider: str, model_name: str) -> None:
        self.provider = provider
        self.model_name = model_name
        if provider == "openai":
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        elif provider == "huggingface":
            self.tokenizer = LlamaTokenizer.from_pretrained(model_name)
            # turn off adding special tokens automatically
            self.tokenizer.add_special_tokens = False  # type: ignore[attr-defined]
            self.tokenizer.add_bos_token = False  # type: ignore[attr-defined]
            self.tokenizer.add_eos_token = False  # type: ignore[attr-defined]
        elif provider == "gemini":
            self.genai_client = None
            if GEN_AI_SDK_AVAILABLE:
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    print("Warning: GOOGLE_API_KEY environment variable not set. Gemini token counting might not work.")
                try:
                    genai.configure(api_key=api_key)
                    self.genai_client = genai.GenerativeModel(model_name=model_name)
                except Exception as e:
                    print(f"Warning: Error initializing google-genai model: {e}")
            else:
                print("Error: google-generativeai library is not available for Gemini token counting.")
        elif provider == "qwen":
            self.tokenizer=None
        else:
            self.tokenizer=None

    def encode(self, text: str) -> list[int]:
        if self.provider == "gemini":
            if self.genai_client:
                try:
                    response = self.genai_client.count_tokens(contents=text)
                    return [response.total_tokens]
                except Exception as e:
                    print(f"Error counting tokens with google-genai: {e}")
                    return [len(text.split()) // 4]  # Fallback
            else:
                return [len(text.split()) // 4]  # Fallback if client not initialized
        else:
            return self.tokenizer.encode(text)

    def decode(self, ids: list[int]) -> str:
        if self.provider == "gemini":
            raise NotImplementedError("Decoding is not directly applicable for Gemini token IDs.")
        else:
            return self.tokenizer.decode(ids)

    def __call__(self, text: str) -> list[int]:
        return self.encode(text)