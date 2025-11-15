"""
Test Terminal UI
SPEC-AI-FACIL-001 Phase 1: Terminal Interface
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestTerminalUI:
    """Tests for terminal-based researcher interface"""

    @pytest.fixture
    def terminal_ui(self):
        """Create TerminalUI instance for testing"""
        from src.ui.terminal_interface import TerminalUI
        return TerminalUI(
            scheduler=Mock(),
            context_manager=Mock(),
            analysis_service=Mock()
        )

    def test_terminal_initialization(self, terminal_ui):
        """Test terminal UI initializes correctly"""
        assert terminal_ui.scheduler is not None
        assert terminal_ui.context_manager is not None
        assert terminal_ui.current_mode == "outlier"  # default

    def test_display_current_mode(self, terminal_ui):
        """Test displaying current agent mode in terminal"""
        terminal_ui.set_mode("summary")
        display = terminal_ui.get_mode_display()
        assert "summary" in display.lower() or "SUMMARY" in display

    def test_mode_selection_commands(self, terminal_ui):
        """Test mode selection via terminal commands"""
        modes = ["outlier", "summary", "connect", "question"]

        for mode in modes:
            terminal_ui.set_mode(mode)
            assert terminal_ui.current_mode == mode

    def test_display_document_changes(self, terminal_ui):
        """Test displaying document changes in terminal"""
        changes = [
            {"timestamp": 1234567890, "author": "Alice", "text": "First contribution"},
            {"timestamp": 1234567900, "author": "Bob", "text": "Second contribution"}
        ]

        with patch.object(terminal_ui, 'print_to_terminal') as mock_print:
            terminal_ui.display_changes(changes)
            assert mock_print.called

    def test_display_analyzing_indicator(self, terminal_ui):
        """Test displaying 'Analyzing...' indicator during analysis"""
        with patch.object(terminal_ui, 'print_to_terminal') as mock_print:
            terminal_ui.show_analyzing_indicator()
            assert mock_print.called

    def test_command_prompt_loop(self, terminal_ui):
        """Test command prompt loop for user input"""
        with patch('builtins.input', return_value="mode outlier"):
            command = terminal_ui.get_user_command()
            assert "mode" in command
            assert "outlier" in command

    def test_analyze_command(self, terminal_ui):
        """Test 'analyze' command to trigger immediate analysis"""
        mock_trigger = patch.object(
            terminal_ui.scheduler, 'trigger_analysis_now'
        )
        with mock_trigger as mt:
            terminal_ui.handle_command("analyze")
            mt.assert_called_once()

    def test_analyze_specific_mode_command(self, terminal_ui):
        """Test 'analyze [mode]' command for mode-specific analysis"""
        modes = ["outlier", "summary", "connect", "question"]

        for mode in modes:
            with patch.object(terminal_ui, 'trigger_mode_analysis') as mock_analysis:
                terminal_ui.handle_command(f"analyze {mode}")
                mock_analysis.assert_called_once()

    def test_mode_command(self, terminal_ui):
        """Test 'mode [type]' command to switch modes"""
        with patch.object(terminal_ui, 'set_mode') as mock_set_mode:
            terminal_ui.handle_command("mode summary")
            mock_set_mode.assert_called()

    def test_mode_auto_command(self, terminal_ui):
        """Test 'mode auto [30|60|120]' command for automatic mode"""
        with patch.object(terminal_ui.scheduler, 'set_automatic_mode') as mock_auto:
            terminal_ui.handle_command("mode auto 60")
            mock_auto.assert_called()

    def test_mode_manual_command(self, terminal_ui):
        """Test 'mode manual' command to switch to on-demand mode"""
        with patch.object(terminal_ui.scheduler, 'set_manual_mode') as mock_manual:
            terminal_ui.handle_command("mode manual")
            mock_manual.assert_called()

    def test_status_command(self, terminal_ui):
        """Test 'status' command to show current mode and countdown"""
        with patch.object(terminal_ui, 'display_status') as mock_status:
            terminal_ui.handle_command("status")
            mock_status.assert_called()

    def test_display_mode_prominently(self, terminal_ui):
        """Test displaying mode prominently in terminal"""
        terminal_ui.set_mode("outlier")
        display = terminal_ui.get_header_display()
        assert "[MODE:" in display or "MODE" in display

    def test_display_auto_countdown(self, terminal_ui):
        """Test displaying countdown to next automatic analysis"""
        terminal_ui.scheduler.set_automatic_mode(interval_seconds=60)
        display = terminal_ui.get_countdown_display()
        assert "next" in display.lower() or "countdown" in display.lower()

    def test_import_context_command(self, terminal_ui):
        """Test 'import <file>' command to add context files"""
        with patch.object(terminal_ui.context_manager, 'import_file') as mock_import:
            terminal_ui.handle_command("import context.txt")
            mock_import.assert_called()

    def test_list_context_command(self, terminal_ui):
        """Test 'list context' command to show imported files"""
        with patch.object(terminal_ui, 'display_context_files') as mock_list:
            terminal_ui.handle_command("list context")
            mock_list.assert_called()

    def test_remove_context_command(self, terminal_ui):
        """Test 'remove <file>' command to remove context file"""
        with patch.object(terminal_ui.context_manager, 'remove_file') as mock_remove:
            terminal_ui.handle_command("remove context.txt")
            mock_remove.assert_called()

    def test_terminal_command_response_time(self, terminal_ui):
        """Test terminal responds to commands within 500ms"""
        import time

        start = time.time()
        with patch.object(terminal_ui.scheduler, 'trigger_analysis_now'):
            terminal_ui.handle_command("analyze")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 500  # milliseconds

    def test_history_command(self, terminal_ui):
        """Test 'history' command to display recent decisions"""
        with patch.object(terminal_ui, 'display_decision_history') as mock_history:
            terminal_ui.handle_command("history")
            mock_history.assert_called()

    def test_pause_resume_commands(self, terminal_ui):
        """Test 'pause' and 'resume' commands for batch processing"""
        mock_stop = patch.object(
            terminal_ui.scheduler, 'stop_automatic_analysis'
        )
        with mock_stop as ms:
            terminal_ui.handle_command("pause")
            ms.assert_called()

        mock_start = patch.object(
            terminal_ui.scheduler, 'start_automatic_analysis'
        )
        with mock_start as mst:
            terminal_ui.handle_command("resume")
            mst.assert_called()

    def test_help_command(self, terminal_ui):
        """Test 'help' command to show available commands"""
        with patch.object(terminal_ui, 'display_help') as mock_help:
            terminal_ui.handle_command("help")
            mock_help.assert_called()

    def test_mode_display_format(self, terminal_ui):
        """Test mode display format with mode and schedule info"""
        terminal_ui.set_mode("outlier")
        terminal_ui.scheduler.set_automatic_mode(60)

        display = terminal_ui.get_full_header()
        assert "MODE" in display
        assert "outlier" in display.lower()
