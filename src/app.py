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
from src.services.analysis_presets import ANALYSIS_CONTEXT_PRESETS
from src.services.document_analyzer import DocumentAnalyzer
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

        # Analysis context - situational framing for LLM
        self.analysis_context = None  # Persists between analysis runs

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

    def _refresh_credentials_if_needed(self):
        """Refresh OAuth credentials if expired"""
        if self.oauth_handler.is_token_expired():
            print("🔄 Refreshing expired OAuth token...")
            try:
                self.oauth_handler.refresh_token_now()
                # Reinitialize Google services with fresh token
                self._initialize_google_services()
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                print("   Please restart the app to re-authenticate")
                sys.exit(1)

    def _initialize_google_services(self):
        """Initialize Google API services after authentication"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials

            # Create credentials object with refresh capability
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

            # Initialize terminal UI
            self.terminal_ui = TerminalUI(
                scheduler=self.scheduler,
                context_manager=self.context_manager,
                analysis_service=self._create_analysis_service()
            )

            # Initialize document analyzer
            self.document_analyzer = DocumentAnalyzer(
                llm_service=self.llm_service,
                context_manager=self.context_manager,
                comment_poster=self.comment_poster,
                approval_workflow=self.approval_workflow,
                document_monitor=self.document_monitor,
                terminal_ui=self.terminal_ui
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
        # Refresh credentials if needed before API calls
        self._refresh_credentials_if_needed()

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
        # Refresh credentials if needed before API calls
        self._refresh_credentials_if_needed()

        analysis_mode = mode or self.current_mode

        docs = self.document_monitor.watched_documents

        if not docs:
            print("❌ Error: No documents are being watched.")
            return

        print(f"🔍 Analyzing {len(docs)} document(s) in {analysis_mode} mode...")
        print()

        # Sync analysis context to document analyzer
        self.document_analyzer.analysis_context = self.analysis_context

        for doc_id in docs:
            self.document_analyzer.analyze_document(doc_id, analysis_mode)

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

        self._print_startup_banner()

        # Main loop
        while True:
            try:
                print()
                has_documents = len(self.document_monitor.watched_documents) > 0
                cmd = self.terminal_ui.get_command_selection(has_documents, self.current_mode)

                if not cmd:
                    continue

                # Delegate command handling to terminal_ui
                if self.terminal_ui.handle_cli_command(cmd, self):
                    sys.exit(0)

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Type 'exit' to quit or continue using commands.\n")

            except EOFError:
                print("\n\n👋 Goodbye!\n")
                sys.exit(0)

    def _print_startup_banner(self):
        """Print startup banner with status information"""
        print()
        print("=" * 70)
        print("  AI Facilitator Agent - Production CLI")
        print("=" * 70)
        print()
        print("✅ Authenticated with Google Workspace")
        print(f"✅ LLM Service: {self.llm_service.model}")
        print(f"✅ Current Mode: {self.current_mode}")
        context_status = "Set" if self.analysis_context else "Not set (use 'context' to configure)"
        print(f"📝 Analysis Context: {context_status}")
        print()
        print("Use arrow keys to select commands. Press Ctrl+C to cancel selection.")
        print()

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
        print("  analyze [mode]      Trigger analysis (optional: specify mode)")
        print("                      Types: outlier, summary, connect, question")
        print()
        print("  context             Set analysis context (situational framing)")
        print("                      Helps LLM understand the situation and target audience")
        print()
        print("  status              Show current status and configuration")
        print()
        print("  import <file>       Import background context file (.txt)")
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
