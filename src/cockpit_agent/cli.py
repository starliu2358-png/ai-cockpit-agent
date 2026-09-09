from __future__ import annotations

from .agent import run_agent


def main() -> None:
    print("AI Cockpit Agent CLI. Type 'exit' to quit.")
    while True:
        message = input("you> ").strip()
        if message.lower() in {"exit", "quit"}:
            break
        if message:
            print("agent>", run_agent(message))


if __name__ == "__main__":
    main()
