"""Entry point to run the RAG Policy Assistant."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="RAG Policy Assistant")
    parser.add_argument(
        "--index",
        action="store_true",
        help="Build/rebuild the document index",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the web server",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run the evaluation suite",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the server on (default: 5000)",
    )

    args = parser.parse_args()

    if not any([args.index, args.serve, args.evaluate]):
        parser.print_help()
        sys.exit(1)

    if args.index:
        print("Building document index...")
        from app.ingestion import build_index
        build_index()
        print("Index built successfully!")

    if args.evaluate:
        print("Running evaluation...")
        from evaluation.evaluate import main as eval_main
        eval_main()

    if args.serve:
        print(f"Starting server on {args.host}:{args.port}...")
        from app.web import app
        app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
