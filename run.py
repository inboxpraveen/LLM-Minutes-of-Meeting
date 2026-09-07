import os

from app import create_app

app = create_app()


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))

    if _flag("FLASK_DEBUG"):
        app.run(host=host, port=port, debug=True)
    else:
        from waitress import serve

        print(f"MoM AI is running on http://localhost:{port}")
        # The real upload limit is the one set in Settings; keep waitress out of the way.
        serve(app, host=host, port=port, threads=8, channel_timeout=3600,
              max_request_body_size=64 * 1024 ** 3)
