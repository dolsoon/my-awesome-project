"""
Real Google Docs API Integration for Comment Posting
SPEC-AI-FACIL-001 Phase 3: Production-grade Google Docs API integration
Replaces mock comment posting with real documents.batchUpdate API calls
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleDocsAPIService:
    """Real Google Docs API integration for posting comments"""

    # Rate limiting configuration
    DEFAULT_RATE_LIMIT_SECONDS = 60
    DEFAULT_MAX_UNRESOLVED = 5

    # Retry configuration
    RETRY_MAX_ATTEMPTS = 3
    RETRY_INITIAL_DELAY = 1.0
    RETRY_MAX_DELAY = 10.0

    def __init__(
        self,
        docs_api_client,
        rate_limit_seconds: int = DEFAULT_RATE_LIMIT_SECONDS,
        max_unresolved: int = DEFAULT_MAX_UNRESOLVED
    ):
        """Initialize Google Docs API service"""
        self.docs_api_client = docs_api_client
        self.rate_limit_seconds = rate_limit_seconds
        self.max_unresolved_comments = max_unresolved

        # Track rate limiting and comments per document
        self.last_comment_time: Dict[str, datetime] = {}
        self.unresolved_comments: Dict[str, int] = {}
        self.posted_comments: Dict[str, Dict] = {}  # comment_hash -> comment metadata
        self.pending_queue: List[Dict] = []  # Comments waiting to be posted
        self.failed_queue: List[Dict] = []  # Comments that failed
        self.posting_history: List[Dict] = []  # Complete history of all posts

        logger.info(f"Initialized GoogleDocsAPIService with rate limit {rate_limit_seconds}s")

    def format_comment(self, comment: Dict[str, Any]) -> str:
        """Format comment with metadata"""
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

    def _find_text_position(
        self,
        document_id: str,
        target_text: str
    ) -> Optional[Dict]:
        """Find position of target text in document using API"""
        try:
            # Fetch document to find text position
            doc = self.docs_api_client.documents().get(
                documentId=document_id
            ).execute()

            # Search through document content
            if "body" not in doc or "content" not in doc["body"]:
                logger.warning(f"Document {document_id} has no body content")
                return None

            current_index = 0
            for element in doc["body"]["content"]:
                if "paragraph" in element:
                    for sub_element in element["paragraph"].get("elements", []):
                        if "textRun" in sub_element:
                            text = sub_element["textRun"].get("content", "")
                            if target_text in text:
                                # Found the text
                                start_index = current_index + text.find(target_text)
                                return {
                                    "index": start_index,
                                    "length": len(target_text)
                                }
                            current_index += len(text)

            logger.warning(f"Target text not found in document {document_id}")
            return None

        except HttpError as e:
            logger.error(f"Error finding text position: {str(e)}")
            return None

    def _create_comment_request(
        self,
        comment_text: str,
        position: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a comment request for batchUpdate API"""
        if position is None:
            # Create quote-based comment at end of document
            return {
                "createComment": {
                    "comment": {
                        "content": comment_text,
                        "quotedTextRange": {
                            "startIndex": 1,
                            "endIndex": 2
                        }
                    }
                }
            }
        else:
            # Create position-based comment
            return {
                "createComment": {
                    "comment": {
                        "content": comment_text,
                        "anchor": {
                            "tabId": "",
                            "bounds": {
                                "startIndex": position["index"],
                                "endIndex": position["index"] + position["length"]
                            }
                        }
                    }
                }
            }

    def _call_docs_api_with_retry(
        self,
        document_id: str,
        requests: List[Dict]
    ) -> Optional[Dict]:
        """Call Google Docs API with retry logic"""
        attempt = 0
        delay = self.RETRY_INITIAL_DELAY

        while attempt < self.RETRY_MAX_ATTEMPTS:
            try:
                logger.debug(f"Calling Docs API (attempt {attempt + 1}/{self.RETRY_MAX_ATTEMPTS})")

                result = self.docs_api_client.documents().batchUpdate(
                    documentId=document_id,
                    body={"requests": requests}
                ).execute()

                logger.info(f"Docs API call successful")
                return result

            except HttpError as e:
                status_code = e.resp.status
                logger.warning(f"HTTP {status_code}: {str(e)}")

                # Handle specific error codes
                if status_code == 429:
                    # Rate limited - retry with backoff
                    attempt += 1
                    if attempt < self.RETRY_MAX_ATTEMPTS:
                        logger.info(f"Rate limited, retrying in {delay}s")
                        time.sleep(delay)
                        delay = min(delay * self.RETRY_MAX_DELAY, self.RETRY_MAX_DELAY)
                    else:
                        logger.error("Max retries exceeded for rate limit")
                        return None

                elif status_code == 400:
                    # Bad request - don't retry
                    logger.error(f"Bad request (400): {str(e)}")
                    return None

                elif status_code == 403:
                    # Permission denied
                    logger.error(f"Permission denied (403): {str(e)}")
                    return None

                elif status_code in [500, 502, 503]:
                    # Server error - retry
                    attempt += 1
                    if attempt < self.RETRY_MAX_ATTEMPTS:
                        logger.info(f"Server error, retrying in {delay}s")
                        time.sleep(delay)
                        delay = min(delay * self.RETRY_MAX_DELAY, self.RETRY_MAX_DELAY)
                    else:
                        logger.error("Max retries exceeded for server error")
                        return None
                else:
                    # Other error
                    logger.error(f"API error {status_code}: {str(e)}")
                    return None

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                attempt += 1
                if attempt < self.RETRY_MAX_ATTEMPTS:
                    time.sleep(delay)
                    delay = min(delay * self.RETRY_MAX_DELAY, self.RETRY_MAX_DELAY)
                else:
                    return None

        return None

    def post_comment(
        self,
        document_id: str,
        comment_text: str,
        target_text: Optional[str] = None,
        mode: str = "default",
        confidence: float = 0.8,
        queue_on_limit: bool = False
    ) -> Dict[str, Any]:
        """Post a comment to Google Docs"""
        logger.info(f"Attempting to post comment to {document_id} with mode={mode}")

        # Check rate limiting
        if not self.can_post_comment(document_id):
            if queue_on_limit:
                comment_data = {
                    "document_id": document_id,
                    "comment_text": comment_text,
                    "target_text": target_text,
                    "mode": mode,
                    "confidence": confidence,
                    "queued_at": datetime.now().isoformat()
                }
                self.pending_queue.append(comment_data)
                logger.info(f"Comment queued due to rate limit")
                return {
                    "success": False,
                    "queued": True,
                    "message": "Rate limited, queued for later"
                }
            return {
                "success": False,
                "paused": True,
                "message": "Rate limit active"
            }

        # Check unresolved comment limit
        unresolved = self.unresolved_comments.get(document_id, 0)
        if unresolved >= self.max_unresolved_comments:
            if queue_on_limit:
                comment_data = {
                    "document_id": document_id,
                    "comment_text": comment_text,
                    "target_text": target_text,
                    "mode": mode,
                    "confidence": confidence,
                    "queued_at": datetime.now().isoformat()
                }
                self.pending_queue.append(comment_data)
                logger.info(f"Comment queued due to unresolved limit")
                return {
                    "success": False,
                    "queued": True,
                    "message": "Too many unresolved comments"
                }
            return {
                "success": False,
                "paused": True,
                "message": "Too many unresolved comments"
            }

        try:
            # Find text position if target text provided
            position = None
            if target_text:
                position = self._find_text_position(document_id, target_text)

            # Format comment with metadata
            formatted_comment = self.format_comment({
                "comment_text": comment_text,
                "mode": mode,
                "confidence": confidence
            })

            # Create comment request
            comment_request = self._create_comment_request(formatted_comment, position)

            # Call API with retry
            result = self._call_docs_api_with_retry(
                document_id,
                [comment_request]
            )

            if result is None:
                logger.error("Failed to post comment after retries")
                self.failed_queue.append({
                    "document_id": document_id,
                    "comment_text": comment_text,
                    "failed_at": datetime.now().isoformat(),
                    "reason": "API call failed"
                })
                return {
                    "success": False,
                    "error": "API call failed"
                }

            # Success
            self.last_comment_time[document_id] = datetime.now()
            self.unresolved_comments[document_id] = unresolved + 1

            comment_id = result.get("replies", [{}])[0].get("createComment", {}).get("commentId")

            history_entry = {
                "document_id": document_id,
                "comment_id": comment_id,
                "text": comment_text,
                "mode": mode,
                "confidence": confidence,
                "posted_at": datetime.now().isoformat(),
                "status": "posted"
            }
            self.posting_history.append(history_entry)

            logger.info(f"Comment posted successfully: {comment_id}")
            return {
                "success": True,
                "comment_id": comment_id,
                "message": "Comment posted successfully"
            }

        except Exception as e:
            logger.error(f"Error posting comment: {str(e)}")
            self.failed_queue.append({
                "document_id": document_id,
                "comment_text": comment_text,
                "failed_at": datetime.now().isoformat(),
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e)
            }

    def resolve_comment(self, document_id: str, comment_id: str) -> bool:
        """Mark a comment as resolved"""
        try:
            logger.info(f"Resolving comment {comment_id}")
            unresolved = self.unresolved_comments.get(document_id, 0)
            if unresolved > 0:
                self.unresolved_comments[document_id] = unresolved - 1
            return True
        except Exception as e:
            logger.error(f"Error resolving comment: {str(e)}")
            return False

    def get_posting_statistics(self) -> Dict[str, Any]:
        """Get statistics about comment posting"""
        total_posted = len(self.posting_history)
        total_failed = len(self.failed_queue)
        success_rate = (total_posted / (total_posted + total_failed) * 100
                       if (total_posted + total_failed) > 0 else 0)

        return {
            "total_posted": total_posted,
            "total_failed": total_failed,
            "success_rate": success_rate,
            "pending_queue_size": len(self.pending_queue),
            "unique_documents": len(self.last_comment_time),
            "total_unresolved": sum(self.unresolved_comments.values())
        }

    def process_pending_queue(self) -> Dict[str, Any]:
        """Process pending comments in queue"""
        logger.info(f"Processing {len(self.pending_queue)} pending comments")
        processed = 0
        failed = 0

        while self.pending_queue:
            comment = self.pending_queue.pop(0)

            result = self.post_comment(
                document_id=comment["document_id"],
                comment_text=comment["comment_text"],
                target_text=comment.get("target_text"),
                mode=comment.get("mode", "default"),
                confidence=comment.get("confidence", 0.8),
                queue_on_limit=False  # Don't queue again
            )

            if result.get("success"):
                processed += 1
            else:
                failed += 1
                # Re-queue if it's a rate limit issue
                if "rate" in result.get("message", "").lower():
                    self.pending_queue.append(comment)

        logger.info(f"Queue processing complete: {processed} posted, {failed} failed")
        return {
            "processed": processed,
            "failed": failed,
            "remaining_in_queue": len(self.pending_queue)
        }
