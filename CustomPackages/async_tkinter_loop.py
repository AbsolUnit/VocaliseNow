import _tkinter
import sys
import asyncio
import customtkinter
from functools import wraps
from typing import Any, Callable, Coroutine

from tkinter import TclError


async def main_loop(root: customtkinter.CTk) -> None:
    """
    An asynchronous implementation of tkinter mainloop
    :param root: tkinter root object
    :return: nothing
    """
    while True:
        # Process all pending events
        while root.tk.dooneevent(_tkinter.DONT_WAIT) > 0:
            if not root._window_exists:
                if sys.platform.startswith("win"):
                    root._windows_set_titlebar_color(root._get_appearance_mode())

                    if not root._withdraw_called_before_window_exists and not root._iconify_called_before_window_exists:
                        # print("window dont exists -> deiconify in mainloop")
                        root.deiconify()

                root._window_exists = True

        try:
            root.winfo_exists()  # Will throw TclError if the main window is destroyed
        except TclError:
            break

        await asyncio.sleep(0.01)


def _get_event_loop() -> asyncio.AbstractEventLoop:
    """
    A helper function to get event loop using current event loop policy
    :return: event loop
    """
    return asyncio.get_event_loop_policy().get_event_loop()


def async_mainloop(root: customtkinter.CTk) -> None:
    """
    A synchronous function to run asynchronous main_loop function
    :param root: tkinter root object
    :return: nothing
    """
    _get_event_loop().run_until_complete(main_loop(root))


def async_handler(async_function: Callable[..., Coroutine[Any, Any, None]], *args, **kwargs) -> Callable[..., None]:
    """
    Helper function to pass async functions as command handlers (e.g. button click handlers) or event handlers

    :param async_function: async function
    :param args: positional parameters which will be passed to the async function
    :param kwargs: keyword parameters which will be passed to the async function
    :return: function

    Examples: ::

        async def some_async_function():
            print("Wait...")
            await asyncio.sleep(0.5)
            print("Done!")

        button = tk.Button("Press me", command=async_handler(some_async_function))

        # ----

        async def some_async_function(event):
            print("Wait...")
            await asyncio.sleep(0.5)
            print("Done!")

        root.bind("<1>", command=async_handler(some_async_function))

        # ----

        # Also, it can be used as a decorator
        @async_handler
        async def some_async_function():
            print("Wait...")
            await asyncio.sleep(0.5)
            print("Done!")

        button = tk.Button("Press me", command=some_async_function)
    """

    @wraps(async_function)
    def wrapper(*handler_args) -> None:
        _get_event_loop().create_task(async_function(*handler_args, *args, **kwargs))

    return wrapper
