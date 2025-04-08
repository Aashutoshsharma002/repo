#!/bin/bash
# Start the application using Gunicorn with the WSGI adapter for FastAPI
exec gunicorn -c gunicorn_conf.py gunicorn_wsgi:application