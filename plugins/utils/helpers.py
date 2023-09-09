import re
from typing import Tuple


def extract_float(text: str) -> float:
    value = re.search(r"(\d+\.\d+|\d+)", text)
    return float(value.group(1))


def extract_integer(text: str) -> int:
    return int("".join(filter(str.isdigit, text)))


def split_address(address: str) -> Tuple[str, str, str]:
    city_state, zip_code = address.rsplit(" ", 1)
    city, state = city_state.rsplit(",", 1)

    return city.strip(), state.strip(), zip_code.strip()
