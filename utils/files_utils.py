import random
import json
import os
from typing import Optional, Union


def join_path(path: Union[str, tuple, list]) -> str:
    if isinstance(path, str):
        return path

    return os.path.join(*path)


def read_json(path: Union[str, tuple, list], encoding: Optional[str] = None) -> Union[list, dict]:
    path = join_path(path)
    return json.load(open(path, encoding=encoding))


def read_lines(path: Union[str, tuple, list], skip_empty_rows: bool = True, encoding: Optional[str] = 'utf-8') -> list:
    path = join_path(path)
    with open(path, encoding=encoding) as f:
        lines = f.readlines()

    lines = [line.rstrip() for line in lines]
    if skip_empty_rows:
        lines = list(filter(lambda a: a, lines))

    return lines


def select_random_proxy(path: str) -> Optional[str]:
    proxies = read_lines(path=path)
    if not proxies:
        return None
    return random.choice(proxies)
