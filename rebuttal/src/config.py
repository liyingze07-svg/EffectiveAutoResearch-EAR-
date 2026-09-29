"""Shared config: load .env and build DSPy LMs for multiple backbone models.

Model registry maps a short key -> (litellm model id, provider, params). get_lm()
resolves the provider's API key from .env and raises a clear error if it's missing,
so the multi-model comparison can skip un-keyed models gracefully.
"""
import os
import dspy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    env = {}
    path = os.path.join(ROOT, ".env")
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    # also honor process env (e.g. keys exported at runtime)
    for k in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


# key -> dict(model=litellm id, provider, key_env, extra params)
MODELS = {
    "deepseek-v4-pro":   dict(model="openai/deepseek-v4-pro",   provider="deepseek", max_tokens=6000),
    "deepseek-v4-flash": dict(model="openai/deepseek-v4-flash", provider="deepseek", max_tokens=6000),
    "opus-4.8":          dict(model="anthropic/claude-opus-4-8", provider="anthropic", max_tokens=4096),
    "opus-4.7":          dict(model="anthropic/claude-opus-4-7", provider="anthropic", max_tokens=4096),
    "sonnet-5":          dict(model="anthropic/claude-sonnet-5", provider="anthropic", max_tokens=4096),
}

PROVIDER_KEY = {
    "deepseek": "DEEPSEEK_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def available_models(env=None):
    env = env or load_env()
    out = []
    for key, spec in MODELS.items():
        if env.get(PROVIDER_KEY[spec["provider"]]):
            out.append(key)
    return out


def get_lm(model_key="deepseek-v4-pro", temperature=0.0, cache=True):
    env = load_env()
    spec = MODELS[model_key]
    keyname = PROVIDER_KEY[spec["provider"]]
    api_key = env.get(keyname)
    if not api_key:
        raise RuntimeError(f"missing {keyname} for model '{model_key}'")
    kwargs = dict(api_key=api_key, max_tokens=spec["max_tokens"],
                  temperature=temperature, cache=cache)
    if spec["provider"] == "deepseek":
        kwargs["api_base"] = env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return dspy.LM(spec["model"], **kwargs)
