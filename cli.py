#!/usr/bin/env python3
"""Command-line interface for the LLM Service."""
import sys
import argparse
import json
import asyncio
from typing import Optional

from services.chat import chat_service
from api.models import ChatRequest, ChatResponse


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LLM Service CLI - Interact with the LLM service from command line"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # Chat command
    chat_parser = subparsers.add_parser(
        "chat",
        help="Send a chat message to the LLM"
    )
    chat_parser.add_argument(
        "-m", "--message",
        required=True,
        help="Message to send to the LLM"
    )
    chat_parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output result in JSON format"
    )
    
    return parser.parse_args()


async def process_chat_message(
    message: str,
    output_json: bool = False
) -> int:
    """
    Process chat message and output result.
    
    Args:
        message: Message to send to LLM
        output_json: Whether to output in JSON format
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Create request
        request = ChatRequest(message=message)
        
        # Process request
        response = chat_service.process_request(request)
        
        if output_json:
            # Output as JSON
            output = {
                "model": response.model,
                "price": response.price
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            # Output as formatted text
            print("=" * 60)
            print("LLM Service Response")
            print("=" * 60)
            print(f"Model:   {response.model}")
            print(f"Price:   {response.price}")
            print("=" * 60)
        
        return 0
        
    except Exception as e:
        if output_json:
            output = {
                "success": False,
                "error": str(e),
                "message": "Failed to process request"
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"Error: {str(e)}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for CLI.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        args = parse_arguments()
        
        if args.command == "chat":
            return asyncio.run(process_chat_message(
                message=args.message,
                output_json=args.json
            ))
        else:
            # No command provided, show help
            parser = argparse.ArgumentParser(
                description="LLM Service CLI - Interact with the LLM service from command line"
            )
            parse_arguments()  # This will print help and exit
            return 0
            
    except SystemExit as e:
        # argparse calls sys.exit on error or --help
        return e.code if isinstance(e.code, int) else 0
    except Exception as e:
        print(f"CLI Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
