# Acceptance Criteria: SPEC-AI-FACIL-001

## TAG BLOCK
```yaml
---
spec_id: SPEC-AI-FACIL-001
acceptance_version: 2.0.0
created: 2025-11-15
updated: 2025-11-15
status: ready
test_framework: pytest
coverage_target: 85%
---
```

## Overview

This document defines the detailed acceptance criteria and test scenarios for the AI Facilitator Agent for Google Docs collaboration. All scenarios use **Given-When-Then** format for clarity and testability.

**Version 2.0.0** reflects the **simplified LLM-only approach**, removing all embedding generation, vector database, and cosine similarity requirements.

## REVISION HISTORY

### Version 2.0.0 (2025-11-15)
- **REMOVED**: All embedding generation test scenarios (AC-2.1 through AC-2.5)
- **REMOVED**: All vector database test scenarios (AC-2.3, AC-2.4)
- **REMOVED**: All cosine similarity and SBERT tests
- **REMOVED**: ChromaDB/Pinecone infrastructure tests
- **ADDED**: Mode-specific test scenarios for 4 agent modes (Outlier, Summary, Connect, Question)
- **ADDED**: Context file import test scenarios
- **ADDED**: Terminal mode switching tests
- **ADDED**: LLM performance tests with token management
- **UPDATED**: Quality gates for LLM-only approach
- **UPDATED**: Performance benchmarks for LLM response times
- **UPDATED**: Research validation framework with mode-specific approval rates

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
7. **LLM Analysis Success**: >95% successful LLM responses (no API errors)
8. **Mode-Specific Approval Rates**:
   - Outlier mode: >60%
   - Summary mode: >70%
   - Connect mode: >50%
   - Question mode: >65%
9. **Context Import Success**: 100% success for valid .txt files
10. **System Uptime**: >99.5%
11. **API Costs**: <$10 per 1000 contributions
12. **Research Data Logging**: 100% of decisions captured

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

## Phase 2: Mode-Specific LLM Analysis

### AC-2.1: Outlier Mode - Unique Contribution Detection

**Given** 10 similar contributions about "accessibility" in document context
**When** user adds unique idea about "privacy"
**Then** LLM detects uniqueness (semantic similarity <0.3 threshold)
**And** LLM suggests encouragement comment: "Great outlier perspective on privacy! This adds a unique angle to our accessibility discussion."
**And** the suggestion is presented to researcher for approval
**And** the analysis completes in <15 seconds

**Test Data**:
- Document context: 10 accessibility-focused contributions
- New contribution: "Privacy concerns should be our top priority"
- LLM prompt: Outlier detection template
- Expected: Outlier detected, encouragement suggested

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_outlier_mode_unique_detection
```

---

### AC-2.2: Outlier Mode - Similar Contribution (No Alert)

**Given** all contributions clustered around 2 themes (accessibility, performance)
**When** user adds idea within existing accessibility cluster
**Then** LLM determines similarity >0.3 threshold
**And** LLM does NOT suggest outlier comment
**And** the system logs "No outlier detected: contribution aligns with existing themes"

**Test Data**:
- Document context: Accessibility and performance themes
- New contribution: "We should improve screen reader support" (accessibility theme)
- Expected: No outlier suggestion

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_outlier_mode_no_alert
```

---

### AC-2.3: Outlier Mode - Response Time Performance

**Given** researcher selects outlier mode
**When** LLM analyzes contribution with document context (approx 50 contributions, 10K tokens)
**Then** response time <15 seconds
**And** LLM returns structured JSON: `{should_comment: boolean, comment_text: string, confidence: float}`
**And** the response is valid and parseable

**Test Data**:
- Document with 50 contributions (approx 10K tokens)
- LLM prompt: Outlier detection template
- Expected: <15s response time

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_outlier_mode_performance --benchmark
```

---

### AC-2.4: Outlier Mode - Researcher Approval Prompt

**Given** outlier detected by LLM
**When** researcher reviews suggestion in terminal
**Then** terminal displays approval prompt: "Post this comment? (y/n/e/c)"
**And** prompt shows: suggested comment text, confidence score, original contribution excerpt
**And** researcher can choose: approve (y), reject (n), edit (e), or customize prompt (c)

**Test Data**:
- Outlier suggestion with confidence 0.85
- Terminal UI active

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_outlier_approval_prompt
```

---

### AC-3.1: Summary Mode - Cluster Summary Generation

**Given** 15 contributions across 3 themes (UX, performance, security)
**When** researcher triggers summary mode
**Then** LLM generates cluster summary with group labels:
  - "Group 1 (5 people): User experience improvements - focus on accessibility and mobile design"
  - "Group 2 (6 people): Performance optimization - emphasizing load times and caching"
  - "Group 3 (4 people): Security enhancements - authentication and data protection"
**And** summary is formatted for posting to document
**And** the analysis completes in <20 seconds

**Test Data**:
- 15 contributions with known themes
- LLM prompt: Summary/clustering template
- Expected: 3 groups identified with accurate labels

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_summary_mode_clustering
```

---

### AC-3.2: Summary Mode - Formatted Output for Document

**Given** cluster summary generated by LLM
**When** posted to document
**Then** format is:
  ```
  [AI Facilitator Summary]

  Group 1 (5 people): [theme description]
  Group 2 (6 people): [theme description]
  Group 3 (4 people): [theme description]

  Generated: 2025-11-15 14:30:00
  ```
**And** format includes participant count per group
**And** summary is posted at designated location (end of document or researcher-specified position)

**Test Data**:
- LLM-generated summary
- Document posting location

**Verification**:
```bash
pytest tests/test_comment_posting.py::test_summary_mode_format
```

---

### AC-3.3: Summary Mode - Minimum Cluster Detection

**Given** 5 contributions to document
**When** summary mode analyzes content
**Then** LLM identifies at least 2 distinct clusters (if content is diverse)
**Or** reports "Insufficient diversity for clustering" if all contributions highly similar
**And** minimum cluster size is 2 contributions per cluster

**Test Data**:
- 5 diverse contributions (2-3 expected clusters)
- 5 identical contributions (expect "no clustering" result)

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_summary_mode_minimum_clusters
```

---

### AC-3.4: Summary Mode - Dynamic Re-clustering

**Given** summary mode active and initial summary posted
**When** new contribution arrives
**Then** LLM re-clusters contributions including new content
**And** summary is updated if cluster composition changes significantly (>20% change)
**And** updated summary includes timestamp and "Updated" label
**And** researcher approves update before posting

**Test Data**:
- Initial summary with 3 clusters
- New contribution that shifts clustering
- Expected: Updated summary generated

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_summary_mode_dynamic_update
```

---

### AC-4.1: Connect Mode - Similar Idea Connection

**Given** user A's idea similar to user B's previous comment (semantic similarity >0.7)
**When** connect mode analyzes contribution
**Then** LLM suggests connection: "@UserA, this connects well with @UserB's earlier point about [topic]. Consider collaborating on this idea."
**And** comment tags both users correctly
**And** comment references specific previous contribution

**Test Data**:
- User A contribution: "We should prioritize mobile-first design"
- User B previous comment: "Mobile experience is critical for our users"
- Expected: Connection suggestion linking both

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_connect_mode_similar_ideas
```

---

### AC-4.2: Connect Mode - Most Relevant Match Selection

**Given** multiple similar contributors (3+ users with related ideas)
**When** connect mode runs
**Then** LLM selects most relevant match based on:
  - Semantic similarity (highest)
  - Recency (preferring recent contributions)
  - Author diversity (avoiding same author connections)
**And** only ONE connection is suggested (not all possible matches)

**Test Data**:
- New contribution with 3 similar previous contributions
- Expected: Single most relevant match selected

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_connect_mode_best_match
```

---

### AC-4.3: Connect Mode - No Connection for Unique Ideas

**Given** contribution with no similar ideas in document context
**When** connect mode analyzes contribution
**Then** LLM determines no relevant connections exist
**And** LLM does NOT suggest connection comment
**And** system logs "No connections found for contribution"

**Test Data**:
- Unique contribution with no semantic matches
- Expected: No connection suggestion

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_connect_mode_no_match
```

---

### AC-4.4: Connect Mode - Researcher Approval with User Tagging

**Given** connection suggested by LLM
**When** researcher approves suggestion
**Then** comment is posted with correct user tags (@UserA, @UserB)
**And** Google Docs mentions both users (if API supports)
**And** comment references specific contribution locations (if available)

**Test Data**:
- Connection suggestion with 2 users
- Google Docs API for user mentions

**Verification**:
```bash
pytest tests/integration/test_connect_mode_posting.py --live-doc
```

---

### AC-5.1: Question Mode - Clarifying Question Generation

**Given** contribution with clear assertion: "We should implement feature X"
**When** question mode analyzes contribution
**Then** LLM generates clarifying question: "What specific outcomes do you expect from feature X? How would it address current user pain points?"
**And** question is relevant and non-generic
**And** question encourages deeper thinking

**Test Data**:
- Assertion-based contribution
- Expected: Clarifying question generated

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_question_mode_clarifying
```

---

### AC-5.2: Question Mode - Deepening Question (Socratic Method)

**Given** shallow contribution: "I think this is good"
**When** question mode runs
**Then** LLM asks deepening question using Socratic method: "What specific aspects do you find valuable? Can you elaborate on why this approach would work?"
**And** question prompts reflection and elaboration
**And** question is open-ended (not yes/no)

**Test Data**:
- Shallow contribution
- Expected: Deepening question generated

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_question_mode_deepening
```

---

### AC-5.3: Question Mode - Domain-Relevant Questions

**Given** technical contribution about "microservices architecture"
**When** question mode analyzes contribution
**Then** question is relevant to domain: "How would you handle inter-service communication and data consistency in this microservices approach?"
**And** question demonstrates understanding of technical context
**And** question is NOT generic ("Can you explain more?")

**Test Data**:
- Technical contribution with domain-specific language
- Expected: Domain-relevant question

**Verification**:
```bash
pytest tests/test_llm_analysis.py::test_question_mode_domain_relevance
```

---

### AC-5.4: Question Mode - Researcher Edit Capability

**Given** question generated by LLM
**When** researcher reviews suggestion and selects edit (e)
**Then** inline editor displays question text
**And** researcher edits to: "Great point! Could you also address [specific aspect]?"
**And** edited version preserves intent (encourages elaboration)
**And** edited question is posted after approval

**Test Data**:
- Original LLM question
- Researcher-edited version
- Expected: Edited question posted

**Verification**:
```bash
pytest tests/test_terminal_ui.py::test_question_mode_edit
```

---

## Phase 2 (Context Management): Context File Import

### AC-6.1: Context File Import - Valid UTF-8 Text

**Given** researcher runs terminal command: `import context.txt`
**When** file is valid UTF-8 text (10KB)
**Then** file content is added to LLM context for future analyses
**And** terminal displays: "✓ Imported context.txt (10KB, 2,500 tokens)"
**And** file metadata stored: filename, size, token count, import timestamp

**Test Data**:
- Valid UTF-8 text file (10KB)
- Expected: Successful import with token count

**Verification**:
```bash
pytest tests/test_context_import.py::test_import_valid_utf8
```

---

### AC-6.2: Context File Import - LLM Context Integration

**Given** context file imported with domain knowledge (e.g., "Focus on accessibility compliance")
**When** LLM analyzes new contribution
**Then** LLM response incorporates context knowledge
**And** LLM suggestions reference context information when relevant
**And** context influence is visible in suggestion quality

**Test Data**:
- Context file: Accessibility compliance guidelines
- New contribution: UI design idea
- Expected: LLM suggestion mentions accessibility considerations

**Verification**:
```bash
pytest tests/test_context_import.py::test_llm_context_integration
```

---

### AC-6.3: Context File Import - Token Limit Management

**Given** multiple files imported with total size approaching token limit (100K tokens)
**When** total imported context exceeds 100K tokens
**Then** system warns: "⚠️ Context approaching token limit (95K/100K). Consider removing older files."
**And** if limit exceeded, system truncates oldest imported files
**And** truncation logged with removed file names

**Test Data**:
- 5 imported files totaling 120K tokens
- Expected: Oldest files truncated to fit within limit

**Verification**:
```bash
pytest tests/test_context_import.py::test_token_limit_truncation
```

---

### AC-6.4: Context File Import - List Imported Files

**Given** researcher runs: `list context`
**When** 3 files exist in context storage
**Then** terminal displays:
  ```
  Imported Context Files:
  1. guidelines.txt (15KB, 3,800 tokens) - Imported: 2025-11-15 10:30
  2. standards.txt (8KB, 2,100 tokens) - Imported: 2025-11-15 11:45
  3. references.txt (12KB, 3,200 tokens) - Imported: 2025-11-15 13:20

  Total: 35KB, 9,100 tokens
  ```
**And** files listed in import order (oldest first)

**Test Data**:
- 3 imported files with known metadata
- Expected: Formatted list with sizes and timestamps

**Verification**:
```bash
pytest tests/test_context_import.py::test_list_context_files
```

---

### AC-6.5: Context File Import - Remove Imported File

**Given** researcher runs: `remove context.txt`
**When** file exists in context storage
**Then** system removes file from LLM context
**And** terminal displays: "✓ Removed context.txt from context"
**And** file no longer appears in `list context` output
**And** LLM analyses no longer use removed file content

**Test Data**:
- Previously imported context.txt
- Expected: Successful removal

**Verification**:
```bash
pytest tests/test_context_import.py::test_remove_context_file
```

---

## Phase 2 (Mode Management): Terminal Mode Switching

### AC-7.1: Mode Switching - Display Current Mode

**Given** researcher runs: `mode outlier`
**When** mode changes successfully
**Then** terminal displays: "[MODE: Outlier Detection]"
**And** mode indicator persists in terminal header
**And** next analysis uses outlier prompt template

**Test Data**:
- Initial mode: None
- Command: `mode outlier`
- Expected: Mode switched to Outlier

**Verification**:
```bash
pytest tests/test_mode_switching.py::test_display_current_mode
```

---

### AC-7.2: Mode Switching - Change Analysis Template

**Given** outlier mode active
**When** researcher switches to: `mode summary`
**Then** next analysis uses summary prompt template
**And** LLM receives summary-specific instructions
**And** terminal displays: "[MODE: Summary/Clustering]"
**And** mode change logged with timestamp

**Test Data**:
- Current mode: Outlier
- Switch to: Summary
- Expected: Prompt template changed

**Verification**:
```bash
pytest tests/test_mode_switching.py::test_mode_template_switch
```

---

### AC-7.3: Mode Switching - Invalid Mode Error

**Given** researcher types: `mode invalid`
**When** system processes command
**Then** terminal displays error: "❌ Invalid mode. Valid modes: outlier, summary, connect, question"
**And** current mode remains unchanged
**And** error logged for debugging

**Test Data**:
- Invalid mode name: "invalid"
- Expected: Error message with valid options

**Verification**:
```bash
pytest tests/test_mode_switching.py::test_invalid_mode_error
```

---

### AC-7.4: Mode Switching - Batch Processing Mode Persistence

**Given** researcher selects: `mode summary`
**When** batch processing runs and analyzes 5 contributions
**Then** all 5 analyses use summary mode template
**And** mode persists across batch processing cycles
**And** mode does NOT reset between contributions

**Test Data**:
- Mode: Summary
- Batch: 5 contributions
- Expected: All analyses use summary template

**Verification**:
```bash
pytest tests/test_mode_switching.py::test_batch_mode_persistence
```

---

## Phase 3: LLM Performance & Token Management

### AC-8.1: LLM Performance - 50 Contributions (10K Tokens)

**Given** document with 50 contributions (approx 10K tokens)
**When** LLM analyzes new contribution in outlier mode
**Then** response time <15 seconds
**And** LLM successfully processes entire context
**And** no token truncation occurs

**Test Data**:
- Document: 50 contributions, 10K tokens
- Mode: Outlier detection
- Expected: <15s response time

**Verification**:
```bash
pytest tests/test_llm_performance.py::test_50_contributions_performance --benchmark
```

---

### AC-8.2: LLM Performance - 200 Contributions (40K Tokens)

**Given** document with 200 contributions (approx 40K tokens)
**When** LLM analyzes new contribution
**Then** response time <30 seconds
**And** LLM successfully processes context (within API token limits)
**And** analysis quality remains high

**Test Data**:
- Document: 200 contributions, 40K tokens
- Mode: Any
- Expected: <30s response time

**Verification**:
```bash
pytest tests/test_llm_performance.py::test_200_contributions_performance --benchmark
```

---

### AC-8.3: LLM Performance - Token Limit Truncation

**Given** LLM context approaching token limit (120K tokens from document + imports)
**When** new contribution arrives
**Then** system truncates oldest document content to fit within limit
**And** system preserves: recent contributions (last 100), imported context files, current contribution
**And** truncation logged: "⚠️ Context truncated: removed 50 oldest contributions to fit token limit"
**And** analysis proceeds with truncated context

**Test Data**:
- Large document: 120K tokens
- Expected: Truncation to fit API limit

**Verification**:
```bash
pytest tests/test_llm_performance.py::test_token_limit_truncation
```

---

### AC-8.4: LLM Performance - API Rate Limit Retry

**Given** LLM API rate limit hit (429 error)
**When** analysis requested
**Then** system retries with exponential backoff:
  - Wait 2 seconds, retry #1
  - If fails, wait 4 seconds, retry #2
  - If fails, wait 8 seconds, retry #3
**And** if all retries fail, system logs error and alerts researcher
**And** batch processing continues with remaining contributions

**Test Data**:
- Mock LLM API returning 429 errors
- Expected: Retry pattern with backoff

**Verification**:
```bash
pytest tests/test_llm_performance.py::test_rate_limit_retry
```

---

## Phase 4: Terminal Interface & Researcher Workflow

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
  │ Confidence: 0.82         │
  │ Author: user_b@example   │
  │ Text: "What if we use..." │
  ╚══════════════════════════╝
  ```
**And** the display uses color coding (yellow for outlier)
**And** LLM-suggested comment displayed below analysis

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

### AC-9.1: System Uptime SLA (99.5%)

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

### AC-9.2: Monitoring Metrics Export

**Given** the system is running with Prometheus client enabled
**When** Prometheus scrapes the `/metrics` endpoint
**Then** the following metrics are exported:
  - `batch_processing_latency_seconds` (histogram)
  - `llm_api_latency_seconds` (histogram)
  - `llm_decision_latency_seconds` (histogram)
  - `comment_posting_success_rate` (gauge)
  - `api_error_rate` (counter)
  - `mode_usage_count` (counter with mode label)
  - `researcher_approval_rate` (gauge per mode)
**And** all metrics have correct labels (document_id, service_name, mode, etc.)
**And** metrics scrape completes in <1 second

**Test Data**:
- Running system with active processing

**Verification**:
```bash
curl http://localhost:9090/metrics | grep batch_processing_latency
pytest tests/test_monitoring.py::test_prometheus_metrics_export
```

---

### AC-9.3: Alert Triggering on API Error Rate

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

### AC-9.4: Graceful Shutdown Handling

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

### AC-9.5: Test Coverage ≥85%

**Given** the entire codebase is analyzed for test coverage
**When** pytest with coverage plugin runs all test suites
**Then** the overall code coverage is ≥85%
**And** critical modules have ≥90% coverage:
  - `llm_decision_service.py`
  - `comment_posting_service.py`
  - `context_manager.py`
  - `mode_manager.py`
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

### AC-9.6: Security Audit (Zero Critical Vulnerabilities)

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

### AC-9.7: End-to-End Workflow Test

**Given** a Google Doc with no existing monitoring
**When** the following workflow is executed:
  1. Facilitator authenticates via OAuth
  2. Registers document for monitoring
  3. Sets mode to "outlier"
  4. User A adds text: "We should focus on user experience first."
  5. User B adds text: "What if we use quantum computing for optimization?" (outlier)
  6. System processes batch after 100 seconds
  7. LLM analyzes in outlier mode and approves comment for User B
  8. Researcher approves suggestion (y)
  9. Comment is posted to Google Doc
**Then** all steps complete successfully
**And** the comment appears in Google Doc within 3 minutes of User B's contribution
**And** the terminal shows real-time updates at each step
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
8. ✅ **Mode Implementation**: All 4 agent modes implemented with distinct prompt templates
9. ✅ **Context Import**: Context file import working for .txt files
10. ✅ **Mode Switching**: Mode switching functional via terminal commands
11. ✅ **Mode Approval Rates**: Mode-specific approval rates meet targets
12. ✅ **Token Management**: LLM token management prevents context overflow
13. ✅ **Research Data Capture**: Research data captures mode selection and approval patterns

---

## Research Validation Framework

### Primary Research Question

**Does LLM-powered semantic analysis + mode-specific intervention improve collaborative document quality?**

### Validation Metrics

**1. Mode-Specific Approval Rates**

| Mode | Target Approval Rate | Measurement | Success Criterion |
|------|---------------------|-------------|------------------|
| **Outlier** | >60% | (approved + edited) / total suggestions | ≥60% indicates valuable unique idea detection |
| **Summary** | >70% | (approved + edited) / total suggestions | ≥70% indicates helpful clustering |
| **Connect** | >50% | (approved + edited) / total suggestions | ≥50% indicates useful idea connections |
| **Question** | >65% | (approved + edited) / total suggestions | ≥65% indicates effective Socratic questioning |

**Sample Size**: Minimum 50 suggestions per mode across 5+ collaboration sessions

**2. False Positive Rate**
- **Target**: <40% of AI suggestions rejected (n) by researcher
- **Measurement**: Total rejected / Total suggestions generated
- **Sample Size**: 200+ total suggestions across all modes
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

**5. Mode Usage Patterns**
- **Measurement**: Frequency of each mode selection by researchers
- **Target**: Balanced usage across modes (no single mode dominates >60%)
- **Interpretation**: Indicates all modes provide value in different contexts

**6. Context Import Effectiveness**
- **Measurement**: Correlation between context file import and approval rates
- **Hypothesis**: Sessions with imported context have higher approval rates
- **Target**: >10% improvement in approval rates when context imported

### Research Data Collection Requirements

**Session Logging (100% capture rate)**:
- All researcher decisions (y/n/e/c) with timestamps
- Original AI suggestion text
- Final posted comment (if approved/edited)
- Decision time (seconds from suggestion display to action)
- Mode active during suggestion
- Context files imported (if any)
- Optional rationale text from researcher
- Session metadata (document ID, researcher ID, date)

**Export Formats**:
- CSV: For quantitative analysis (approval rates, timing)
- JSON: For qualitative analysis (text comparisons, patterns)

**Analysis Tools**:
- Mode-specific approval rate calculator
- False positive rate calculator per mode
- Decision time distribution (mean, median, 95th percentile)
- Edit diff analyzer (original vs. final comment text)
- Mode usage frequency tracker
- Context import correlation analyzer

### Hypothesis Validation Decision Tree

```
IF outlier_approval ≥ 60% AND summary_approval ≥ 70% AND connect_approval ≥ 50% AND question_approval ≥ 65%:
  → Strong validation: Proceed to semi-automation (Phase 2.0)

ELIF ANY mode_approval ≥ 70%:
  → Moderate validation: Focus on successful modes, iterate on others

ELIF ALL mode_approvals < 40%:
  → Weak validation: Analyze rejection patterns, revise LLM prompts

IF qualitative_feedback ≥ 70% positive:
  → Confirms participant value, not just researcher preference

IF edit_rate > 30%:
  → AI suggestions too generic, need more context-specific prompts

IF context_import_correlation > 0.1:
  → Context files significantly improve suggestion quality
```

---

## Performance Benchmarks

All performance tests run on standard infrastructure:
- **CPU**: 4 cores (2.5 GHz)
- **RAM**: 16 GB
- **Network**: 100 Mbps
- **LLM API**: Gemini 1.5 Pro (or equivalent)

### Benchmark Targets

| Metric | Target | Critical Threshold | Test Method |
|--------|--------|-------------------|-------------|
| Batch processing latency | <180s (95th percentile) | <300s | Pytest benchmark with 100 batches |
| LLM analysis time (50 contributions) | <15s (95th percentile) | <30s | Pytest benchmark with 50 analyses |
| LLM analysis time (200 contributions) | <30s (95th percentile) | <60s | Pytest benchmark with load test |
| Comment posting latency | <3s (95th percentile) | <5s | Integration test with live Docs API |
| Context import time (10KB file) | <2s | <5s | Pytest benchmark with file I/O |
| Mode switching latency | <500ms | <1s | Unit test with mode manager |
| Terminal command response | <300ms | <500ms | Unit test with terminal UI |

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

### Mock LLM Responses

Use mock LLM responses for deterministic testing:

```python
import pytest
from unittest.mock import patch

@patch('llm_service.call_gemini_api')
def test_outlier_mode_analysis(mock_llm):
    mock_llm.return_value = {
        "should_comment": True,
        "comment_text": "Great outlier perspective!",
        "confidence": 0.85
    }
    # Test code here
```

---

## Continuous Validation

### CI/CD Pipeline Requirements

1. **Pre-commit hooks**: Run linters (ruff, mypy, black) before each commit
2. **PR checks**: All tests must pass before merge
3. **Nightly builds**: Run full test suite + performance benchmarks
4. **Weekly security scans**: Bandit, Safety, Trivy
5. **Monthly human validation**: Re-test mode-specific approval rates with new data

### Production Monitoring

1. **Daily**: Check uptime, error rates, API costs, mode usage distribution
2. **Weekly**: Review researcher approval rates per mode, analyze comment resolution rates
3. **Monthly**: Validate LLM suggestion relevance with random sampling
4. **Quarterly**: Conduct comprehensive security audit and performance review

---

**Acceptance Criteria Version**: 2.0.0
**Last Updated**: 2025-11-15
**Next Review**: After Phase 2 completion (LLM-only implementation)
