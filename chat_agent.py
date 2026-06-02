#!/usr/bin/env python3
"""Simple CLI chat agent for basic tech support prompts."""

from __future__ import annotations


RESPONSES = {
    "password": "Try resetting your password from the account settings page, then sign out and in again.",
    "wifi": "Please restart your router, confirm the cable is connected, and reconnect to the network.",
    "internet": "Check if other devices can connect. If not, restart your modem/router and test again.",
    "slow": "Close heavy applications, restart your machine, and ensure updates are not running in the background.",
    "printer": "Confirm the printer is powered on, connected to the network, and set as your default printer.",
    "install": "Verify you have enough disk space and administrator permissions, then retry the installation.",
}


def get_reply(user_message: str) -> str:
    normalized = user_message.lower()
    for keyword, response in RESPONSES.items():
        if keyword in normalized:
            return response
    return "I can help with password, internet, printer, speed, or install issues. Could you share more details?"


def run_chat() -> None:
    print("Tech Support Agent is running. Type 'exit' to quit.")
    while True:
        user_message = input("You: ").strip()
        if user_message.lower() in {"exit", "quit"}:
            print("Agent: Goodbye!")
            break
        if not user_message:
            print("Agent: Please describe the issue you're facing.")
            continue
        print(f"Agent: {get_reply(user_message)}")


if __name__ == "__main__":
    run_chat()
