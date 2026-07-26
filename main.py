#!/usr/bin/env python3
"""Main entry point for the LLM Service."""
import os
import sys
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging with file and console output
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create logger
logger = logging.getLogger('llm_service')
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# File handler with rotation
log_file = os.getenv('LOG_FILE', 'app.log')
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# Suppress verbose logs from external libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('uvicorn').setLevel(logging.WARNING)
logging.getLogger('starlette').setLevel(logging.WARNING)

app = FastAPI(
    title="LLM Service",
    description="API service for LLM operations",
    version="1.0.0"
)

# Import and include API router
from api import router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {"message": "LLM Service is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


async def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server"""
    logger.info(f"Starting LLM Service on {host}:{port}...")
    import uvicorn
    uvicorn.run(app, host=host, port=port)


def run_cli():
    """Run CLI commands"""
    import sys
    from cli import main as cli_main
    sys.exit(cli_main())


async def main():
    """Main application entry point"""
    logger.info("Starting LLM Service...")
    # Application startup logic here
    pass


if __name__ == "__main__":
    # Check if CLI mode is requested by checking for 'chat' subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        run_cli()
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
