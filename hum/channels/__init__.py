from ..channel import Channel
from .http import HttpChannel
from .stdin import StdinChannel

_REGISTRY = {
    "http": HttpChannel,
    "stdin": StdinChannel,
}


def build_channel(config: dict) -> Channel:
    kind = config.get("type")
    if kind not in _REGISTRY:
        known = ", ".join(f"'{t}'" for t in _REGISTRY)
        raise ValueError(f"unknown channel type '{kind}' — known types: {known}")
    return _REGISTRY[kind](config)
