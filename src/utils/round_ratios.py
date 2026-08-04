def round_ratio(ratio: int | float) -> int:
    if type(ratio) == int:
        return int(ratio)

    if ratio % 10 <= 5:
        return int(ratio - ratio % 10)
    else:
        return int(ratio + (10 - ratio % 10))
