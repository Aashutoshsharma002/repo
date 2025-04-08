#!/bin/bash
# Start the application using uvicorn directly
exec uvicorn asgi:app --host 0.0.0.0 --port 5000 --reload