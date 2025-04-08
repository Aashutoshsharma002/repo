"""
This script starts the FastAPI application using uvicorn.
"""
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    # Run the app with Uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)