import os
import ssl
import sys
import time
import uuid

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
        "litellm_model": "vertex/claude-haiku-4-5@20251001",
        "api_base": "https://claude--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443",
        "env_key": "SANDBOX_API_KEY_CLAUDE",
        "extra_params": {},
        "custom_handler": "vertex_anthropic",
        "vertex_path": "haiku",
    },
    "granite-4-1-8b": {
        "litellm_model": "openai/ibm-granite/granite-4.1-8b",
        "api_base": "https://granite-4-1-8b--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443/v1",
        "env_key": "SANDBOX_API_KEY_GRANITE41",
        "extra_params": {},
    },
    "gpt-oss-20b": {
        "litellm_model": "openai/openai/gpt-oss-20b",
        "api_base": "https://gpt-oss-20b--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443/v1",
        "env_key": "SANDBOX_API_KEY_GPTOSS",
        "extra_params": {},
    },
    "gemini-flash": {
        "litellm_model": "vertex_ai/gemini-2.0-flash",
        "api_base": None,
        "env_key": "VERTEXAI_PROJECT",
        "extra_params": {},
        "vertex_ai_native": True,
    },
}

EMBED_CONFIG = {
    "model": "nomic-ai/nomic-embed-text-v1.5",
    "base_url": "https://nomic-embed-text-v1-5--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com/v1",
    "env_key": "SANDBOX_API_KEY_NOMIC",
}


def get_llm_config(model_name: str, required: bool = True) -> dict | None:
    if model_name not in MODELS:
        if required:
            print(f"Error: unknown model '{model_name}'. Options: {', '.join(MODELS.keys())}")
            sys.exit(1)
        return None
    config = MODELS[model_name]
    api_key = os.environ.get(config["env_key"])
    if not api_key:
        if required:
            print(f"Error: {config['env_key']} environment variable not set")
            sys.exit(1)
        return None
    return {**config, "api_key": api_key}


def _vertex_anthropic_completion(config: dict, messages: list[dict], temperature: float = 0, **kwargs) -> litellm.ModelResponse:
    model_id = config["litellm_model"].split("/", 1)[1]
    vertex_path = config.get("vertex_path", "opus")
    url = f"{config['api_base']}/{vertex_path}/models/{model_id}:streamRawPredict"

    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    chat_messages = [m for m in messages if m["role"] != "system"]

    body = {
        "anthropic_version": "vertex-2023-10-16",
        "messages": chat_messages,
        "max_tokens": kwargs.get("max_tokens", 1024),
        "temperature": temperature,
    }
    if system_parts:
        body["system"] = "\n".join(system_parts)

    # n > 1 not supported — run multiple requests
    n = kwargs.get("n", 1)
    kwargs.pop("n", None)
    kwargs.pop("max_tokens", None)
    kwargs.pop("logprobs", None)
    kwargs.pop("extra_body", None)

    with httpx.Client(verify=False, timeout=120) as client:
        choices = []
        total_prompt = 0
        total_completion = 0

        for i in range(n):
            for attempt in range(6):
                resp = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {config['api_key']}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if resp.status_code == 429:
                    wait = min(2 ** attempt, 60)
                    retry_after = resp.headers.get("retry-after")
                    if retry_after:
                        try:
                            wait = max(wait, float(retry_after))
                        except ValueError:
                            pass
                    print(f"    Rate limited, retrying in {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                break
            else:
                resp.raise_for_status()

            text = ""
            input_tokens = 0
            output_tokens = 0
            stop_reason = "end_turn"

            content_type = resp.headers.get("content-type", "")
            if "text/event-stream" in content_type or resp.text.startswith("event:"):
                import json as _json
                for line in resp.text.splitlines():
                    if not line.startswith("data: "):
                        continue
                    chunk = _json.loads(line[6:])
                    chunk_type = chunk.get("type")
                    if chunk_type == "content_block_delta":
                        delta = chunk.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text += delta.get("text", "")
                    elif chunk_type == "message_start":
                        msg = chunk.get("message", {})
                        usage = msg.get("usage", {})
                        input_tokens = usage.get("input_tokens", 0)
                    elif chunk_type == "message_delta":
                        delta = chunk.get("delta", {})
                        stop_reason = delta.get("stop_reason", stop_reason)
                        usage = chunk.get("usage", {})
                        output_tokens = usage.get("output_tokens", 0)
            else:
                data = resp.json()
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text += block["text"]
                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                stop_reason = data.get("stop_reason", "end_turn")

            choices.append(litellm.Choices(
                index=i,
                message=litellm.Message(role="assistant", content=text.strip()),
                finish_reason=stop_reason,
            ))
            total_prompt += input_tokens
            total_completion += output_tokens

    return litellm.ModelResponse(
        id=f"vertex-{uuid.uuid4().hex[:8]}",
        choices=choices,
        model=model_id,
        usage=litellm.Usage(
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            total_tokens=total_prompt + total_completion,
        ),
    )


def llm_completion(config: dict, messages: list[dict], temperature: float = 0, **kwargs) -> litellm.ModelResponse:
    if config.get("custom_handler") == "vertex_anthropic":
        return _vertex_anthropic_completion(config, messages, temperature, **kwargs)

    extra_params = dict(config.get("extra_params", {}))
    if "extra_body" in kwargs and "extra_body" in extra_params:
        extra_params["extra_body"] = {**extra_params["extra_body"], **kwargs.pop("extra_body")}

    call_kwargs = {
        "model": config["litellm_model"],
        "messages": messages,
        "temperature": temperature,
        **extra_params,
        **kwargs,
    }
    if config.get("vertex_ai_native"):
        call_kwargs["vertex_project"] = config["api_key"]
        call_kwargs["vertex_location"] = os.environ.get("VERTEXAI_LOCATION", "us-central1")
    else:
        call_kwargs["api_key"] = config["api_key"]
        call_kwargs["api_base"] = config["api_base"]

    return litellm.completion(**call_kwargs)


_embed_cache: dict[tuple, list[list[float]]] = {}


def embed_texts(client, texts: list[str], model: str) -> list[list[float]]:
    key = (tuple(texts), model)
    if key in _embed_cache:
        return _embed_cache[key]
    result = client.embeddings.create(model=model, input=texts).data
    vecs = [d.embedding for d in result]
    _embed_cache[key] = vecs
    return vecs


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
