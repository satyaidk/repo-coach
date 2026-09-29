"""`python -m repocompass` starts the web app."""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RepoCompass web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="restart on code changes (for development)")
    args = parser.parse_args()
    print(f"RepoCompass API running at http://{args.host}:{args.port} (docs at /docs)")
    print("Start the UI with `npm run dev` in the frontend/ folder, then open http://localhost:3000")
    uvicorn.run("repocompass.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
