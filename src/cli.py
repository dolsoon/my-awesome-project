"""
Command-Line Interface for AI Facilitator Agent
Main entry point for researchers to interact with the system
"""

import re
import sys
from typing import Optional


def extract_doc_id(url_or_id: str) -> Optional[str]:
    """
    Extract Google Docs document ID from URL or return ID directly

    Supports formats:
    - https://docs.google.com/document/d/DOCUMENT_ID/edit
    - https://docs.google.com/document/d/DOCUMENT_ID
    - DOCUMENT_ID (direct ID)
    """
    # Pattern to match Google Docs URLs
    url_pattern = r'docs\.google\.com/document/d/([a-zA-Z0-9-_]+)'

    match = re.search(url_pattern, url_or_id)
    if match:
        return match.group(1)

    # If no URL pattern found, assume it's a direct document ID
    # Google Docs IDs are typically 44 characters of alphanumeric + hyphens/underscores
    if re.match(r'^[a-zA-Z0-9-_]{20,}$', url_or_id):
        return url_or_id

    return None


def print_header():
    """Print application header"""
    print()
    print("=" * 70)
    print("  AI Facilitator Agent - Google Docs Collaboration Assistant")
    print("=" * 70)
    print()


def print_help():
    """Print available commands"""
    print()
    print("Available Commands:")
    print("-" * 70)
    print("  watch <url>         Register a Google Docs URL for monitoring")
    print("                      Example: watch https://docs.google.com/document/d/...")
    print()
    print("  list                List all watched documents")
    print()
    print("  mode <type>         Switch agent mode")
    print("                      Types: outlier, summary, connect, question")
    print()
    print("  analyze [mode]      Trigger analysis (optional: specify mode)")
    print()
    print("  status              Show current status and configuration")
    print()
    print("  import <file>       Import context file (.txt)")
    print("  context             List imported context files")
    print()
    print("  auto <interval>     Enable automatic mode (30, 60, or 120 seconds)")
    print("  manual              Switch to manual mode")
    print()
    print("  help                Show this help message")
    print("  exit                Exit the application")
    print("-" * 70)
    print()


def main():
    """Main CLI loop"""
    print_header()

    print("Welcome to the AI Facilitator Agent!")
    print()
    print("This tool helps facilitate Google Docs collaboration using AI.")
    print()
    print("⚠️  Setup Required:")
    print("  1. Configure your .env file with API keys (see .env.example)")
    print("  2. Set up Google OAuth credentials")
    print("  3. Configure production settings in config/production.yaml")
    print()
    print("Type 'help' for available commands or 'exit' to quit.")
    print()

    # Simulated state (in production, this would use real services)
    watched_docs = []
    current_mode = "outlier"
    auto_mode = False
    auto_interval = 60

    while True:
        try:
            # Display prompt with current mode
            mode_indicator = f"[{current_mode.upper()}]"
            auto_indicator = f" AUTO:{auto_interval}s" if auto_mode else " MANUAL"
            prompt = f"{mode_indicator}{auto_indicator} > "

            command = input(prompt).strip()

            if not command:
                continue

            parts = command.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None

            # Handle commands
            if cmd == "help":
                print_help()

            elif cmd == "watch":
                if not arg:
                    print("❌ Error: Please provide a Google Docs URL or document ID")
                    print("   Usage: watch <url>")
                    print("   Example: watch https://docs.google.com/document/d/ABC123...")
                else:
                    doc_id = extract_doc_id(arg)
                    if doc_id:
                        watched_docs.append({
                            'id': doc_id,
                            'url': f"https://docs.google.com/document/d/{doc_id}",
                            'status': 'monitoring'
                        })
                        print(f"✅ Now watching document: {doc_id}")
                        print(f"   URL: https://docs.google.com/document/d/{doc_id}")
                        print(f"   Total watched documents: {len(watched_docs)}")
                    else:
                        print("❌ Error: Invalid Google Docs URL or document ID")
                        print("   Expected format: https://docs.google.com/document/d/...")

            elif cmd == "list":
                if not watched_docs:
                    print("📋 No documents are being watched.")
                    print("   Use 'watch <url>' to add a document.")
                else:
                    print(f"📋 Watching {len(watched_docs)} document(s):")
                    print()
                    for i, doc in enumerate(watched_docs, 1):
                        print(f"   {i}. {doc['id']}")
                        print(f"      URL: {doc['url']}")
                        print(f"      Status: {doc['status']}")
                        print()

            elif cmd == "mode":
                valid_modes = ["outlier", "summary", "connect", "question"]
                if not arg:
                    print(f"Current mode: {current_mode}")
                    print(f"Available modes: {', '.join(valid_modes)}")
                elif arg.lower() in valid_modes:
                    current_mode = arg.lower()
                    print(f"✅ Switched to {current_mode} mode")
                else:
                    print(f"❌ Error: Invalid mode '{arg}'")
                    print(f"   Available modes: {', '.join(valid_modes)}")

            elif cmd == "analyze":
                mode_to_use = arg.lower() if arg else current_mode
                if not watched_docs:
                    print("❌ Error: No documents are being watched.")
                    print("   Use 'watch <url>' to add a document first.")
                else:
                    print(f"🔍 Analyzing {len(watched_docs)} document(s) in {mode_to_use} mode...")
                    print("   (In production, this would trigger LLM analysis)")

            elif cmd == "status":
                print()
                print("📊 Current Status:")
                print(f"   Mode: {current_mode}")
                print(f"   Scheduling: {'Automatic (' + str(auto_interval) + 's)' if auto_mode else 'Manual'}")
                print(f"   Watched documents: {len(watched_docs)}")
                print(f"   Context files: 0 (use 'import' command)")
                print()

            elif cmd == "auto":
                if arg and arg in ["30", "60", "120"]:
                    auto_mode = True
                    auto_interval = int(arg)
                    print(f"✅ Automatic mode enabled ({auto_interval}s intervals)")
                else:
                    print("❌ Error: Invalid interval")
                    print("   Usage: auto <interval>")
                    print("   Valid intervals: 30, 60, 120")

            elif cmd == "manual":
                auto_mode = False
                print("✅ Switched to manual mode")

            elif cmd == "import":
                if not arg:
                    print("❌ Error: Please specify a file to import")
                    print("   Usage: import <file.txt>")
                else:
                    print(f"📁 Importing context file: {arg}")
                    print("   (In production, this would import the file)")

            elif cmd == "context":
                print("📚 No context files imported yet")
                print("   Use 'import <file.txt>' to add context")

            elif cmd in ["exit", "quit", "q"]:
                print()
                print("👋 Goodbye! Thanks for using AI Facilitator Agent.")
                print()
                sys.exit(0)

            else:
                print(f"❌ Unknown command: {cmd}")
                print("   Type 'help' for available commands")

        except KeyboardInterrupt:
            print()
            print()
            print("👋 Interrupted. Type 'exit' to quit or continue using commands.")
            print()

        except EOFError:
            print()
            print()
            print("👋 Goodbye!")
            print()
            sys.exit(0)


if __name__ == "__main__":
    main()
