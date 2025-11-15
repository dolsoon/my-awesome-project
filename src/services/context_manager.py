"""
Context File Manager
Manages importing, storing, and tracking context files for LLM augmentation
"""

import os
import json
from typing import Dict, List, Optional, Tuple
import tiktoken


class ContextFileManager:
    """Manages context files for LLM analysis"""

    # Constants
    MAX_FILE_SIZE = 10000  # characters
    MAX_TOTAL_SIZE = 50000  # characters
    TOKEN_LIMIT = 128000  # for Gemini/GPT-4

    def __init__(self):
        """Initialize context file manager"""
        self.imported_files: Dict[str, str] = {}  # filename -> content
        self.config_path: str = "context_config.json"
        self.token_encoder = tiktoken.get_encoding("cl100k_base")

    def import_file(self, file_path: str) -> bool:
        """Import a context file"""
        if not self.validate_file(file_path):
            return False

        if not self.validate_file_content(file_path):
            return False

        # Check total size limit
        current_total = sum(len(content) for content in self.imported_files.values())
        new_file_size = os.path.getsize(file_path)

        if current_total + new_file_size > self.MAX_TOTAL_SIZE:
            return False

        # Check for duplicates
        filename = os.path.basename(file_path)
        if filename in self.imported_files:
            return False

        # Read and store file
        try:
            with open(file_path, "r") as f:
                content = f.read()
            self.imported_files[filename] = content
            return True
        except Exception:
            return False

    def validate_file(self, file_path: str) -> bool:
        """Validate file format and size"""
        # Check if file exists
        if not os.path.exists(file_path):
            return False

        # Check file extension
        if not file_path.endswith(".txt"):
            return False

        # Check file size
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                return False
        except Exception:
            return False

        return True

    def validate_file_content(self, file_path: str) -> bool:
        """Validate file content is readable text"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read()
            return True
        except Exception:
            return False

    def list_files(self) -> List[str]:
        """List imported context files"""
        return list(self.imported_files.keys())

    def list_files_with_sizes(self) -> List[Tuple[str, int]]:
        """List imported files with their sizes"""
        return [
            (filename, len(content))
            for filename, content in self.imported_files.items()
        ]

    def remove_file(self, filename: str) -> bool:
        """Remove a context file"""
        if filename in self.imported_files:
            del self.imported_files[filename]
            return True
        return False

    def get_full_context(self) -> str:
        """Get concatenated context of all files"""
        parts = []
        for filename, content in self.imported_files.items():
            parts.append(f"[{filename}]\n{content}\n")
        return "\n".join(parts)

    def get_token_count(self) -> int:
        """Get total token count of all context files"""
        context = self.get_full_context()
        tokens = self.token_encoder.encode(context)
        return len(tokens)

    @property
    def total_token_count(self) -> int:
        """Get total token count of all context"""
        return self.get_token_count()

    def check_token_limit_warning(self) -> Optional[str]:
        """Check if approaching token limit and return warning"""
        token_count = self.get_token_count()
        threshold = int(self.TOKEN_LIMIT * 0.8)  # Warn at 80% usage

        if token_count > threshold:
            remaining = self.TOKEN_LIMIT - token_count
            msg = (
                f"Warning: Token usage at {token_count}/{self.TOKEN_LIMIT}. "
                f"{remaining} tokens remaining."
            )
            return msg

        return None

    def clear_all(self) -> None:
        """Clear all imported context files"""
        self.imported_files.clear()

    def save_context_list(self) -> None:
        """Save context file list to disk"""
        config = {
            "files": list(self.imported_files.keys()),
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def load_context_list(self) -> None:
        """Load context file list from disk"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    _config = json.load(f)
                # Note: content would need to be loaded from disk separately
            except Exception:
                pass
