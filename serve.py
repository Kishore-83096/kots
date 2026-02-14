
import os

from waitress import serve

from wsgi import app


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    threads = int(os.getenv("WAITRESS_THREADS", "8"))
    print(f"Waitress serving on http://{host}:{port} (threads={threads})", flush=True)
    serve(app, host=host, port=port, threads=threads)
