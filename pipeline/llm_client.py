"""Unified LLM client using LiteLLM for routing and cost tracking."""

from dataclasses import dataclass, field
import os

import litellm

import dotenv

dotenv.load_dotenv()

DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.6-plus"


class LLMError(Exception):
    """Unified error for LLM API failures."""
    pass


@dataclass
class LLMUsage:
    """Token usage and cost for an LLM call (or accumulated across calls)."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    def __add__(self, other: "LLMUsage") -> "LLMUsage":
        return LLMUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
        )

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
        }


@dataclass
class LLMResponse:
    """Response from an LLM call, including text, usage, and model info."""
    text: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""


def _dashscope_base_name(model: str) -> str:
    """Strip a leading ``openai/`` routing prefix to get the raw model id."""
    return model.split("/", 1)[1] if model.startswith("openai/") else model


def _is_dashscope_model(model: str) -> bool:
    # Any DashScope-hosted Qwen model (e.g. qwen3.6-plus, qwen3.6-flash),
    # with or without the LiteLLM ``openai/`` routing prefix.
    return _dashscope_base_name(model).startswith("qwen")


def _is_anthropic_model(model: str) -> bool:
    return model.startswith("anthropic/") or "claude" in model


def _completion_model_name(model: str) -> str:
    if _is_dashscope_model(model):
        # LiteLLM routes OpenAI-compatible providers through the openai prefix.
        # Preserve the requested model id rather than forcing the default.
        return f"openai/{_dashscope_base_name(model)}"
    if _is_anthropic_model(model) and not model.startswith("anthropic/"):
        # Force the anthropic/ prefix so LiteLLM routes to the Anthropic API
        # even for model IDs not yet in its registry (e.g. claude-sonnet-4-6).
        return f"anthropic/{model}"
    return model


def _is_openai_model(model: str) -> bool:
    completion_model = _completion_model_name(model)
    return any(completion_model.startswith(p) for p in ("gpt-", "o1-", "o3-", "o4-", "openai/"))


def chat(messages: list[dict], model: str = DEFAULT_MODEL, max_tokens: int = 4096) -> LLMResponse:
    """Send messages to an LLM and return the response with usage/cost info.

    Routes to the appropriate provider via LiteLLM.
    Requires the relevant provider API key in the environment, including
    `DASHSCOPE_API_KEY` for the default DashScope-hosted Qwen model.
    """
    # LiteLLM uses max_tokens for Anthropic, max_completion_tokens for OpenAI
    kwargs: dict = {"model": _completion_model_name(model), "messages": messages}
    if _is_dashscope_model(model):
        kwargs["api_base"] = DASHSCOPE_BASE_URL
        kwargs["api_key"] = os.environ.get("DASHSCOPE_API_KEY")
    elif _is_anthropic_model(model):
        kwargs["api_key"] = os.environ.get("ANTHROPIC_API_KEY")
    if _is_openai_model(model):
        kwargs["max_completion_tokens"] = max_tokens
    else:
        kwargs["max_tokens"] = max_tokens

    try:
        response = litellm.completion(**kwargs)
    except litellm.exceptions.APIError as e:
        raise LLMError(str(e)) from e
    except Exception as e:
        raise LLMError(str(e)) from e

    text = response.choices[0].message.content or ""

    # Extract usage
    usage = LLMUsage()
    if response.usage:
        usage.prompt_tokens = response.usage.prompt_tokens or 0
        usage.completion_tokens = response.usage.completion_tokens or 0
        usage.total_tokens = response.usage.total_tokens or 0

    # Extract cost from LiteLLM's hidden params
    try:
        cost = response._hidden_params.get("response_cost", 0.0)
        if cost is not None:
            usage.cost_usd = float(cost)
    except Exception:
        # If cost extraction fails, try completion_cost as fallback
        try:
            usage.cost_usd = float(litellm.completion_cost(completion_response=response))
        except Exception:
            pass

    return LLMResponse(text=text, usage=usage, model=model)
