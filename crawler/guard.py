"""Makes it impossible for this process to open the hidden answer key.

Python calls an "audit hook" on every file open. Ours raises an error if the path is
inside answer_key/, so a bug can't quietly let the crawler peek at the answers.
"""

import os
import sys

from .settings import ANSWER_KEY_DIR

_FORBIDDEN = os.path.realpath(ANSWER_KEY_DIR)


class AnswerKeyAccessError(PermissionError):
    pass


def _hook(event, args):
    if event in ("open", "os.listdir", "os.scandir") and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.path.realpath(os.fsdecode(args[0]))
        if path == _FORBIDDEN or path.startswith(_FORBIDDEN + os.sep):
            raise AnswerKeyAccessError(f"The crawler must never read the answer key: {path}")


def install():
    """Turn the guard on for the rest of this process (it cannot be turned off again)."""
    sys.addaudithook(_hook)
