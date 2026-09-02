# Brain-Rag Desktop

A PyWebView desktop shell around the Brain-Rag backend. React (Vite) handles the
UI; a Python `Api` class is exposed directly to JS via PyWebView's `js_api`
bridge — no HTTP server, no FastAPI/Flask.

```
/
├── frontend/          Vite + React app (the chat terminal UI)
│   ├── src/
│   └── dist/          build output — PyWebView points here in production
├── backend/
│   └── api.py         Api class exposed to JS (ping, send_message)
├── main.py            creates the PyWebView window
├── agent.py           existing RAG agent logic (unchanged, now returns instead of prints)
└── requirements.txt
```

## Dev mode

Two terminals:

```bash
# Terminal 1 — Vite dev server (hot reload)
cd frontend
npm install   # first time only
npm run dev

# Terminal 2 — PyWebView shell pointed at the dev server
python main.py --dev
```

## Production build

```bash
cd frontend
npm run build       # outputs frontend/dist/

cd ..
python main.py       # loads frontend/dist/index.html
```

## Setup

```bash
pip install -r requirements.txt
```

### Linux note

This machine has no PyWebView GUI backend installed (no GTK/WebKit2GTK
`python-gobject` bindings, no PyQt). `python main.py` will fail to open an
actual window until one is installed — that's a system package (e.g. via
`pacman -S python-gobject webkit2gtk`), not something `pip` can provide.
This does **not** affect the eventual Windows/MSIX target, since PyWebView
uses the built-in Edge WebView2 runtime there automatically.

## Next steps (not implemented yet)

- [ ] PyInstaller: freeze `main.py` + `frontend/dist` into a single executable
- [ ] MSIX packaging for Microsoft Store distribution
- [ ] App icon / window branding
