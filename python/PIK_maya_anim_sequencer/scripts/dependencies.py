def valid_shot_name(name: str) -> str:
    """Check if the shot name is valid."""
    error = ValueError("Invalid shot name")

    seq, shot = name.split("_")

    if not seq.startswith("SQ") or not shot.startswith("SH"):
        raise error
    if not seq[2:].isdigit() or not shot[2:].isdigit():
        raise error

    return name
