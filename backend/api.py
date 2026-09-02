"""Python side of the JS <-> Python bridge. Methods on Api are called directly
from React via window.pywebview.api.<method>() — no HTTP server involved.
"""

from agent import handle_message


class Api:
    def ping(self):
        return "pong"

    def send_message(self, text):
        try:
            result = handle_message(text)
            return result if result is not None else ""
        except Exception as e:
            return f"Error: {e}"
