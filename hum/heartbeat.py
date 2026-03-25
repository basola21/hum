import re


def parse_interval(interval: str) -> float:
    match = re.fullmatch(r"(\d+)(s|m|h|d)", interval)
    if not match:
        raise ValueError(f"Invalid interval '{interval}'. Use e.g. '30s', '10m', '1h'.")
    value, unit = int(match.group(1)), match.group(2)
    return value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
