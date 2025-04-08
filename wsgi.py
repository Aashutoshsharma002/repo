"""
WSGI adapter for FastAPI application.
This file serves as a bridge between Gunicorn (WSGI server) and FastAPI (ASGI application).
"""
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("wsgi_adapter")

# Import main app
from main import app as fastapi_app

# Create the WSGI app
def create_app():
    try:
        # Import here to prevent import errors
        from asgiref.wsgi import WsgiToAsgi
        
        # FastAPI is an ASGI app but Gunicorn is WSGI
        # Use asgiref adapter to convert
        wsgi_app = WsgiToAsgi(fastapi_app)
        return wsgi_app
    except ImportError as e:
        logger.error(f"Failed to import asgiref: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating WSGI adapter: {e}")
        raise

# Create an app instance that Gunicorn will use
app = create_app()

# For direct Uvicorn execution if file is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5000, log_level="debug")