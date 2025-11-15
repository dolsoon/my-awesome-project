"""
Document Monitor Service
Monitors Google Docs for changes and manages batch processing
"""

import time
from typing import Dict, List, Optional


class DocumentMonitor:
    """Monitors Google Docs for changes and tracks revisions"""

    def __init__(self, google_client, oauth_handler):
        """Initialize document monitor"""
        self.google_client = google_client
        self.oauth_handler = oauth_handler
        self.watched_documents: Dict[str, Dict] = {}
        self.revision_history: Dict[str, List[str]] = {}
        self.last_change_timestamp: Dict[str, float] = {}
        self.batch_interval: int = 60  # seconds

    def register_document(self, doc_id: str) -> None:
        """Register a document for monitoring"""
        self.watched_documents[doc_id] = {
            "last_revision": None,
            "registered_at": time.time(),
        }
        self.revision_history[doc_id] = []

    def fetch_document_content(self, doc_id: str) -> Dict:
        """Fetch full document content from Google Docs API"""
        docs_service = self.google_client.documents()
        result = docs_service.get(documentId=doc_id).execute()
        return result

    def track_revision(self, doc_id: str, revision_id: str) -> None:
        """Track a document revision for deduplication"""
        if doc_id not in self.revision_history:
            self.revision_history[doc_id] = []

        self.revision_history[doc_id].append(revision_id)
        self.watched_documents[doc_id]["last_revision"] = revision_id

    def get_last_revision(self, doc_id: str) -> Optional[str]:
        """Get the last tracked revision ID"""
        return self.watched_documents.get(doc_id, {}).get("last_revision")

    def has_changes_since_revision(self, doc_id: str, new_revision: str) -> bool:
        """Check if there are changes since last revision"""
        last_revision = self.get_last_revision(doc_id)
        return last_revision != new_revision if last_revision else True

    def extract_text_from_document(self, doc_id: str) -> str:
        """Extract plain text from document"""
        doc = self.fetch_document_content(doc_id)
        text_parts = []

        if "body" in doc and "content" in doc["body"]:
            for element in doc["body"]["content"]:
                if "paragraph" in element:
                    for sub_element in element["paragraph"].get("elements", []):
                        if "textRun" in sub_element:
                            text_parts.append(sub_element["textRun"].get("content", ""))

        return "".join(text_parts)

    def get_documents_for_batch(self) -> List[str]:
        """Get list of documents to process in next batch"""
        return list(self.watched_documents.keys())

    def is_duplicate_revision(self, doc_id: str, revision_id: str) -> bool:
        """Check if revision has already been processed"""
        if doc_id in self.watched_documents:
            last_revision = self.watched_documents[doc_id].get("last_revision")
            return last_revision == revision_id if last_revision else False
        return False

    def get_revision_history(self, doc_id: str) -> List[str]:
        """Get revision history for a document"""
        return self.revision_history.get(doc_id, [])

    def record_change_timestamp(self, doc_id: str, timestamp: float) -> None:
        """Record when a document change was detected"""
        self.last_change_timestamp[doc_id] = timestamp

    def get_last_change_timestamp(self, doc_id: str) -> Optional[float]:
        """Get timestamp of last change"""
        return self.last_change_timestamp.get(doc_id)

    def set_batch_interval(self, interval: int) -> None:
        """Set batch processing interval in seconds"""
        self.batch_interval = interval
