"""
Comment Posting Service
SPEC-AI-FACIL-001 Phase 2: Google Docs API comment posting with rate limiting
Minimal implementation for TDD GREEN phase
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import time
import re


class CommentPoster:
    """Posts comments to Google Docs with rate limiting and deduplication"""

    def __init__(self, docs_api_client, drive_api_client, rate_limit_seconds: int = 60, max_unresolved: int = 5):
        """Initialize CommentPoster"""
        self.docs_api_client = docs_api_client
        self.drive_api_client = drive_api_client
        self.rate_limit_seconds = rate_limit_seconds
        self.max_unresolved_comments = max_unresolved
        self.last_comment_time: Dict[str, datetime] = {}
        self.unresolved_comments: Dict[str, int] = {}
        self.posted_comments: Dict[str, Dict] = {}
        self.pending_queue: List[Dict] = []
        self.failed_queue: List[Dict] = []
        self.posting_history: List[Dict] = []
        self.current_document_text: str = ""

    def format_comment(self, comment: Dict[str, Any]) -> str:
        """Format comment with mode attribution and metadata"""
        mode = comment.get("mode", "").upper()
        confidence = comment.get("confidence", 0)
        comment_text = comment.get("comment_text", "")
        timestamp = datetime.now().isoformat()

        return f"[AI Facilitator - {mode}] {comment_text}\n(Confidence: {confidence:.0%}, Posted: {timestamp})"

    def can_post_comment(self, document_id: str) -> bool:
        """Check if comment can be posted (rate limiting)"""
        last_time = self.last_comment_time.get(document_id)
        if last_time is None:
            return True

        elapsed = datetime.now() - last_time
        return elapsed.total_seconds() >= self.rate_limit_seconds

    def _hash_position(self, document_id: str, position: Optional[Dict] = None) -> str:
        """Hash document position for deduplication"""
        key = f"{document_id}:{position}".encode()
        return hashlib.md5(key).hexdigest()

    def _find_text_position(self, target_text: str) -> Optional[Dict]:
        """Find position of target text in document"""
        if not target_text or not self.current_document_text:
            print(f"   ❌ DEBUG: Empty target_text or document_text")
            return None

        print(f"\n🔍 DEBUG - Text Matching:")
        print(f"   Target text: '{target_text}'")
        print(f"   Target length: {len(target_text)} chars")
        print(f"   Document length: {len(self.current_document_text)} chars")
        print(f"   Document preview: '{self.current_document_text[:200]}...'")

        # Try exact match
        if target_text in self.current_document_text:
            index = self.current_document_text.find(target_text)
            print(f"   ✅ Exact match found at index {index}")
            return {"index": index, "length": len(target_text)}

        # Try case-insensitive match
        lower_doc = self.current_document_text.lower()
        lower_target = target_text.lower()
        if lower_target in lower_doc:
            index = lower_doc.find(lower_target)
            print(f"   ✅ Case-insensitive match found at index {index}")
            return {"index": index, "length": len(target_text)}

        # No match found - show why
        print(f"   ❌ No exact or case-insensitive match found")
        print(f"   💡 Checking if words from target appear in document:")
        words = target_text.lower().split()
        for word in words[:5]:  # Check first 5 words
            if word in lower_doc:
                print(f"      ✓ '{word}' found")
            else:
                print(f"      ✗ '{word}' NOT found")

        return None

    def _call_docs_api(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Insert AI facilitation text directly into the document with formatting"""
        document_id = request["document_id"]
        comment_text = request["comment_text"]
        position = request.get("position")

        # Determine insertion position and extract context
        target_text_quote = None
        if position and isinstance(position, dict):
            # Insert after the target text
            insert_index = position["index"] + position["length"]
            # Extract the target text for context
            if self.current_document_text:
                target_text_quote = self.current_document_text[
                    position["index"]:position["index"] + position["length"]
                ].strip()
        else:
            # Insert at the top of the document (so users see it immediately)
            insert_index = 1  # Index 1 is right after the document start

        # Format the AI message with context
        if target_text_quote:
            ai_message = f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🤖 AI Facilitator\n📍 Regarding: \"{target_text_quote}\"\n\n{comment_text}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        else:
            ai_message = f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🤖 AI Facilitator\n\n{comment_text}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        message_length = len(ai_message)

        # Create batchUpdate requests
        requests = [
            # 1. Insert the text
            {
                "insertText": {
                    "location": {"index": insert_index},
                    "text": ai_message
                }
            },
            # 2. Style the entire block (light blue background, italic)
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": insert_index,
                        "endIndex": insert_index + message_length
                    },
                    "textStyle": {
                        "backgroundColor": {
                            "color": {
                                "rgbColor": {
                                    "red": 0.85,
                                    "green": 0.92,
                                    "blue": 1.0
                                }
                            }
                        },
                        "italic": True,
                        "fontSize": {
                            "magnitude": 11,
                            "unit": "PT"
                        }
                    },
                    "fields": "backgroundColor,italic,fontSize"
                }
            }
        ]

        # If we have a quoted context, make it bold for emphasis
        if target_text_quote:
            # Find the position of the quoted text in the ai_message
            quote_start = ai_message.find(f'"{target_text_quote}"')
            if quote_start != -1:
                requests.append({
                    "updateTextStyle": {
                        "range": {
                            "startIndex": insert_index + quote_start,
                            "endIndex": insert_index + quote_start + len(target_text_quote) + 2  # +2 for quotes
                        },
                        "textStyle": {
                            "bold": True,
                            "foregroundColor": {
                                "color": {
                                    "rgbColor": {
                                        "red": 0.2,
                                        "green": 0.3,
                                        "blue": 0.6
                                    }
                                }
                            }
                        },
                        "fields": "bold,foregroundColor"
                    }
                })

        # Call Google Docs API
        result = self.docs_api_client.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()

        # Generate a pseudo comment ID for tracking
        comment_id = f"text_{insert_index}_{int(time.time())}"

        return {
            "commentId": comment_id,
            "success": True,
            "insertIndex": insert_index
        }

    def post_comment(
        self,
        comment: Dict[str, Any],
        queue_on_limit: bool = False
    ) -> Dict[str, Any]:
        """Post comment to Google Docs"""
        document_id = comment.get("document_id")

        # Check rate limiting
        if not self.can_post_comment(document_id):
            if queue_on_limit:
                self.pending_queue.append(comment)
                return {"success": False, "queued": True, "message": "Rate limited, queued for later"}
            return {"success": False, "paused": True, "message": "Rate limit active"}

        # Check unresolved comment limit
        unresolved = self.unresolved_comments.get(document_id, 0)
        if unresolved >= self.max_unresolved_comments:
            if queue_on_limit:
                self.pending_queue.append(comment)
                return {"success": False, "queued": True, "message": "Too many unresolved comments"}
            return {"success": False, "paused": True, "message": "Too many unresolved comments"}

        # Handle text_position: can be None, a string (target text), or a dict (position)
        text_position = comment.get("text_position")
        position = None

        if text_position:
            if isinstance(text_position, str):
                # LLM provided target text - find its position in document
                position = self._find_text_position(text_position)
                if position is None:
                    # Text not found - post at top as fallback
                    print(f"   ⚠️  Target text not found in document, posting at top")
            elif isinstance(text_position, dict):
                # Already a position dict
                position = text_position

        # Check deduplication
        position_hash = self._hash_position(document_id, position)
        if position_hash in self.posted_comments:
            return {"success": False, "duplicate": True, "message": "Comment already posted at this position"}

        # Format comment
        formatted_comment = self.format_comment(comment)

        try:
            # Call API (with retry)
            result = self._call_docs_api({
                "document_id": document_id,
                "comment_text": formatted_comment,
                "position": position
            })

            # Track posted comment
            self.posted_comments[position_hash] = {
                "text": formatted_comment,
                "timestamp": datetime.now()
            }
            self.last_comment_time[document_id] = datetime.now()
            self.posting_history.append({
                "suggestion_id": comment.get("suggestion_id"),
                "document_id": document_id,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })

            return {
                "success": True,
                "comment_id": result.get("commentId"),
                "message": "Comment posted successfully"
            }

        except Exception as e:
            # Log failure
            self.failed_queue.append(comment)
            self.posting_history.append({
                "suggestion_id": comment.get("suggestion_id"),
                "document_id": document_id,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def post_batch_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post batch of comments respecting rate limits"""
        results = []
        for comment in comments:
            result = self.post_comment(comment, queue_on_limit=True)
            results.append(result)
            # Small delay between posts to respect rate limit
            if result.get("success"):
                time.sleep(0.5)
        return results

    def get_unresolved_comment_count(self, document_id: str) -> int:
        """Get count of unresolved comments for document"""
        return self.unresolved_comments.get(document_id, 0)

    def get_posting_statistics(self) -> Dict[str, Any]:
        """Get statistics on comment posting"""
        successful = sum(1 for h in self.posting_history if h.get("success"))
        failed = sum(1 for h in self.posting_history if not h.get("success"))
        total = len(self.posting_history)

        return {
            "total_attempted": total,
            "posted_count": successful,
            "failed_count": failed,
            "success_rate": successful / total if total > 0 else 0,
            "queued_count": len(self.pending_queue),
            "failed_queue_count": len(self.failed_queue)
        }
