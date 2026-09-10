"""PyWebView desktop shell. Loads the React frontend and exposes backend.api.Api
to JS via the pywebview js_api bridge.

Dev mode:  python main.py --dev   (points at Vite dev server, http://localhost:5173)
Prod mode: python main.py         (points at frontend/dist/index.html)
"""

import argparse
import os

import webview

from backend.api import Api

DEV_URL = "http://localhost:5180"
PROD_INDEX = os.path.join(os.path.dirname(__file__), "frontend", "dist", "index.html")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Load the Vite dev server instead of the built frontend")
    args = parser.parse_args()

    dev_mode = args.dev or os.environ.get("BRAIN_RAG_ENV") == "dev"
    url = DEV_URL if dev_mode else PROD_INDEX

    api = Api()
    webview.create_window(
        "Memstra", url, js_api=api, width=1000, height=700,
        background_color="#0b0b0c",
    )
    webview.start(debug=dev_mode)


if __name__ == "__main__":
    main()
