"""
Terminal-Based Researcher Interface
Manages researcher interaction, mode selection, and approval workflow
"""

from typing import Dict, List, Any


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
