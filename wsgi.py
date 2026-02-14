"""
WSGI entry point for production servers (gunicorn/uwsgi/mod_wsgi).
"""

from app import create_app


app = create_app()
application = app

