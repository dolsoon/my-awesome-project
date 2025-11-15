# Acceptance Criteria: SPEC-AI-FACIL-001

## TAG BLOCK
```yaml
---
spec_id: SPEC-AI-FACIL-001
acceptance_version: 1.1.0
created: 2025-11-15
updated: 2025-11-15
status: ready
test_framework: pytest
coverage_target: 85%
---
```

## Overview

This document defines the detailed acceptance criteria and test scenarios for the AI Facilitator Agent for Google Docs collaboration. All scenarios use **Given-When-Then** format for clarity and testability.

## REVISION HISTORY

### Version 1.1.0 (2025-11-15)
- **REMOVED**: Phase 5 dashboard scenarios (AC-5.1 through AC-5.6)
- **ADDED**: Terminal interface scenarios (AC-4.9 through AC-4.15)
- **CHANGED**: Phase 5 renamed to "Production Hardening & Research Data Collection"
- **ADDED**: Research validation criteria with approval rate >60% target
- **UPDATED**: Quality gates to focus on researcher approval metrics

## Quality Gates

Before production release, the system MUST meet:

1. **Functional Completeness**: All primary scenarios pass ✅
2. **Performance Targets**: 95th percentile latencies within spec limits
3. **Reliability Threshold**: 99.5% uptime during 7-day soak test
4. **Security Audit**: Zero critical/high vulnerabilities
5. **Test Coverage**: ≥85% code coverage for critical paths
6. **Human Validation**: ≥4/5 facilitator satisfaction rating
7. **Cost Efficiency**: <$5 per 1000 contributions analyzed
8. **Research Validation**: Researcher approval rate >60% for AI suggestions
9. **Terminal UI Usability**: Researcher can complete approval workflow in <30 seconds per suggestion
10. **Research Data Quality**: 100% of decisions logged with complete metadata

---

## Phase 1: Foundation & Google API Integration

### AC-1.1: OAuth Authentication Flow

**Given** a user initiates authentication for the first time
**When** they visit `/auth/login` endpoint
**Then** they are redirected to Google OAuth consent screen
**And** after granting permissions (Drive readonly, Docs), they are redirected back to `/auth/callback`
**And** the system stores encrypted refresh tokens (AES-256) in secure storage
**And** the system displays "Authentication successful" message

**Test Data**:
- Valid Google account with Workspace access
- OAuth scopes: `drive.readonly`, `documents`

**Verification**:
```bash
# Unit test: Mock OAuth flow
pytest tests/test_auth.py::test_oauth_flow_success

# Integration test: Real Google OAuth
pytest tests/integration/test_google_auth.py --google-credentials
```

---

### AC-1.2: Automatic Token Refresh

**Given** a user has authenticated with OAuth tokens
**When** the access token expires (after 3600 seconds)
**Then** the system automatically refreshes the token using stored refresh token
**And** the new access token is used for subsequent API calls
**And** no user re-authentication is required

**Test Data**:
- Expired access token (mock or wait 1 hour)
- Valid refresh token

**Verification**:
```bash
pytest tests/test_auth.py::test_token_auto_refresh
```

---

### AC-1.3: Document Change Detection

**Given** a Google Doc is registered for monitoring
**When** the system subscribes to change notifications via Drive API `files.watch`
**Then** a push notification is received within 90-120 seconds of document edit
**And** the document is added to the batch processing queue
**And** the notification includes document ID and revision number

**Test Data**:
- Shared Google Doc with edit permissions
- Webhook endpoint exposed via ngrok or public URL

**Verification**:
```bash
# Integration test: Trigger document edit and verify notification
pytest tests/integration/test_drive_notification.py --live-doc
```

---

### AC-1.4: Batch Processing Scheduler

**Given** the batch processing scheduler is running
**When** the configured interval (90-120 seconds) elapses
**Then** Celery beat triggers batch processing task
**And** all documents in the queue are processed
**And** the scheduler runs continuously without missed cycles
**And** each batch processing job is logged with correlation ID

**Test Data**:
- 3 documents in queue with recent changes
- Batch interval: 100 seconds (configurable)

**Verification**:
```bash
# Unit test: Mock scheduler
pytest tests/test_scheduler.py::test_batch_interval_trigger

# Integration test: Live scheduler for 5 minutes
pytest tests/integration/test_scheduler_reliability.py --duration 300
```

---

### AC-1.5: Document Change Fetching

**Given** a document has new revisions since last processing
**When** the batch processor fetches document content via Docs API `documents.get`
**Then** the system retrieves all text changes since last processed revision ID
**And** the system extracts text segments with author attribution
**And** the system updates last processed revision ID
**And** no duplicate changes are processed

**Test Data**:
- Document with 5 new paragraphs by 3 different authors
- Last processed revision ID: `rev_abc123`
- Current revision ID: `rev_def456`

**Verification**:
```bash
# Unit test: Mock Docs API response
pytest tests/test_document_fetcher.py::test_fetch_new_changes

# Integration test: Real document changes
pytest tests/integration/test_docs_api.py::test_fetch_incremental_changes
```

---

### AC-1.6: API Error Handling with Backoff

**Given** the system calls Google Docs API
**When** a 429 (rate limit) error is returned
**Then** the system waits 1 second and retries
**And** if the second attempt fails, waits 2 seconds
**And** if the third attempt fails, waits 4 seconds (exponential backoff)
**And** after 3 failures, the system logs the error and alerts human facilitator
**And** the batch processing continues with remaining documents

**Test Data**:
- Mock Docs API returning 429 errors
- Retry intervals: 1s, 2s, 4s

**Verification**:
```bash
pytest tests/test_api_error_handling.py::test_rate_limit_backoff
```

---

## Phase 2: Embedding & Vector Database Integration

### AC-2.1: SBERT Embedding Generation

**Given** 10 text segments extracted from document changes
**When** the embedding service generates vectors using SBERT (`all-mpnet-base-v2`)
**Then** 10 embeddings are created with dimension 768
**And** all vectors are normalized to unit length (L2 norm = 1.0)
**And** embedding generation completes in <5 seconds
**And** all embeddings are non-zero vectors

**Test Data**:
- 10 paragraphs (50-200 words each)
- Expected embedding dimension: 768
- Expected throughput: >100 segments/minute

**Verification**:
```bash
pytest tests/test_embedding_service.py::test_sbert_generation
```

---

### AC-2.2: Gemini Embedding Generation

**Given** the system is configured to use Gemini embeddings
**When** 20 text segments are sent to Gemini `embedding-001` API
**Then** 20 embeddings are returned with dimension 768
**And** all vectors are normalized to unit length
**And** API call completes in <8 seconds (batched)
**And** the system handles API errors gracefully (retry once)

**Test Data**:
- 20 sentences (20-50 words each)
- Gemini API key configured
- Expected dimension: 768

**Verification**:
```bash
pytest tests/test_embedding_service.py::test_gemini_generation --gemini-api-key
```

---

### AC-2.3: Vector Storage in ChromaDB

**Given** 100 embeddings are generated with metadata
**When** the system stores them in ChromaDB
**Then** all 100 embeddings are persisted with metadata:
  - `text`: Original text segment
  - `author`: User email or ID
  - `timestamp`: ISO 8601 timestamp
  - `document_id`: Google Doc ID
  - `position`: Character offset in document
**And** embeddings are retrievable by document_id filter
**And** storage operation completes in <3 seconds

**Test Data**:
- 100 embeddings with varying authors and timestamps
- Document ID: `doc_12345`

**Verification**:
```bash
pytest tests/test_vector_db.py::test_chromadb_storage
```

---

### AC-2.4: Similarity Search Performance

**Given** ChromaDB contains 10,000 stored embeddings
**When** the system performs cosine similarity search with a query vector
**Then** the top 20 most similar embeddings are returned
**And** the search completes in <2 seconds
**And** all results have cosine similarity scores between -1.0 and 1.0
**And** results are sorted by similarity (descending)

**Test Data**:
- 10,000 pre-stored embeddings
- Query vector: New text segment embedding
- Expected top-k: 20

**Verification**:
```bash
pytest tests/test_vector_db.py::test_similarity_search_performance --benchmark
```

---

### AC-2.5: Embedding API Failure Handling

**Given** the SBERT or Gemini API fails for 3 consecutive text segments
**When** the embedding service attempts to generate vectors
**Then** the system logs the failures with text samples
**And** the system continues processing remaining segments
**And** the system alerts if >20% of segments fail in a batch
**And** failed segments are queued for retry with exponential backoff

**Test Data**:
- Mock embedding API returning errors
- Batch of 10 segments, 3 failures

**Verification**:
```bash
pytest tests/test_embedding_service.py::test_failure_handling
```

---

## Phase 3: Analysis Engine (Outlier Detection & Related Ideas)

### AC-3.1: Outlier Detection with Low Similarity

**Given** 20 text segments are stored in vector database with high similarity (>0.8)
**When** a new text segment is added with average similarity 0.4 to all others
**Then** the system identifies it as an outlier
**And** the novelty score is calculated: `(1 - 0.4) * length_weight`
**And** the outlier is ranked as #1 in the batch
**And** the outlier is logged with text, author, and similarity scores

**Test Data**:
- 20 similar embeddings (cosine similarity >0.8)
- 1 outlier embedding (average similarity 0.4)
- Outlier threshold: 0.6

**Verification**:
```bash
pytest tests/test_analysis_engine.py::test_outlier_detection_low_similarity
```

---

### AC-3.2: No Outliers Detected (All Similar)

**Given** 30 text segments with average pairwise similarity >0.75
**When** the analysis engine processes the batch
**Then** zero outliers are detected
**And** no outlier alerts are generated
**And** the system logs "No outliers found in batch"

**Test Data**:
- 30 similar embeddings (all discussing the same topic)
- Average similarity >0.75

**Verification**:
```bash
pytest tests/test_analysis_engine.py::test_no_outliers_high_similarity
```

---

### AC-3.3: Top 3 Outliers Ranked by Novelty

**Given** a batch contains 5 outliers with varying novelty scores:
  - Outlier A: novelty 0.9 (very unique, long text)
  - Outlier B: novelty 0.7 (moderately unique, medium text)
  - Outlier C: novelty 0.65 (slightly unique, short text)
  - Outlier D: novelty 0.6 (barely unique, long text)
  - Outlier E: novelty 0.55 (low uniqueness)
**When** the system ranks outliers
**Then** only the top 3 are selected: A, B, D
**And** they are ordered by novelty score (descending)
**And** outliers C and E are logged but not processed further

**Test Data**:
- 5 outliers with known novelty scores
- Max outliers per batch: 3

**Verification**:
```bash
pytest tests/test_analysis_engine.py::test_top3_outliers_ranking
```

---

### AC-3.4: Related Idea Connection (Same Authors Excluded)

**Given** 10 text segments from 5 different authors
**When** two segments from Author A have similarity 0.82
**And** two segments from Authors B and C have similarity 0.78
**Then** only the B-C pair is identified as a "related idea" connection
**And** the A-A pair is excluded (same author)
**And** the related pair is logged with both authors and similarity score

**Test Data**:
- 10 embeddings from 5 authors
- 2 high-similarity pairs (1 same author, 1 different authors)
- Related similarity threshold: 0.75

**Verification**:
```bash
pytest tests/test_analysis_engine.py::test_related_ideas_different_authors
```

---

### AC-3.5: Convergent Theme Detection (≥3 Authors)

**Given** 15 text segments discussing "sustainability" from 4 authors
**When** hierarchical clustering groups them into a cluster with similarity >0.7
**And** the cluster contains segments from Authors A, B, C, D
**Then** the system identifies this as a "convergent theme"
**And** the theme is logged with author list and representative text samples
**And** the system prioritizes this for LLM review

**Test Data**:
- 15 embeddings about sustainability
- 4 different authors
- Clustering threshold: 0.7

**Verification**:
```bash
pytest tests/test_analysis_engine.py::test_convergent_theme_detection
```

---

### AC-3.6: Moving Window Eviction (Last 100 Contributions)

**Given** the vector database contains 100 contributions for a document
**When** 10 new contributions are added
**Then** the 10 oldest contributions are evicted from the active window
**And** the active window maintains exactly 100 contributions
**And** evicted embeddings are archived for long-term analytics
**And** similarity search only uses active window embeddings

**Test Data**:
- 100 pre-stored embeddings with timestamps
- 10 new embeddings
- Window size: 100

**Verification**:
```bash
pytest tests/test_analysis_engine.py::test_moving_window_eviction
```

---

### AC-3.7: Duplicate Outlier Suppression

**Given** Outlier X was detected in batch N
**When** the same text (or 95% similar) is detected as outlier in batch N+1
**Then** the system suppresses the duplicate alert
**And** the recurrence counter for Outlier X is incremented
**And** the system logs "Duplicate outlier suppressed: X (recurrence: 2)"
**And** no LLM decision is triggered for the duplicate

**Test Data**:
- Same outlier text in 2 consecutive batches
- Similarity threshold for duplicate: 0.95

**Verification**:
```bash
pytest tests/test_analysis_engine.py::test_duplicate_outlier_suppression
```

---

## Phase 4: LLM Decision Service & Comment Posting

### AC-4.1: LLM Decision Approval (High Confidence)

**Given** an outlier is detected with novelty score 0.85
**When** the LLM decision service constructs a prompt including:
  - Original outlier text
  - Similarity scores
  - Author metadata
  - Document context (previous 500 words)
**And** sends it to Gemini `gemini-1.5-pro`
**Then** the LLM returns structured JSON: `{should_comment: true, comment_text: "...", confidence: 0.9}`
**And** the decision latency is <10 seconds
**And** the comment is approved for posting

**Test Data**:
- Outlier text: "What if we use blockchain for decentralized governance?"
- Document context: Discussion about team decision-making
- Expected LLM response: Approve with relevant comment

**Verification**:
```bash
pytest tests/test_llm_service.py::test_llm_approval_high_confidence --gemini-api-key
```

---

### AC-4.2: LLM Decision Rejection (Low Confidence)

**Given** a marginal outlier is detected with novelty score 0.62
**When** the LLM evaluates the outlier
**Then** the LLM returns `{should_comment: false, comment_text: "", confidence: 0.5}`
**And** the system does NOT post a comment
**And** the decision is logged for human review
**And** the LLM rationale is stored for analysis

**Test Data**:
- Marginal outlier text: "I agree with the previous point."
- Expected LLM response: Reject (low value, redundant)

**Verification**:
```bash
pytest tests/test_llm_service.py::test_llm_rejection_low_confidence
```

---

### AC-4.3: LLM Timeout Fallback to Rule-Based

**Given** the LLM API call times out after 10 seconds
**When** the system detects the timeout
**Then** the system falls back to rule-based commenting
**And** uses conservative thresholds: novelty >0.8, similarity >0.85
**And** if thresholds are met, posts a generic comment: "[AI Facilitator] Unique idea detected: {outlier_text}"
**And** the system alerts the human facilitator about fallback mode
**And** the fallback decision is logged

**Test Data**:
- Mock LLM API with 15-second delay (timeout: 10s)
- High-novelty outlier (>0.8)

**Verification**:
```bash
pytest tests/test_llm_service.py::test_llm_timeout_fallback
```

---

### AC-4.4: Comment Posting to Google Docs

**Given** an LLM approves a comment with text: "Great outlier idea! Consider connecting this with earlier discussion on X."
**When** the comment posting service calls Docs API `documents.batchUpdate` with `createComment`
**Then** the comment is posted at the correct text position (character offset)
**And** the comment is formatted: `[AI Facilitator] Great outlier idea! Consider connecting this with earlier discussion on X.`
**And** the comment includes metadata in reply: `Confidence: 0.9 | Analysis: Outlier | Timestamp: 2025-11-15T10:30:00Z`
**And** the API call succeeds with 200 OK response

**Test Data**:
- Document ID: `doc_12345`
- Text position: Character offset 500
- Comment text from LLM

**Verification**:
```bash
pytest tests/integration/test_comment_posting.py::test_post_comment_success --live-doc
```

---

### AC-4.5: Comment Posting Rate Limiting

**Given** the system posted a comment to document X at timestamp T
**When** a new comment is approved for the same document at T+30 seconds
**Then** the system queues the comment instead of posting immediately
**And** the comment is posted at T+60 seconds (minimum 60-second interval)
**And** the system logs "Comment queued due to rate limit"

**Test Data**:
- Document ID: `doc_12345`
- 2 comments approved 30 seconds apart
- Rate limit: 1 comment per 60 seconds

**Verification**:
```bash
pytest tests/test_comment_posting.py::test_rate_limit_queuing
```

---

### AC-4.6: Comment Posting Paused (≥5 Unresolved Comments)

**Given** document X has 5 unresolved AI-generated comments
**When** a new comment is approved by LLM
**Then** the system does NOT post the comment
**And** the comment is queued with "Paused: too many unresolved comments" status
**And** when unresolved count drops to 3, the system resumes posting from queue
**And** the system logs "Comment posting paused for document X"

**Test Data**:
- Document with 5 unresolved comments
- 1 new approved comment

**Verification**:
```bash
pytest tests/test_comment_posting.py::test_pause_at_max_unresolved
```

---

### AC-4.7: Duplicate Comment Prevention

**Given** a comment was posted at text position 500 with content "Unique idea about blockchain governance"
**When** a similar outlier is detected at position 500 again
**Then** the system checks for existing comments at that position
**And** finds the existing comment (exact position match OR 95% text similarity)
**And** the system suppresses the duplicate comment
**And** logs "Duplicate comment suppressed at position 500"

**Test Data**:
- Existing comment at position 500
- New comment at same position with 96% similar text

**Verification**:
```bash
pytest tests/test_comment_posting.py::test_duplicate_comment_suppression
```

---

### AC-4.8: Comment Posting Retry on API Failure

**Given** the Docs API `batchUpdate` call fails with 503 (service unavailable)
**When** the comment posting service detects the failure
**Then** the system waits 5 seconds and retries once
**And** if the retry succeeds, the comment is posted successfully
**And** if the retry fails, the comment is logged to retry queue for manual review
**And** the system alerts the human facilitator

**Test Data**:
- Mock Docs API returning 503 on first call, 200 on second
- Comment text and position

**Verification**:
```bash
pytest tests/test_comment_posting.py::test_retry_on_api_failure
```

---

## Phase 4 (Terminal Interface): Additional Scenarios

### AC-4.9: Terminal UI Display Document Changes

**Given** the terminal interface is running and monitoring a document
**When** User A adds text: "We should prioritize mobile experience"
**Then** the terminal displays:
  - Timestamp: "2025-11-15 14:32:18"
  - Author: "user_a@example.com"
  - Text preview: "We should prioritize mobile experience" (full text if <200 chars)
  - Change type: "new paragraph"
**And** the display updates within 2 seconds of batch processing completion

**Test Data**:
- Active document monitoring
- New text contribution from User A

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_display_document_changes
```

---

### AC-4.10: Terminal UI Show Analysis Results

**Given** the analysis engine detects an outlier with novelty score 0.82
**When** the terminal UI receives the analysis result
**Then** the terminal displays:
  ```
  ╔════ OUTLIER DETECTED ════╗
  │ Type: Outlier Idea       │
  │ Novelty: 0.82           │
  │ Similarity: 0.35 (avg)  │
  │ Author: user_b@example  │
  │ Text: "What if we use..." │
  ╚══════════════════════════╝
  ```
**And** the display uses color coding (yellow for outlier)
**And** similarity scores show comparison to last 100 contributions

**Test Data**:
- Outlier detection result with known metrics

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_show_analysis_results
```

---

### AC-4.11: Researcher Approval Workflow (Approve)

**Given** the LLM generates comment: "Interesting outlier! This connects to earlier discussion on X."
**When** the terminal prompts: "Post this comment? (y/n/e/c)"
**And** the researcher types: "y"
**Then** the comment is posted to Google Docs immediately
**And** the terminal displays: "✓ Comment posted successfully"
**And** the decision is logged with: decision_type="approve", timestamp, researcher_id

**Test Data**:
- LLM-generated comment with 0.85 confidence
- Researcher input: "y"

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_researcher_approve
```

---

### AC-4.12: Researcher Approval Workflow (Edit)

**Given** the LLM generates comment: "Consider connecting this idea with sustainability theme"
**When** the terminal prompts: "Post this comment? (y/n/e/c)"
**And** the researcher types: "e"
**Then** the terminal opens inline editor with comment text
**And** the researcher edits to: "Great connection! Consider linking with sustainability discussion on page 2"
**And** after saving, the edited comment is posted
**And** the decision is logged with: decision_type="edit", original_suggestion, final_comment

**Test Data**:
- Original comment from LLM
- Edited comment from researcher

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_researcher_edit
```

---

### AC-4.13: On-Demand Analysis Command

**Given** the terminal interface is active
**When** the researcher types: "analyze from conflict resolution perspective"
**Then** the system constructs custom LLM prompt including:
  - Current document state
  - Recent contributions
  - Custom perspective: "conflict resolution"
**And** the LLM generates custom analysis within 10 seconds
**And** the terminal displays the analysis results
**And** the researcher can approve/reject as normal

**Test Data**:
- Command: "analyze from [perspective]"
- Custom perspective: "conflict resolution"

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_on_demand_analysis
```

---

### AC-4.14: Session Statistics Display

**Given** the terminal interface has processed 50 contributions in the session
**When** the researcher runs: "status"
**Then** the terminal displays:
  ```
  ╔════ SESSION STATISTICS ════╗
  │ Total Contributions: 50    │
  │ AI Suggestions: 8          │
  │ Approved: 5 (62.5%)       │
  │ Rejected: 2 (25%)         │
  │ Edited: 1 (12.5%)         │
  │ Avg Decision Time: 24s    │
  │ Batch Cycle: 82s (next in 18s) │
  ╚═════════════════════════════╝
  ```
**And** all percentages are calculated correctly
**And** next batch countdown is accurate

**Test Data**:
- Session with 50 contributions, 8 suggestions, 5 approved, 2 rejected, 1 edited

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_session_statistics
```

---

### AC-4.15: Prompt Customization Before LLM Call

**Given** the system is about to call LLM for an outlier decision
**When** the researcher types: "c" (customize)
**Then** the terminal displays default prompt template:
  ```
  Analyze this outlier contribution:
  Text: "{outlier_text}"
  Context: "{document_context}"

  Decide: Should we post a facilitation comment?
  ```
**And** the researcher can edit inline (e.g., add: "Focus on connection to sustainability")
**And** after editing, the LLM is called with customized prompt
**And** the response is shown for approval

**Test Data**:
- Default LLM prompt template
- Researcher customization

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_prompt_customization
```

---

## Phase 5: Production Hardening & Research Data Collection

### AC-6.1: System Uptime SLA (99.5%)

**Given** the system is deployed in production
**When** measured over a 30-day period
**Then** the system uptime is ≥99.5% (maximum 3.6 hours downtime per month)
**And** all downtime is logged with root cause analysis
**And** no data loss occurs during downtime

**Test Data**:
- 30-day production monitoring period
- Health check endpoint: `/health` returns 200 OK

**Verification**:
```bash
# Manual verification: Production uptime monitoring
# Check Prometheus metrics: up{job="ai-facilitator"} over 30 days
```

---

### AC-6.2: Monitoring Metrics Export

**Given** the system is running with Prometheus client enabled
**When** Prometheus scrapes the `/metrics` endpoint
**Then** the following metrics are exported:
  - `batch_processing_latency_seconds` (histogram)
  - `embedding_api_latency_seconds` (histogram)
  - `llm_decision_latency_seconds` (histogram)
  - `comment_posting_success_rate` (gauge)
  - `vector_db_query_latency_seconds` (histogram)
  - `api_error_rate` (counter)
**And** all metrics have correct labels (document_id, service_name, etc.)
**And** metrics scrape completes in <1 second

**Test Data**:
- Running system with active processing

**Verification**:
```bash
curl http://localhost:9090/metrics | grep batch_processing_latency
pytest tests/test_monitoring.py::test_prometheus_metrics_export
```

---

### AC-6.3: Alert Triggering on API Error Rate

**Given** the Prometheus alerting rule is configured:
  ```yaml
  - alert: HighAPIErrorRate
    expr: rate(api_error_rate[5m]) > 0.05
    for: 2m
    annotations:
      summary: "API error rate >5% for 2 minutes"
  ```
**When** the API error rate exceeds 5% for 2 consecutive minutes
**Then** an alert is triggered and sent to the configured notification channel (email, Slack, PagerDuty)
**And** the alert includes:
  - Affected service (Google Docs API, LLM API, etc.)
  - Current error rate
  - Recent error logs (last 10 entries)
**And** the system logs the alert trigger event

**Test Data**:
- Simulate API errors to exceed 5% threshold

**Verification**:
```bash
# Integration test: Trigger high error rate and verify alert
pytest tests/integration/test_alerting.py::test_high_api_error_rate_alert
```

---

### AC-6.4: Graceful Shutdown Handling

**Given** the system is processing a batch with 5 pending comments in queue
**When** a SIGTERM signal is sent (graceful shutdown request)
**Then** the system stops accepting new batches
**And** the system completes the current batch processing
**And** all 5 pending comments are persisted to disk (job queue)
**And** the system shuts down within 30 seconds
**And** on restart, the 5 comments are recovered and posted

**Test Data**:
- Active batch processing with pending comments

**Verification**:
```bash
pytest tests/test_graceful_shutdown.py::test_shutdown_with_pending_comments
```

---

### AC-6.5: Test Coverage ≥85%

**Given** the entire codebase is analyzed for test coverage
**When** pytest with coverage plugin runs all test suites
**Then** the overall code coverage is ≥85%
**And** critical modules have ≥90% coverage:
  - `embedding_service.py`
  - `analysis_engine.py`
  - `llm_decision_service.py`
  - `comment_posting_service.py`
**And** the coverage report is generated in HTML format
**And** uncovered lines are logged for manual review

**Test Data**:
- All test suites (unit, integration, end-to-end)

**Verification**:
```bash
pytest --cov=src --cov-report=html --cov-report=term
# Check htmlcov/index.html for detailed coverage
```

---

### AC-6.6: Security Audit (Zero Critical Vulnerabilities)

**Given** the codebase is scanned with security tools (Bandit, Safety, Trivy)
**When** the scan completes
**Then** zero critical or high-severity vulnerabilities are reported
**And** all medium-severity vulnerabilities are documented with mitigation plans
**And** dependency versions are up-to-date with security patches
**And** OAuth tokens are encrypted at rest (AES-256)
**And** all API inputs are sanitized to prevent injection attacks

**Test Data**:
- Full codebase + dependencies

**Verification**:
```bash
bandit -r src/
safety check
trivy image ai-facilitator:latest
pytest tests/security/test_token_encryption.py
```

---

### AC-6.7: End-to-End Workflow Test

**Given** a Google Doc with no existing monitoring
**When** the following workflow is executed:
  1. Facilitator authenticates via OAuth
  2. Registers document for monitoring
  3. User A adds text: "We should focus on user experience first."
  4. User B adds text: "What if we use quantum computing for optimization?" (outlier)
  5. System processes batch after 100 seconds
  6. LLM approves comment for User B's outlier
  7. Comment is posted to Google Doc
**Then** all steps complete successfully
**And** the comment appears in Google Doc within 3 minutes of User B's contribution
**And** the dashboard shows real-time updates at each step
**And** no errors are logged during the workflow

**Test Data**:
- Live Google Doc
- Real users making contributions
- End-to-end timing: <3 minutes

**Verification**:
```bash
pytest tests/e2e/test_full_workflow.py::test_complete_facilitation_cycle --live-doc --slow
```

---

## Definition of Done

For each acceptance criterion, the following must be completed:

1. ✅ **Test Implementation**: Automated test written and passing
2. ✅ **Code Review**: Code reviewed and approved by at least one other developer
3. ✅ **Documentation**: Behavior documented in code comments and API docs
4. ✅ **Performance**: Meets specified latency/throughput targets
5. ✅ **Security**: No new vulnerabilities introduced (scanned and verified)
6. ✅ **Integration**: Works correctly with dependent components
7. ✅ **User Validation**: Human facilitator testing completed with positive feedback

---

## Human Validation Criteria

### Outlier Detection Accuracy

**Sample Size**: 100 outliers detected by system
**Human Evaluation**: 3 independent facilitators rate each outlier on relevance (1-5 scale)
**Acceptance**: ≥85% of outliers rated ≥4/5 (relevant and valuable)

**Test Data**:
- 100 diverse outliers from different document types
- 3 human evaluators (experienced facilitators)

---

### LLM Comment Relevance

**Sample Size**: 50 LLM-generated comments posted to documents
**Human Evaluation**: Facilitators rate each comment on relevance and helpfulness (1-5 scale)
**Acceptance**: ≥80% of comments rated ≥4/5 (relevant and helpful)

**Test Data**:
- 50 comments across different scenarios (outliers, related ideas, convergent themes)
- Diverse document topics

---

### Researcher Satisfaction Survey

**Sample Size**: 5-10 researchers using the system for 3+ collaboration sessions
**Survey Questions**:
1. Overall satisfaction with AI Facilitator Agent (1-5)
2. Relevance of AI-generated comment suggestions (1-5)
3. Usefulness of terminal interface for approval workflow (1-5)
4. Helpfulness of on-demand analysis commands (1-5)
5. Reduction in manual facilitation effort (percentage estimate)
6. Would you recommend this tool to other researchers? (Yes/No)

**Acceptance**:
- Average satisfaction ≥4/5 across all questions
- ≥80% would recommend the tool
- Estimated manual effort reduction ≥40%

---

## Research Validation Criteria (Wizard-of-Oz Hypothesis Testing)

### Primary Research Question

**Does semantic analysis + LLM-powered intervention improve collaborative document quality?**

### Validation Metrics

**1. Researcher Approval Rate**
- **Target**: >60% of AI suggestions approved (y) or edited (e) before posting
- **Measurement**: Total approved + edited / Total suggestions generated
- **Sample Size**: Minimum 100 AI suggestions across 5+ collaboration sessions
- **Success Criterion**: Approval rate ≥60% indicates AI suggestions are valuable

**2. False Positive Rate**
- **Target**: <40% of AI suggestions rejected (n) by researcher
- **Measurement**: Total rejected / Total suggestions generated
- **Sample Size**: Same as approval rate (100+ suggestions)
- **Success Criterion**: False positive rate ≤40% indicates acceptable precision

**3. Qualitative Feedback from Participants**
- **Method**: Post-session interviews with document collaborators (not researchers)
- **Questions**:
  - Did AI comments improve your collaboration experience? (Yes/No/Neutral)
  - Were AI comments relevant to the discussion? (1-5 scale)
  - Did AI comments help you connect ideas? (Yes/No/Neutral)
  - Were there too many AI comments? (Yes/No)
- **Success Criterion**: ≥70% positive responses, <20% "too many comments"

**4. Edit Frequency Analysis**
- **Measurement**: Percentage of approved suggestions that were edited before posting
- **Target**: 10-30% edit rate (indicates researchers customize but mostly approve)
- **Interpretation**:
  - <10% edits: AI is very accurate, little researcher input needed
  - 10-30% edits: Healthy balance (researcher adds value)
  - >30% edits: AI suggestions may be too generic or off-target

**5. Custom Prompt Usage**
- **Measurement**: Frequency of "c" (customize prompt) option usage
- **Target**: 5-15% of suggestions trigger custom prompts
- **Interpretation**: Indicates researchers experiment with analysis strategies

**6. On-Demand Analysis Effectiveness**
- **Measurement**: Approval rate for on-demand analysis ("analyze from [perspective]")
- **Target**: ≥50% approval rate for on-demand suggestions
- **Interpretation**: Tests if custom perspectives generate valuable insights

### Research Data Collection Requirements

**Session Logging (100% capture rate)**:
- All researcher decisions (y/n/e/c) with timestamps
- Original AI suggestion text
- Final posted comment (if approved/edited)
- Decision time (seconds from suggestion display to action)
- Optional rationale text from researcher
- Session metadata (document ID, researcher ID, date)

**Export Formats**:
- CSV: For quantitative analysis (approval rates, timing)
- JSON: For qualitative analysis (text comparisons, patterns)

**Analysis Tools**:
- Approval rate calculator (approve + edit / total)
- False positive rate calculator (reject / total)
- Decision time distribution (mean, median, 95th percentile)
- Edit diff analyzer (original vs. final comment text)

### Hypothesis Validation Decision Tree

```
IF approval_rate ≥ 70% AND false_positive_rate ≤ 30%:
  → Strong validation: Proceed to semi-automation (Phase 2.0)

ELIF approval_rate ≥ 60% AND false_positive_rate ≤ 40%:
  → Moderate validation: Refine prompts, continue testing

ELIF approval_rate < 60% OR false_positive_rate > 40%:
  → Weak validation: Analyze rejection patterns, revise approach

IF qualitative_feedback ≥ 70% positive:
  → Confirms participant value, not just researcher preference

IF edit_rate > 30%:
  → AI suggestions too generic, need more context-specific prompts
```

---

## Performance Benchmarks

All performance tests run on standard infrastructure:
- **CPU**: 4 cores (2.5 GHz)
- **RAM**: 16 GB
- **Network**: 100 Mbps
- **Vector DB**: ChromaDB (local SSD storage)

### Benchmark Targets

| Metric | Target | Test Method |
|--------|--------|-------------|
| Batch processing latency | <60s (95th percentile) | Pytest benchmark with 100 batches |
| Embedding generation throughput | >100 segments/min | Pytest benchmark with 1000 segments |
| Vector DB query latency | <2s (10K embeddings) | Pytest benchmark with similarity search |
| LLM decision time | <10s (95th percentile) | Pytest benchmark with 50 decisions |
| Comment posting latency | <3s (95th percentile) | Integration test with live Docs API |
| Dashboard page load | <500ms | Selenium test with network throttling |
| Dashboard WebSocket update | <5s | Integration test with triggered events |

---

## Appendix: Test Data Generation

### Synthetic Document Generation

For repeatable testing, generate synthetic Google Docs with known characteristics:

```python
# Generate document with 100 contributions from 10 authors
# Include 5 known outliers and 3 convergent themes
pytest tests/fixtures/generate_test_document.py --authors 10 --contributions 100 --outliers 5
```

### Mock API Responses

Use `responses` library to mock Google API calls for unit tests:

```python
import responses

@responses.activate
def test_fetch_document_changes():
    responses.add(
        responses.GET,
        'https://docs.googleapis.com/v1/documents/doc_12345',
        json={'body': {'content': [...]}},
        status=200
    )
    # Test code here
```

---

## Continuous Validation

### CI/CD Pipeline Requirements

1. **Pre-commit hooks**: Run linters (ruff, mypy, black) before each commit
2. **PR checks**: All tests must pass before merge
3. **Nightly builds**: Run full test suite + performance benchmarks
4. **Weekly security scans**: Bandit, Safety, Trivy
5. **Monthly human validation**: Re-test outlier detection accuracy with new data

### Production Monitoring

1. **Daily**: Check uptime, error rates, API costs
2. **Weekly**: Review human facilitator feedback, analyze comment resolution rates
3. **Monthly**: Validate LLM comment relevance with random sampling
4. **Quarterly**: Conduct comprehensive security audit and performance review

---

**Acceptance Criteria Version**: 1.0.0
**Last Updated**: 2025-11-15
**Next Review**: After Phase 1 completion
