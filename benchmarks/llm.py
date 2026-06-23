import os
import ssl
import sys

import httpx
import litellm
from openai import OpenAI

litellm.ssl_verify = False

MODELS = {
    "qwen": {
        "litellm_model": "openai/Qwen/Qwen3-14B",
        "api_base": "https://qwen3-14b--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443/v1",
        "env_key": "SANDBOX_API_KEY_QWEN3",
        "extra_params": {"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}},
    },
    "claude-haiku": {
        "litellm_model": "anthropic/claude-haiku-4-5-20251001",
        "api_base": "https://claude--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443",
        "env_key": "SANDBOX_API_KEY_CLAUDE",
        "extra_params": {},
    },
}

EMBED_CONFIG = {
    "model": "nomic-ai/nomic-embed-text-v1.5",
    "base_url": "https://nomic-embed-text-v1-5--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com/v1",
    "env_key": "SANDBOX_API_KEY_NOMIC",
}


def get_llm_config(model_name: str) -> dict:
    if model_name not in MODELS:
        print(f"Error: unknown model '{model_name}'. Options: {', '.join(MODELS.keys())}")
        sys.exit(1)
    config = MODELS[model_name]
    api_key = os.environ.get(config["env_key"])
    if not api_key:
        print(f"Error: {config['env_key']} environment variable not set")
        sys.exit(1)
    return {**config, "api_key": api_key}


def llm_completion(config: dict, messages: list[dict], temperature: float = 0, **kwargs) -> "litellm.ModelResponse":
    return litellm.completion(
        model=config["litellm_model"],
        messages=messages,
        temperature=temperature,
        api_key=config["api_key"],
        api_base=config["api_base"],
        **config.get("extra_params", {}),
        **kwargs,
    )


def get_embed_client() -> tuple[OpenAI, str]:
    embed_key = os.environ.get(EMBED_CONFIG["env_key"])
    if not embed_key:
        print(f"Error: {EMBED_CONFIG['env_key']} environment variable not set")
        sys.exit(1)
    client = OpenAI(
        api_key=embed_key,
        base_url=EMBED_CONFIG["base_url"],
        http_client=httpx.Client(verify=False),
    )
    return client, EMBED_CONFIG["model"]
