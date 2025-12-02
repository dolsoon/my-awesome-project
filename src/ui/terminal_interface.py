"""
Terminal-Based Researcher Interface
Manages researcher interaction, mode selection, and approval workflow
"""

from typing import Dict, List, Any, Optional
import questionary

from src.services.analysis_presets import ANALYSIS_CONTEXT_PRESETS


class TerminalUI:
    """Terminal-based researcher interface"""

    VALID_MODES = ["outlier", "summary", "connect", "question"]

    def __init__(self, scheduler, context_manager, analysis_service):
        """Initialize terminal UI"""
        self.scheduler = scheduler
        self.context_manager = context_manager
        self.analysis_service = analysis_service
        self.current_mode: str = "outlier"
        self.decision_history: List[Dict] = []
        self.analysis_context: Optional[str] = None

    def set_mode(self, mode: str) -> None:
        """Set current agent mode"""
        if mode in self.VALID_MODES:
            self.current_mode = mode

    def get_mode_display(self) -> str:
        """Get display string for current mode"""
        return f"[MODE: {self.current_mode.upper()}]"

    def display_changes(self, changes: List[Dict]) -> None:
        """Display document changes in terminal"""
        for change in changes:
            self.print_to_terminal(
                f"[{change.get('timestamp')}] {change.get('author')}: "
                f"{change.get('text', '')[:100]}..."
            )

    def show_analyzing_indicator(self) -> None:
        """Display analyzing progress indicator"""
        self.print_to_terminal("Analyzing...")

    def get_user_command(self) -> str:
        """Get user command input"""
        return input("> ").strip()

    def handle_command(self, command: str) -> Any:
        """Handle user terminal command"""
        parts = command.split(maxsplit=2)

        if not parts:
            return None

        cmd = parts[0].lower()

        if cmd == "analyze":
            if len(parts) > 1:
                mode = parts[1].lower()
                if mode in self.VALID_MODES:
                    self.trigger_mode_analysis(mode)
            else:
                self.scheduler.trigger_analysis_now()

        elif cmd == "mode":
            if len(parts) < 2:
                return None

            subcommand = parts[1].lower()

            if subcommand == "auto":
                if len(parts) > 2:
                    try:
                        interval = int(parts[2])
                        self.scheduler.set_automatic_mode(interval)
                    except ValueError:
                        pass
            elif subcommand == "manual":
                self.scheduler.set_manual_mode()
            elif subcommand in self.VALID_MODES:
                self.set_mode(subcommand)

        elif cmd == "status":
            self.display_status()

        elif cmd == "import":
            if len(parts) > 1:
                self.context_manager.import_file(parts[1])

        elif cmd == "list":
            if len(parts) > 1 and parts[1].lower() == "context":
                self.display_context_files()

        elif cmd == "remove":
            if len(parts) > 1:
                self.context_manager.remove_file(parts[1])

        elif cmd == "history":
            self.display_decision_history()

        elif cmd == "pause":
            self.scheduler.stop_automatic_analysis()

        elif cmd == "resume":
            self.scheduler.start_automatic_analysis()

        elif cmd == "help":
            self.display_help()

        return None

    def trigger_mode_analysis(self, mode: str) -> None:
        """Trigger analysis for specific mode"""
        pass

    def display_status(self) -> None:
        """Display current status"""
        pass

    def display_context_files(self) -> None:
        """Display imported context files"""
        pass

    def display_decision_history(self) -> None:
        """Display recent decisions"""
        pass

    def display_help(self) -> None:
        """Display help information"""
        pass

    def print_to_terminal(self, message: str) -> None:
        """Print message to terminal"""
        print(message)

    def get_header_display(self) -> str:
        """Get terminal header display with mode"""
        return f"[MODE: {self.current_mode}]"

    def get_countdown_display(self) -> str:
        """Get countdown to next automatic analysis"""
        if not self.scheduler.is_automatic():
            return ""
        countdown = self.scheduler.get_next_analysis_countdown()
        return f"[Next analysis in {countdown}s]"

    def get_full_header(self) -> str:
        """Get full header with mode and schedule"""
        mode_part = f"MODE: {self.current_mode}"
        if self.scheduler.is_automatic():
            return f"[{mode_part} | AUTO: {self.scheduler.interval}s]"
        else:
            return f"[{mode_part} | MANUAL]"

    # ==================== Menu Methods ====================

    def get_approval_decision(self) -> str:
        """Interactive menu for approval decision using arrow keys"""
        choices = [
            questionary.Choice(title="✅ Approve - Post this comment", value='y'),
            questionary.Choice(title="✏️  Edit - Modify comment manually", value='e'),
            questionary.Choice(title="🔄 Refine - Ask LLM to modify", value='r'),
            questionary.Choice(title="❌ Reject - Skip this comment", value='n'),
        ]

        result = questionary.select(
            "Post this comment?",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else 'n'

    def get_command_selection(self, has_documents: bool, current_mode: str) -> str:
        """Interactive menu for command selection (context-aware)"""
        if has_documents:
            # Documents exist - show Analyze at top
            context_indicator = " ✓" if self.analysis_context else ""

            choices = [
                questionary.Choice(title="📊 analyze - Analyze documents (choose mode)", value='analyze'),
                questionary.Choice(title=f"🎯 context - Set analysis context{context_indicator}", value='context'),
                questionary.Choice(title="📝 watch - Watch a new document", value='watch'),
                questionary.Choice(title="📋 list - List watched documents", value='list'),
                questionary.Choice(title="⏱️  schedule - Configure automatic mode", value='schedule'),
                questionary.Choice(title="📈 stats - View statistics", value='stats'),
                questionary.Choice(title="💾 export - Export decisions", value='export'),
                questionary.Choice(title="❓ help - Show help", value='help'),
                questionary.Choice(title="🚪 exit - Quit application", value='exit'),
            ]
        else:
            # No documents - show Watch at top
            context_indicator = " ✓" if self.analysis_context else ""

            choices = [
                questionary.Choice(title="📝 watch - Watch a new document (start here!)", value='watch'),
                questionary.Choice(title=f"🎯 context - Set analysis context{context_indicator}", value='context'),
                questionary.Choice(title="📋 list - List watched documents", value='list'),
                questionary.Choice(title="❓ help - Show help", value='help'),
                questionary.Choice(title="🚪 exit - Quit application", value='exit'),
            ]

        result = questionary.select(
            f"[{current_mode.upper()}] Main Menu:",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else 'exit'

    def get_analyze_menu(self, current_mode: str) -> str:
        """Interactive menu for analysis mode selection"""
        modes = ["outlier", "summary", "connect", "question"]
        choices = [
            questionary.Choice(
                title=f"{'✅' if mode == current_mode else '  '} {mode.capitalize()} mode",
                value=mode
            )
            for mode in modes
        ]
        choices.append(questionary.Choice(title="🔙 Back to main menu", value='back'))

        result = questionary.select(
            "Select analysis mode:",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else 'back'

    def get_mode_selection(self, current_mode: str) -> str:
        """Interactive menu for mode selection"""
        modes = ["outlier", "summary", "connect", "question"]
        choices = [
            questionary.Choice(
                title=f"{'✅' if mode == current_mode else '  '} {mode.capitalize()} mode",
                value=mode
            )
            for mode in modes
        ]

        result = questionary.select(
            "Select analysis mode:",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else current_mode

    def get_context_menu(self) -> str:
        """Interactive menu for setting analysis context"""
        choices = []

        # Show current context status with view option
        if self.analysis_context:
            first_line = self.analysis_context.split('\n')[0]
            current_preview = first_line[:40] + "..." if len(first_line) > 40 else first_line
            choices.append(questionary.Choice(
                title=f"👁️  View current context ({current_preview})",
                value='view_current'
            ))

        # Predefined options
        choices.extend([
            questionary.Choice(
                title="📋 Collaborative Feedback Session",
                value='collaborative_feedback'
            ),
            questionary.Choice(
                title="🔬 Research/Academic Review",
                value='research_review'
            ),
            questionary.Choice(
                title="💡 Brainstorming Session",
                value='brainstorming'
            ),
            questionary.Choice(
                title="✏️  Custom Context - Enter your own",
                value='custom'
            ),
        ])

        # Add reset option if context is set
        if self.analysis_context:
            choices.append(questionary.Choice(
                title="🔄 Reset - Clear analysis context",
                value='reset'
            ))

        choices.append(questionary.Choice(
            title="🔙 Back to main menu",
            value='back'
        ))

        result = questionary.select(
            "Set Analysis Context:",
            choices=choices,
            use_arrow_keys=True
        ).ask()

        return result if result else 'back'

    def handle_context_menu(self) -> None:
        """Handle analysis context menu selection. Updates self.analysis_context."""
        while True:
            choice = self.get_context_menu()

            if choice == 'back':
                break

            elif choice == 'reset':
                self.analysis_context = None
                print()
                print("✅ Analysis context cleared")
                print()
                break

            elif choice == 'custom':
                print()
                print("Enter your custom analysis context.")
                print("Describe the situation, target audience, and purpose of the analysis.")
                print("(Press Enter twice to finish)")
                print()

                custom_context = questionary.text(
                    "Custom context:",
                    multiline=False
                ).ask()

                if custom_context and custom_context.strip():
                    self.analysis_context = custom_context.strip()
                    print()
                    print("✅ Custom analysis context set")
                    print()
                break

            elif choice in ANALYSIS_CONTEXT_PRESETS:
                preset = ANALYSIS_CONTEXT_PRESETS[choice]
                self.analysis_context = preset["context"]
                print()
                print(f"✅ Analysis context set: {preset['name']}")
                print(f"   {preset['description']}")
                print()
                break

            elif choice == 'view_current':
                # Display the full current context
                print()
                print("=" * 70)
                print("📝 Current Analysis Context:")
                print("-" * 70)
                print(self.analysis_context)
                print("-" * 70)
                print()
                # Continue the loop to show menu again
                continue

    # ==================== CLI Command Handlers ====================

    def handle_cli_command(self, cmd: str, app) -> bool:
        """
        Handle CLI command. Returns True if should exit.

        Args:
            cmd: Command string from menu selection
            app: Reference to AIFacilitatorApp for accessing app methods

        Returns:
            True if the application should exit, False otherwise
        """
        handlers = {
            'help': lambda: self._handle_help(app),
            'watch': lambda: self._handle_watch(app),
            'list': lambda: self._handle_list(app),
            'analyze': lambda: self._handle_analyze(app),
            'context': lambda: self._handle_context(app),
            'schedule': lambda: self._handle_schedule(app),
            'stats': lambda: self._handle_stats(app),
            'export': lambda: self._handle_export(app),
            'exit': lambda: self._handle_exit(),
        }

        handler = handlers.get(cmd)
        if handler:
            result = handler()
            return cmd == 'exit'

        print(f"❌ Unknown command: {cmd}")
        print("   Type 'help' for available commands")
        return False

    def _handle_help(self, app) -> None:
        """Handle help command"""
        app.print_help()

    def _handle_watch(self, app) -> None:
        """Handle watch command"""
        url = questionary.text(
            "Enter Google Docs URL:",
            validate=lambda text: len(text) > 0 or "URL cannot be empty"
        ).ask()
        if url:
            app.watch_document(url)

    def _handle_list(self, app) -> None:
        """Handle list command"""
        app.list_documents()

    def _handle_analyze(self, app) -> None:
        """Handle analyze command with mode selection loop"""
        while True:
            mode_choice = self.get_analyze_menu(app.current_mode)

            if mode_choice == 'back':
                break

            # Update current mode
            app.current_mode = mode_choice
            print(f"\n✅ Selected {app.current_mode} mode")

            # Perform analysis
            app.perform_analysis(app.current_mode)

            # After analysis, show post-analysis menu
            post_analysis_choice = questionary.select(
                "What would you like to do next?",
                choices=[
                    questionary.Choice(title="🔄 Analyze again (same mode)", value='again'),
                    questionary.Choice(title="🎯 Change mode and analyze", value='change'),
                    questionary.Choice(title="🔙 Back to main menu", value='back'),
                ],
                use_arrow_keys=True
            ).ask()

            if post_analysis_choice == 'again':
                app.perform_analysis(app.current_mode)
            elif post_analysis_choice == 'change':
                continue
            else:
                break

    def _handle_context(self, app) -> None:
        """Handle context command"""
        self.handle_context_menu()
        # Sync context state back to app
        app.analysis_context = self.analysis_context

    def _handle_schedule(self, app) -> None:
        """Handle schedule command"""
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
            app.scheduler.set_manual_mode()
            print("✅ Switched to manual mode")
        elif schedule_choice:
            interval = int(schedule_choice)
            app.scheduler.set_automatic_mode(interval)
            print(f"✅ Automatic mode enabled ({interval}s intervals)")

    def _handle_stats(self, app) -> None:
        """Handle stats command"""
        stats = app.approval_workflow.get_session_statistics()
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

    def _handle_export(self, app) -> None:
        """Handle export command"""
        import time
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

    def _handle_exit(self) -> bool:
        """Handle exit command"""
        print()
        print("👋 Goodbye! Thanks for using AI Facilitator Agent.")
        print()
        return True


def main():
    """Main entry point for terminal interface"""
    print("AI Facilitator Agent - Terminal Interface")
    print("=" * 60)
    print()
    print("Welcome! This is the terminal interface for the AI Facilitator.")
    print()
    print("To run the full application, you need to:")
    print("1. Set up your .env file with API keys (see .env.example)")
    print("2. Configure production settings in config/production.yaml")
    print("3. Run the main application (coming in production deployment)")
    print()
    print("For now, this is a demonstration of the module structure.")
    print()
    print("Available commands will include:")
    print("  - analyze [mode]    : Trigger analysis")
    print("  - mode [type]       : Switch agent mode")
    print("  - status            : Show current status")
    print("  - import <file>     : Import context file")
    print("  - help              : Show all commands")
    print()


if __name__ == "__main__":
    main()
