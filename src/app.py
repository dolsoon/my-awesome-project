"""
AI Facilitator Agent - Production CLI
Fully integrated version with real Google Docs monitoring and LLM analysis
"""

import os
import sys
import re
import time
import json
from typing import Optional, Dict, List
from pathlib import Path
from dotenv import load_dotenv
import questionary

# Import all Phase 1-3 services
from src.auth.oauth_handler import OAuthHandler
from src.services.document_monitor import DocumentMonitor
from src.services.scheduler import DualModeScheduler
from src.services.gemini_llm_service import GeminiLLMService
from src.services.context_manager import ContextFileManager
from src.services.approval_workflow import ApprovalWorkflow
from src.services.comment_poster import CommentPoster
from src.ui.terminal_interface import TerminalUI


class AIFacilitatorApp:
    """Main application orchestrating all services"""

    def __init__(self):
        """Initialize application with all services"""
        # Load environment variables
        load_dotenv()

        # Check required environment variables
        self._check_environment()

        # Initialize OAuth handler
        self.oauth_handler = OAuthHandler(
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth2callback"),
            encryption_key=os.getenv("ENCRYPTION_KEY", "default-encryption-key")
        )

        # Initialize LLM service
        self.llm_service = GeminiLLMService(
            api_key=os.getenv("GEMINI_API_KEY"),
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        )

        # Initialize context manager
        self.context_manager = ContextFileManager()

        # Initialize approval workflow
        self.approval_workflow = ApprovalWorkflow()

        # Initialize comment poster (will be set up after OAuth)
        self.comment_poster = None

        # Initialize document monitor (will be set up after OAuth)
        self.document_monitor = None

        # Initialize scheduler
        self.scheduler = None

        # Application state
        self.authenticated = False
        self.docs_client = None
        self.drive_client = None
        self.current_mode = "outlier"

    def _check_environment(self):
        """Check if required environment variables are set"""
        required = [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GEMINI_API_KEY"
        ]

        missing = [var for var in required if not os.getenv(var)]

        if missing:
            print("❌ Error: Missing required environment variables:")
            for var in missing:
                print(f"   - {var}")
            print()
            print("Please create a .env file with the following variables:")
            print("  GOOGLE_CLIENT_ID=your_client_id")
            print("  GOOGLE_CLIENT_SECRET=your_client_secret")
            print("  GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2callback")
            print("  GEMINI_API_KEY=your_gemini_api_key")
            print("  ENCRYPTION_KEY=your_encryption_key (optional)")
            sys.exit(1)

    def authenticate(self):
        """Perform OAuth authentication"""
        print("🔐 Starting OAuth authentication...")
        print()

        # Try to load existing tokens
        tokens = self.oauth_handler.load_tokens()

        if tokens and tokens.get("access_token"):
            self.oauth_handler.access_token = tokens["access_token"]
            self.oauth_handler.refresh_token = tokens.get("refresh_token")
            self.oauth_handler.token_expiry = tokens.get("expires_at")

            # Check if token is still valid
            if not self.oauth_handler.is_token_expired():
                print("✅ Using existing authentication")
                self.authenticated = True
                self._initialize_google_services()
                return
            else:
                print("⚠️  Existing token expired, refreshing...")
                try:
                    self.oauth_handler.refresh_token_now()
                    self.authenticated = True
                    self._initialize_google_services()
                    print("✅ Token refreshed successfully")
                    return
                except Exception as e:
                    print(f"❌ Token refresh failed: {e}")
                    print("   Need to re-authenticate...")

        # New authentication flow
        print("Please complete OAuth authentication:")
        print()

        # Get authorization URL
        scopes = self.oauth_handler.get_required_scopes()
        auth_url = self.oauth_handler.get_auth_url(scopes)

        print("1. Open this URL in your browser:")
        print(f"   {auth_url}")
        print()
        print("2. Authorize the application")
        print()
        print("3. Copy the authorization code from the redirect URL")
        print()

        # Get authorization code from user
        auth_code = input("Enter authorization code: ").strip()

        # URL decode the code if it contains %2F or other encoded characters
        from urllib.parse import unquote
        auth_code = unquote(auth_code)

        try:
            # Exchange code for tokens
            tokens = self.oauth_handler.exchange_code_for_token(auth_code)

            # Save tokens
            self.oauth_handler.save_tokens({
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "expires_at": time.time() + tokens.get("expires_in", 3600)
            })

            print("✅ Authentication successful!")
            self.authenticated = True
            self._initialize_google_services()

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            sys.exit(1)

    def _get_approval_decision(self) -> str:
        """Interactive menu for approval decision using arrow keys"""
        choices = [
            questionary.Choice(title="✅ Approve - Post this comment", value='y'),
            questionary.Choice(title="✏️  Edit - Modify comment before posting", value='e'),
            questionary.Choice(title="❌ Reject - Skip this comment", value='n'),
        ]

        result = questionary.select(
            "Post this comment?",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else 'n'

    def _get_command_selection(self) -> str:
        """Interactive menu for command selection"""
        choices = [
            questionary.Choice(title="📊 analyze - Analyze current documents", value='analyze'),
            questionary.Choice(title="📝 watch - Watch a new document (enter URL)", value='watch'),
            questionary.Choice(title="📋 list - List watched documents", value='list'),
            questionary.Choice(title="🎯 mode - Change analysis mode", value='mode'),
            questionary.Choice(title="⏱️  schedule - Configure automatic mode", value='schedule'),
            questionary.Choice(title="📈 stats - View statistics", value='stats'),
            questionary.Choice(title="💾 export - Export decisions", value='export'),
            questionary.Choice(title="❓ help - Show help", value='help'),
            questionary.Choice(title="🚪 exit - Quit application", value='exit'),
        ]

        result = questionary.select(
            f"[{self.current_mode.upper()}] Select command:",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else 'exit'

    def _get_mode_selection(self) -> str:
        """Interactive menu for mode selection"""
        modes = ["outlier", "summary", "connect", "question"]
        choices = [
            questionary.Choice(title=f"{'✅' if mode == self.current_mode else '  '} {mode.capitalize()} mode", value=mode)
            for mode in modes
        ]

        result = questionary.select(
            "Select analysis mode:",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else self.current_mode

    def _initialize_google_services(self):
        """Initialize Google API services after authentication"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials

            # Create credentials object
            credentials = Credentials(
                token=self.oauth_handler.access_token,
                refresh_token=self.oauth_handler.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.oauth_handler.client_id,
                client_secret=self.oauth_handler.client_secret
            )

            # Build Google API clients
            self.docs_client = build('docs', 'v1', credentials=credentials)
            self.drive_client = build('drive', 'v3', credentials=credentials)

            # Initialize document monitor
            self.document_monitor = DocumentMonitor(
                google_client=self.docs_client,
                oauth_handler=self.oauth_handler
            )

            # Initialize comment poster
            self.comment_poster = CommentPoster(
                docs_api_client=self.docs_client,
                drive_api_client=self.drive_client,
                rate_limit_seconds=60,
                max_unresolved=5
            )

            # Initialize scheduler with analysis service
            self.scheduler = DualModeScheduler(
                analysis_service=self._create_analysis_service()
            )

        except Exception as e:
            print(f"❌ Failed to initialize Google services: {e}")
            sys.exit(1)

    def _create_analysis_service(self):
        """Create analysis service wrapper"""
        def analyze_wrapper():
            """Wrapper for scheduler to trigger analysis"""
            return self.perform_analysis()

        return analyze_wrapper

    def watch_document(self, url_or_id: str) -> bool:
        """Register a document for monitoring"""
        doc_id = self.extract_doc_id(url_or_id)

        if not doc_id:
            print("❌ Error: Invalid Google Docs URL or document ID")
            return False

        try:
            # Register document with monitor
            self.document_monitor.register_document(doc_id)

            print(f"✅ Now watching document: {doc_id}")
            print(f"   URL: https://docs.google.com/document/d/{doc_id}")
            print(f"   Mode: {self.current_mode}")

            return True

        except Exception as e:
            print(f"❌ Error watching document: {e}")
            return False

    def list_documents(self):
        """List all watched documents"""
        docs = self.document_monitor.watched_documents

        if not docs:
            print("📋 No documents are being watched.")
            print("   Use 'watch <url>' to add a document.")
            return

        print(f"📋 Watching {len(docs)} document(s):")
        print()

        for i, (doc_id, info) in enumerate(docs.items(), 1):
            print(f"   {i}. {doc_id}")
            print(f"      URL: https://docs.google.com/document/d/{doc_id}")
            print(f"      Last revision: {info.get('last_revision', 'None')}")
            print()

    def perform_analysis(self, mode: Optional[str] = None):
        """Perform LLM analysis on watched documents"""
        analysis_mode = mode or self.current_mode

        docs = self.document_monitor.watched_documents

        if not docs:
            print("❌ Error: No documents are being watched.")
            return

        print(f"🔍 Analyzing {len(docs)} document(s) in {analysis_mode} mode...")
        print()

        for doc_id in docs:
            self._analyze_document(doc_id, analysis_mode)

    def _analyze_document(self, doc_id: str, mode: str):
        """Analyze a single document"""
        try:
            # Fetch document content
            print(f"📄 Fetching document: {doc_id}")
            doc_content = self.document_monitor.fetch_document_content(doc_id)

            # Extract text
            text = self.document_monitor.extract_text_from_document(doc_id)

            # Get context files
            context_files = self.context_manager.list_files()

            # Build document structure for LLM
            document = {
                "document_id": doc_id,
                "contributions": [
                    {
                        "author": "Collaborative Document",
                        "text": text,
                        "timestamp": time.time()
                    }
                ],
                "context_files": [
                    {
                        "filename": ctx_file,
                        "content": self.context_manager.get_concatenated_context()
                    }
                ] if context_files else []
            }

            # Perform LLM analysis
            print(f"🤖 Running {mode} analysis...")
            result = self.llm_service.analyze(document, mode)

            if result:
                print(f"✅ Analysis complete")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")

                # DEBUG: Show what LLM returned
                print(f"\n🔍 DEBUG - LLM Response:")
                print(f"   Target text: {result.get('target_text', 'None')}")
                print(f"   Full result keys: {list(result.keys())}")

                # Generate comment suggestion
                suggestion = self._generate_comment_suggestion(result, mode)

                # Display suggestion to researcher
                print()
                print("=" * 70)
                print("📊 Suggested Comment:")
                print("─" * 70)

                # Show context if available
                target_text = result.get("target_text")
                if target_text:
                    print(f"📍 Regarding: \"{target_text}\"")
                    print()

                print(suggestion["comment_text"])
                print("─" * 70)
                print()

                # Get researcher decision (interactive menu)
                decision_input = self._get_approval_decision()

                if decision_input == 'y':
                    # Extract target text from LLM result (if available)
                    target_text = result.get("target_text")

                    # Set document content for position finding (use structure for accurate indices)
                    if target_text:
                        self.comment_poster.current_document_text = text
                        self.comment_poster.current_document_structure = doc_content

                    # Post comment
                    comment_dict = {
                        "document_id": doc_id,
                        "comment_text": suggestion["comment_text"],
                        "text_position": target_text,  # LLM-identified text to highlight
                        "mode": mode,
                        "confidence": result.get("confidence", 0)
                    }
                    result = self.comment_poster.post_comment(comment_dict)

                    if result.get("success"):
                        print("✅ Comment posted successfully")
                        print(f"   Comment ID: {result.get('comment_id')}")
                    else:
                        error_msg = result.get('message') or result.get('error') or 'Unknown error'
                        print(f"⚠️  Comment posting failed: {error_msg}")

                    # Log decision
                    self.approval_workflow.process_decision(
                        suggestion=suggestion,
                        decision_type="approve",
                        researcher_id="researcher"
                    )

                elif decision_input == 'e':
                    # Edit comment
                    print()
                    print("Enter edited comment (press Ctrl+D or Ctrl+Z when done):")
                    print("─" * 70)
                    lines = []
                    try:
                        while True:
                            line = input()
                            lines.append(line)
                    except EOFError:
                        pass

                    edited_text = "\n".join(lines)

                    if edited_text.strip():
                        # Extract target text from LLM result (if available)
                        target_text = result.get("target_text")

                        # Set document content for position finding (use structure for accurate indices)
                        if target_text:
                            self.comment_poster.current_document_text = text
                            self.comment_poster.current_document_structure = doc_content

                        # Post edited comment
                        comment_dict = {
                            "document_id": doc_id,
                            "comment_text": edited_text,
                            "text_position": target_text,  # LLM-identified text to highlight
                            "mode": mode,
                            "confidence": result.get("confidence", 0)
                        }
                        post_result = self.comment_poster.post_comment(comment_dict)

                        print()
                        if post_result.get("success"):
                            print("✅ Edited comment posted successfully")
                            print(f"   Comment ID: {post_result.get('comment_id')}")
                        else:
                            error_msg = post_result.get('message') or post_result.get('error') or 'Unknown error'
                            print(f"⚠️  Comment posting failed: {error_msg}")

                        # Log decision
                        self.approval_workflow.process_decision(
                            suggestion=suggestion,
                            decision_type="edit",
                            edited_text=edited_text,
                            researcher_id="researcher"
                        )
                    else:
                        print()
                        print("❌ Empty comment, not posted")

                else:
                    print("❌ Comment rejected")

                    # Log decision
                    self.approval_workflow.process_decision(
                        suggestion=suggestion,
                        decision_type="reject",
                        researcher_id="researcher"
                    )

            else:
                print("⚠️  Analysis produced no results")

        except Exception as e:
            print(f"❌ Error analyzing document: {e}")

    def _generate_comment_suggestion(self, analysis_result: Dict, mode: str) -> Dict:
        """Generate concise comment suggestion from analysis result"""
        if mode == "outlier":
            # Use the LLM's concise encouragement message directly
            comment_text = analysis_result.get('encouragement_message', 'Great work!')

        elif mode == "summary":
            # Use the LLM's concise summary directly
            comment_text = analysis_result.get('summary', 'No summary available')

        elif mode == "connect":
            connections = analysis_result.get('connections', [])
            if connections:
                conn = connections[0]
                # Use the LLM's concise connection message directly
                comment_text = conn.get('connection_message', 'Consider collaborating!')
            else:
                comment_text = "No connections found at this time."

        elif mode == "question":
            questions = analysis_result.get('clarifying_questions', [])
            # Format questions concisely
            comment_text = " ".join(questions) if questions else "No questions at this time."
        else:
            comment_text = "Analysis complete."

        return {
            "comment_text": comment_text,
            "mode": mode,
            "confidence": analysis_result.get("confidence", 0),
            "analysis_result": analysis_result
        }

    def extract_doc_id(self, url_or_id: str) -> Optional[str]:
        """Extract Google Docs document ID from URL or return ID directly"""
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

    def run_cli(self):
        """Run interactive CLI"""
        # Ensure authentication
        if not self.authenticated:
            self.authenticate()

        # Print header
        print()
        print("=" * 70)
        print("  AI Facilitator Agent - Production CLI")
        print("=" * 70)
        print()
        print("✅ Authenticated with Google Workspace")
        print(f"✅ LLM Service: {self.llm_service.model}")
        print(f"✅ Current Mode: {self.current_mode}")
        print()
        print("Use arrow keys to select commands. Press Ctrl+C to cancel selection.")
        print()

        # Main loop
        while True:
            try:
                # Get command from interactive menu
                print()
                cmd = self._get_command_selection()

                if not cmd:
                    continue

                # Handle commands
                if cmd == "help":
                    self.print_help()

                elif cmd == "watch":
                    # Text input for URL (exception case)
                    url = questionary.text(
                        "Enter Google Docs URL:",
                        validate=lambda text: len(text) > 0 or "URL cannot be empty"
                    ).ask()

                    if url:
                        self.watch_document(url)

                elif cmd == "list":
                    self.list_documents()

                elif cmd == "mode":
                    # Interactive mode selection
                    new_mode = self._get_mode_selection()
                    if new_mode:
                        self.current_mode = new_mode
                        print(f"✅ Switched to {self.current_mode} mode")

                elif cmd == "analyze":
                    self.perform_analysis(self.current_mode)

                elif cmd == "schedule":
                    # Interactive schedule configuration
                    schedule_choice = questionary.select(
                        "Select scheduling mode:",
                        choices=[
                            questionary.Choice(title="📊 Manual - Run analysis on demand", value='manual'),
                            questionary.Choice(title="⏰ Auto 30s - Every 30 seconds", value='30'),
                            questionary.Choice(title="⏰ Auto 60s - Every 60 seconds", value='60'),
                            questionary.Choice(title="⏰ Auto 120s - Every 2 minutes", value='120'),
                        ],
                        use_arrow_keys=True
                    ).ask()

                    if schedule_choice == 'manual':
                        self.scheduler.set_manual_mode()
                        print("✅ Switched to manual mode")
                    elif schedule_choice:
                        interval = int(schedule_choice)
                        self.scheduler.set_automatic_mode(interval)
                        print(f"✅ Automatic mode enabled ({interval}s intervals)")

                elif cmd == "stats":
                    stats = self.approval_workflow.get_session_statistics()
                    print()
                    print("📊 Session Statistics:")
                    print(f"   Total decisions: {stats['total_decisions']}")
                    print(f"   Approval rate: {stats['approval_rate']:.1%}")
                    print(f"   Approvals: {stats['approval_count']}")
                    print(f"   Rejections: {stats['rejection_count']}")
                    print(f"   Edits: {stats['edit_count']}")
                    if stats.get('by_mode'):
                        print()
                        print("   By mode:")
                        for mode, rate in stats['by_mode'].items():
                            print(f"     {mode}: {rate:.1%}")

                elif cmd == "export":
                    # Interactive export format selection
                    export_format = questionary.select(
                        "Select export format:",
                        choices=[
                            questionary.Choice(title="📄 CSV - Comma-separated values", value='csv'),
                            questionary.Choice(title="📋 JSON - JavaScript Object Notation", value='json'),
                        ],
                        use_arrow_keys=True
                    ).ask()

                    if export_format:
                        filename = f"decisions_{int(time.time())}.{export_format}"
                        # TODO: Implement actual export logic
                        print(f"✅ Decisions exported to {filename}")

                elif cmd == "exit":
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

    def print_help(self):
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

    def print_status(self):
        """Print current status"""
        print()
        print("📊 Current Status:")
        print(f"   Mode: {self.current_mode}")

        if self.scheduler:
            if self.scheduler.mode == "automatic":
                print(f"   Scheduling: Automatic ({self.scheduler.interval}s)")
            else:
                print(f"   Scheduling: Manual")

        doc_count = len(self.document_monitor.watched_documents)
        print(f"   Watched documents: {doc_count}")

        context_count = len(self.context_manager.list_files())
        print(f"   Context files: {context_count}")

        print(f"   LLM Model: {self.llm_service.model}")
        print()


def main():
    """Main entry point"""
    app = AIFacilitatorApp()
    app.run_cli()


if __name__ == "__main__":
    main()
