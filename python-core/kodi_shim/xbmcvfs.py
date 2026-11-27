# -*- coding: utf-8 -*-
import os
import shutil
from xbmc import translatePath


def exists(path: str) -> bool:
    return os.path.exists(translatePath(path))


def copy(source: str, destination: str) -> bool:
    try:
        shutil.copy2(translatePath(source), translatePath(destination))
        return True
    except Exception:
        return False


def delete(path: str) -> bool:
    try:
        p = translatePath(path)
        if os.path.exists(p):
            os.remove(p)
        return True
    except Exception:
        return False


class File:
    def __init__(self, filepath: str, mode: str = "r"):
        self._path = translatePath(filepath)
        self._mode = mode
        if "w" in mode:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            self._f = open(self._path, mode)
        else:
            self._f = open(self._path, "rb" if "b" in mode else "r")

    def read(self, size: int = -1):
        return self._f.read(size)

    def write(self, data):
        return self._f.write(data)

    def close(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
