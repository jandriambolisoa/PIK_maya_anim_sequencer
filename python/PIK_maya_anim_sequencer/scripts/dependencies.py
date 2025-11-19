def valid_shot_name(name: str) -> str:
    """
    Return the shot name if the given name is valid.
    Args:
        name (str): The name of the shot.

    Returns:
        str: The shot name.
    """
    seq, shot = name.split("_")

    if not seq.startswith("SQ") or not shot.startswith("SH"):
        raise ValueError(
            "Invalid shot name. Sequence must start with 'SQ' and shot must start with 'SH'. The expected format is SQ0010_SH0010."
        )
    if not seq[2:].isdigit() or not shot[2:].isdigit():
        raise ValueError(
            "Unexpected characters. Shot name must be in the format 'SQXXXX_SHXXXX' where 'X' are digits."
        )

    return name
