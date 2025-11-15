"""
Test Context File Import Manager
SPEC-AI-FACIL-001 Phase 1: Context File Import
"""

import pytest


class TestContextFileManager:
    """Tests for context file import and management"""

    @pytest.fixture
    def context_manager(self):
        """Create ContextManager instance for testing"""
        from src.services.context_manager import ContextFileManager
        return ContextFileManager()

    def test_context_manager_initialization(self, context_manager):
        """Test context manager initializes correctly"""
        assert hasattr(context_manager, 'imported_files')
        assert hasattr(context_manager, 'total_token_count')
        assert len(context_manager.imported_files) == 0

    def test_import_valid_text_file(self, context_manager, tmp_path):
        """Test importing valid .txt file"""
        test_file = tmp_path / "context.txt"
        test_file.write_text("Sample context content")

        result = context_manager.import_file(str(test_file))
        assert result is True
        assert "context.txt" in context_manager.imported_files

    def test_validate_file_format(self, context_manager, tmp_path):
        """Test file format validation (.txt only)"""
        # Valid .txt file
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("Content")
        assert context_manager.validate_file(str(valid_file)) is True

        # Invalid .pdf file
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("Content")
        assert context_manager.validate_file(str(invalid_file)) is False

    def test_validate_file_size_limit(self, context_manager, tmp_path):
        """Test individual file size limit (10,000 characters)"""
        # Small file (valid)
        small_file = tmp_path / "small.txt"
        small_file.write_text("Small content")
        assert context_manager.validate_file(str(small_file)) is True

        # Large file (invalid - 10K+ chars)
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 15000)
        assert context_manager.validate_file(str(large_file)) is False

    def test_validate_total_context_size(self, context_manager, tmp_path):
        """Test total context size limit (50,000 characters)"""
        file1 = tmp_path / "file1.txt"
        file1.write_text("x" * 20000)
        context_manager.import_file(str(file1))

        file2 = tmp_path / "file2.txt"
        file2.write_text("x" * 35000)  # Would exceed 50K total
        result = context_manager.import_file(str(file2))

        assert result is False  # Should fail due to total size

    def test_list_imported_files(self, context_manager, tmp_path):
        """Test listing imported context files"""
        file1 = tmp_path / "context1.txt"
        file1.write_text("Content 1")
        context_manager.import_file(str(file1))

        files = context_manager.list_files()
        assert len(files) >= 1

    def test_list_files_with_sizes(self, context_manager, tmp_path):
        """Test listing files shows sizes"""
        test_file = tmp_path / "test.txt"
        test_content = "Sample content"
        test_file.write_text(test_content)
        context_manager.import_file(str(test_file))

        files_info = context_manager.list_files_with_sizes()
        assert len(files_info) >= 1
        assert len(files_info[0]) == 2  # (filename, size)

    def test_remove_context_file(self, context_manager, tmp_path):
        """Test removing context file"""
        test_file = tmp_path / "context.txt"
        test_file.write_text("Content")
        context_manager.import_file(str(test_file))

        assert "context.txt" in context_manager.imported_files

        context_manager.remove_file("context.txt")
        assert "context.txt" not in context_manager.imported_files

    def test_get_concatenated_context(self, context_manager, tmp_path):
        """Test getting concatenated context of all imported files"""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        context_manager.import_file(str(file1))

        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")
        context_manager.import_file(str(file2))

        full_context = context_manager.get_full_context()
        assert "Content 1" in full_context
        assert "Content 2" in full_context

    def test_context_file_error_handling(self, context_manager, tmp_path):
        """Test error handling for invalid file import"""
        nonexistent_file = "/nonexistent/path/file.txt"
        result = context_manager.import_file(nonexistent_file)
        assert result is False

    def test_token_usage_tracking(self, context_manager, tmp_path):
        """Test tracking token usage of context files"""
        test_file = tmp_path / "context.txt"
        test_file.write_text("Sample content for token counting")
        context_manager.import_file(str(test_file))

        token_count = context_manager.get_token_count()
        assert token_count > 0

    def test_token_limit_warning(self, context_manager, tmp_path):
        """Test warning when approaching 128K token limit"""
        test_file = tmp_path / "large_context.txt"
        # Create large content (approximately 100K tokens)
        test_file.write_text("word " * 20000)
        context_manager.import_file(str(test_file))

        warning = context_manager.check_token_limit_warning()
        assert warning is not None

    def test_clear_all_context_files(self, context_manager, tmp_path):
        """Test clearing all imported context files"""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        context_manager.import_file(str(file1))

        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")
        context_manager.import_file(str(file2))

        assert len(context_manager.imported_files) >= 2

        context_manager.clear_all()
        assert len(context_manager.imported_files) == 0

    def test_context_persistence(self, context_manager, tmp_path):
        """Test persisting context across session"""
        config_file = str(tmp_path / "context_config.json")
        context_manager.config_path = config_file

        # Save context
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content")
        context_manager.import_file(str(file1))
        context_manager.save_context_list()

        # Load in new manager
        from src.services.context_manager import ContextFileManager
        new_manager = ContextFileManager()
        new_manager.config_path = config_file
        new_manager.load_context_list()

        assert len(new_manager.imported_files) >= 1

    def test_duplicate_file_import_prevention(self, context_manager, tmp_path):
        """Test preventing duplicate file imports"""
        test_file = tmp_path / "context.txt"
        test_file.write_text("Content")

        # First import
        result1 = context_manager.import_file(str(test_file))
        assert result1 is True

        # Second import of same file
        result2 = context_manager.import_file(str(test_file))
        count = len([f for f in context_manager.imported_files
                     if "context.txt" in f])
        assert result2 is False or count == 1

    def test_file_content_validation(self, context_manager, tmp_path):
        """Test validating file content is readable text"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Readable text content")

        result = context_manager.validate_file_content(str(test_file))
        assert result is True
