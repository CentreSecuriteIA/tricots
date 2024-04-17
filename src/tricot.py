"""
TRICOT: Trace Interception and Collection Tool

This single file module is a monkey-patch for the openai api that enables:
- Logging of all calls to the openai api
- Modification of the messages sent to the api before sending them

TRICOT contains two main functions:
- `patch_openai(edit_call)`: Patches the openai api to add logging, with an optional function to edit the list of messages before sending them.
- `new_log_file(path)`: Sets the log file to use, should be before each individual run of the LLM-app to monitor.

---
MIT License

Copyright (c) 2024 Diego Dorn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import json
import time
import logging
from functools import partial
from copy import deepcopy

import openai
from typing import Callable

OPENAI_IS_PRE_1_0_0 = openai.__version__.split(".")[0] == "0"

if OPENAI_IS_PRE_1_0_0:
    original_chat_completion_create = openai.ChatCompletion.create
    ChatCompletionMessage = dict[str, str]
else:
    from openai.types.chat import ChatCompletionMessage

    original_chat_completion_create = openai.chat.completions.create


def create_and_log(
    *,
    messages: list,
    edit_call: Callable[[list[ChatCompletionMessage]], list[ChatCompletionMessage]] = None,
    **kwargs,
):
    if edit_call is not None:
        messages = deepcopy(messages)
        messages = edit_call(messages)

    logger = logging.getLogger("TRICOT")
    now = time.time()

    response = original_chat_completion_create(messages=messages, **kwargs)

    messages = [*messages, dict(response["choices"][0]["message"])]
    logger.info(
        json.dumps(
            {
                "timestamp": now,
                "messages": messages,
            }
        )
    )
    return response


def patch_openai(edit_call: Callable[[list[dict[str, str]]], list[dict[str, str]]] = None):
    """Patch the openai api to add logging. This should be called before any calls to the openai api.

    If `edit_call` is provided, it will be called with the list of messages before sending its result to the api.
    `edit_call` should return the edited list of messages.

    It is safe to call this function multiple times, it will replace the previous patch (and previous `edit_call`)
    """

    new = partial(create_and_log, edit_call=edit_call)

    if OPENAI_IS_PRE_1_0_0:
        openai.ChatCompletion.create = new
    else:
        openai.chat.completions.create = new


def new_log_file(path: str = None):
    """Set the log file for the supervisor logger. If `path` is None, logs into logs/{timestamp}.log."""
    if path is None:
        path = f"logs/{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"

    logger = logging.getLogger("TRICOT")
    logger.setLevel(logging.INFO)
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
    logger.addHandler(logging.FileHandler(path))
