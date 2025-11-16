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
        self.current_document_structure: Optional[Dict] = None  # Store structured content

    def format_comment(self, comment: Dict[str, Any]) -> str:
        """Format comment (just return the text, no metadata)"""
        # Return comment text directly without metadata
        return comment.get("comment_text", "")

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

    def _extract_plain_text(self, doc: Dict) -> str:
        """Extract plain text from document structure"""
        body = doc.get("body", {})
        content = body.get("content", [])
        text_parts = []

        for element in content:
            if "paragraph" not in element:
                continue

            paragraph = element["paragraph"]
            elements = paragraph.get("elements", [])

            for text_element in elements:
                if "textRun" not in text_element:
                    continue

                text_run = text_element["textRun"]
                content_text = text_run.get("content", "")
                text_parts.append(content_text)

        return "".join(text_parts)

    def _find_text_position(self, target_text: str) -> Optional[Dict]:
        """Find position of target text in document using structural content"""
        if not target_text:
            print(f"   ❌ DEBUG: Empty target_text")
            return None

        print(f"\n🔍 DEBUG - Text Matching (Structural):")
        print(f"   Target text: '{target_text}'")
        print(f"   Target length: {len(target_text)} chars")

        # Use structural content if available (accurate indices)
        if self.current_document_structure:
            return self._find_in_structure(target_text)

        # Fallback to plain text search (less accurate)
        if not self.current_document_text:
            print(f"   ❌ DEBUG: No document content available")
            return None

        print(f"   ⚠️  Using plain text fallback (may be inaccurate)")
        print(f"   Document length: {len(self.current_document_text)} chars")

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

        print(f"   ❌ No match found")
        return None

    def _find_paragraph_end(self, start_index: int) -> int:
        """Find the end of paragraph (next newline) after start_index"""
        if not self.current_document_structure:
            return start_index

        body = self.current_document_structure.get("body", {})
        content = body.get("content", [])

        # Walk through structural elements to find newline after start_index
        for element in content:
            if "paragraph" not in element:
                continue

            paragraph = element["paragraph"]
            elements = paragraph.get("elements", [])

            for text_element in elements:
                if "textRun" not in text_element:
                    continue

                text_run = text_element["textRun"]
                content_text = text_run.get("content", "")
                elem_start = text_element.get("startIndex")
                elem_end = text_element.get("endIndex")

                # If this element is after our start_index and contains newline
                if elem_start >= start_index and "\n" in content_text:
                    # Find first newline position
                    newline_offset = content_text.find("\n")
                    return elem_start + newline_offset + 1  # After the newline

        # If no newline found, return original position
        return start_index

    def _find_in_structure(self, target_text: str) -> Optional[Dict]:
        """Search for target text in document structure (accurate indices)"""
        if not self.current_document_structure:
            return None

        target_lower = target_text.lower()
        body = self.current_document_structure.get("body", {})
        content = body.get("content", [])

        print(f"   📊 Searching {len(content)} structural elements")

        # Build a complete text map with index positions
        full_text = ""
        index_map = []  # List of (char_position_in_full_text, structural_index)

        for element in content:
            if "paragraph" not in element:
                continue

            paragraph = element["paragraph"]
            elements = paragraph.get("elements", [])

            for text_element in elements:
                if "textRun" not in text_element:
                    continue

                text_run = text_element["textRun"]
                content_text = text_run.get("content", "")
                start_index = text_element.get("startIndex")

                # Record the mapping between full_text position and structural index
                for i, char in enumerate(content_text):
                    index_map.append((len(full_text) + i, start_index + i))

                full_text += content_text

        # Search for target in the full text
        if target_lower in full_text.lower():
            # Find position in full_text
            text_position = full_text.lower().find(target_lower)

            # Look up the structural index for this position
            if text_position < len(index_map):
                _, structural_index = index_map[text_position]

                print(f"   ✅ Match found at text position {text_position}")
                print(f"   📍 Structural index: {structural_index}")

                return {
                    "index": structural_index,
                    "length": len(target_text)
                }

        print(f"   ❌ Target text not found in document structure")
        return None

    def _call_docs_api(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Insert AI facilitation text directly into the document with formatting"""
        document_id = request["document_id"]
        comment_text = request["comment_text"]
        position = request.get("position")
        target_text = request.get("target_text")  # Original target text from LLM

        # Determine insertion position
        if position and isinstance(position, dict):
            # Find the end of the paragraph containing the target text
            target_end_index = position["index"] + position["length"]

            # Find next paragraph break (newline) after target text
            insert_index = self._find_paragraph_end(target_end_index)
            print(f"   📍 Inserting after paragraph at index {insert_index}")
        else:
            # Fallback: Insert at top when position not found
            insert_index = 1
            print(f"   ⚠️  Position not found, inserting at top")

        # Format the AI message with context (Jaemin style - will apply bullet formatting)
        if target_text:
            # Extract first 40 chars of quote for context (preserve word boundaries)
            if len(target_text) > 40:
                # Find last space within 40 chars to avoid cutting words
                preview_cutoff = target_text[:40].rfind(' ')
                if preview_cutoff == -1:
                    preview_cutoff = 40
                quote_preview = target_text[:preview_cutoff] + "..."
            else:
                quote_preview = target_text

            ai_message = f"Jaemin: Re: \"{quote_preview}\" — {comment_text}\n"
        else:
            ai_message = f"Jaemin: {comment_text}\n"

        message_length = len(ai_message)

        # Create batchUpdate requests with compact styling
        requests = [
            # 1. Insert the text
            {
                "insertText": {
                    "location": {"index": insert_index},
                    "text": ai_message
                }
            },
            # 2. Style the entire comment (light blue background)
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
                        "fontSize": {
                            "magnitude": 10,
                            "unit": "PT"
                        }
                    },
                    "fields": "backgroundColor,fontSize"
                }
            }
        ]

        # Make "Jaemin:" bold
        jaemin_end = ai_message.find(":")
        if jaemin_end != -1:
            requests.append({
                "updateTextStyle": {
                    "range": {
                        "startIndex": insert_index + ai_message.find("Jaemin"),
                        "endIndex": insert_index + jaemin_end + 1
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

        # Apply bullet list formatting (proper Google Docs bullet, not character)
        requests.append({
            "createParagraphBullets": {
                "range": {
                    "startIndex": insert_index,
                    "endIndex": insert_index + message_length - 1  # Exclude trailing newline
                },
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
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
        target_text = None  # Store original target text for quote

        if text_position:
            if isinstance(text_position, str):
                # LLM provided target text - store it
                target_text = text_position

                # REFRESH DOCUMENT: Re-fetch to get current state (handles live collaboration)
                print(f"   🔄 Refreshing document to get current state...")
                try:
                    fresh_doc = self.docs_api_client.documents().get(
                        documentId=document_id
                    ).execute()
                    self.current_document_structure = fresh_doc
                    self.current_document_text = self._extract_plain_text(fresh_doc)
                    print(f"   ✅ Document refreshed")
                except Exception as e:
                    print(f"   ⚠️  Failed to refresh document: {e}")
                    # Continue with existing structure

                # Re-find position in fresh document
                position = self._find_text_position(text_position)
                if position is None:
                    # Text not found - might have been edited/deleted
                    print(f"   ⚠️  Target text not found in current document")
                    print(f"   💡 Possible reasons: text edited/deleted by collaborators")
                    return {
                        "success": False,
                        "error": "Target text not found in current document state",
                        "suggestion": "Text may have been edited/deleted. Try analyzing again."
                    }
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
                "position": position,
                "target_text": target_text  # Pass original target text for accurate quote
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
