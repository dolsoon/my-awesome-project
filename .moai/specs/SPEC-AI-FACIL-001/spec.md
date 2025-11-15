# SPEC-AI-FACIL-001: AI Facilitator Agent for Google Docs Collaboration

## TAG BLOCK
```yaml
---
spec_id: SPEC-AI-FACIL-001
title: "AI Facilitator Agent for Google Docs Collaboration"
version: 1.1.0
status: draft
created: 2025-11-15
updated: 2025-11-15
author: @user
priority: high
---
```

## HISTORY

### Version 1.1.0 (2025-11-15)
- **REVISED**: Removed real-time dashboard (React/Vue, WebSocket, Chart.js)
- **ADDED**: Terminal-based researcher interface with human-in-the-loop approval workflow
- **CHANGED**: Philosophy from fully automated to semi-automated research tool
- **CHANGED**: Implementation phases from 6 to 5 (combined Phase 4, revised Phase 5)
- **CHANGED**: Success metric from fully automated to researcher approval rate >60%
- **RATIONALE**: Wizard-of-Oz approach enables research validation before investing in full automation

### Version 1.0.0 (2025-11-15)
- Initial SPEC creation with real-time dashboard design

## Executive Summary

A semi-automated research tool that monitors shared Google Docs, analyzes contributions using semantic embeddings, identifies outlier ideas, and provides AI-generated comment suggestions through a terminal-based interface where researchers maintain full control. Using a Wizard-of-Oz approach, researchers preview, edit, and manually approve all AI interventions before posting to validate the effectiveness of semantic analysis and LLM-powered facilitation strategies.

## Business Context

### Problem Statement
In collaborative document editing sessions, unique or outlier ideas can get lost in the flow of contributions. Human facilitators struggle to identify connections between ideas from different users in real-time, leading to missed opportunities for synthesis and innovation.

### Solution Overview
A semi-automated research tool that:
- Monitors Google Docs changes using batch processing (90-120 second intervals)
- Analyzes semantic meaning of contributions using embeddings
- Identifies outlier ideas via cosine similarity analysis
- Generates AI comment suggestions via LLM
- Presents suggestions through terminal interface for researcher review
- Enables manual approval, editing, or rejection of all interventions
- Supports on-demand analysis from specific perspectives
- Logs all decisions for research analysis

### Success Criteria
- Detection of outlier ideas with >85% accuracy (human validation)
- AI suggestion generation latency <3 minutes from contribution
- Researcher approval rate >60% for AI-generated suggestions
- Zero duplicate or contradictory automated comments
- Qualitative feedback confirms AI interventions improve collaboration
- System uptime >99.5% during research sessions
- Research data collection enables hypothesis validation

## EARS Requirements

### Environment (System Context)

**E-001**: The system SHALL operate as a web service accessible via HTTPS endpoints.

**E-002**: The system SHALL integrate with Google Workspace APIs (Drive API, Docs API) using OAuth 2.0 authentication.

**E-003**: The system SHALL support multiple concurrent document monitoring sessions (minimum 10 simultaneous documents).

**E-004**: The system SHALL store vector embeddings in a persistent vector database (ChromaDB or Pinecone).

**E-005**: The system SHALL use semantic embedding models (SBERT or Gemini embeddings) for text analysis.

**E-006**: The system SHALL interface with LLM services (Gemini or GPT-4) for intervention decision-making.

**E-007**: The system SHALL provide a terminal-based interface for researcher interaction and control.

**E-008**: The system SHALL process document changes in batch intervals of 90-120 seconds to prevent interruption fatigue.

**E-009**: The system SHALL log all researcher decisions (approve, edit, reject) with timestamps and rationale for research analysis.

### Assumptions (Design Constraints)

**A-001**: The system ASSUMES Google Docs API rate limits allow for batch polling every 90-120 seconds.

**A-002**: The system ASSUMES users have granted OAuth 2.0 permissions for document read/write access.

**A-003**: The system ASSUMES embedding model API calls complete within 5 seconds per batch.

**A-004**: The system ASSUMES vector database similarity searches complete within 2 seconds.

**A-005**: The system ASSUMES LLM API calls for intervention decisions complete within 10 seconds.

**A-006**: The system ASSUMES network latency between components averages <100ms.

**A-007**: The system ASSUMES document changes per batch interval average <50 distinct contributions.

### Requirements (Functional Specifications)

#### R1: Real-Time Document Monitoring

**R1.1**: WHEN a Google Doc is registered for monitoring, the system SHALL subscribe to change notifications via Google Drive API push notifications.

**R1.2**: WHEN a change notification is received, the system SHALL add the document to the batch processing queue.

**R1.3**: The system SHALL process queued documents every 90-120 seconds (configurable batch interval).

**R1.4**: WHEN a batch processing cycle begins, the system SHALL fetch all text changes since the last processed timestamp using Google Docs API.

**R1.5**: The system SHALL track document revision IDs to prevent duplicate processing of the same changes.

**R1.6**: IF the Google Docs API returns rate limit errors, the system SHALL implement exponential backoff with maximum retry of 3 attempts.

**R1.7**: The system SHALL log all document access events with timestamps, user IDs, and change summaries.

#### R2: Semantic Analysis and Embedding

**R2.1**: WHEN new text contributions are detected, the system SHALL extract distinct text segments (paragraphs or sentences) with author attribution.

**R2.2**: The system SHALL generate semantic embeddings for each text segment using SBERT (sentence-transformers) or Gemini embeddings API.

**R2.3**: The system SHALL normalize all embedding vectors to unit length for cosine similarity calculations.

**R2.4**: The system SHALL store embeddings in vector database with metadata: {text, author, timestamp, document_id, position}.

**R2.5**: IF embedding generation fails for a text segment, the system SHALL log the error and continue processing remaining segments.

**R2.6**: The system SHALL batch embedding API calls to minimize latency (maximum 20 segments per API request).

#### R3: Outlier Detection

**R3.1**: WHEN new embeddings are stored, the system SHALL perform cosine similarity search against all existing embeddings in the same document session.

**R3.2**: The system SHALL identify outliers as text segments with average cosine similarity <0.6 (configurable threshold) to all other contributions.

**R3.3**: The system SHALL rank outliers by novelty score: novelty = (1 - max_similarity) * contribution_length_weight.

**R3.4**: IF multiple outliers are detected in a single batch, the system SHALL prioritize the top 3 by novelty score.

**R3.5**: The system SHALL maintain a moving window of the last 100 contributions for similarity comparison.

**R3.6**: The system SHALL exclude very short contributions (<15 words) from outlier analysis.

#### R4: Related Idea Connection

**R4.1**: WHEN processing new contributions, the system SHALL perform similarity search to find related ideas from different authors.

**R4.2**: The system SHALL identify related ideas as pairs with cosine similarity >0.75 (configurable threshold) from different users.

**R4.3**: The system SHALL group related ideas into clusters using hierarchical clustering with similarity threshold 0.7.

**R4.4**: IF a cluster contains ideas from ≥3 different authors, the system SHALL flag it as a "convergent theme".

**R4.5**: The system SHALL limit related idea connections to maximum 5 pairs per batch to avoid overwhelming users.

#### R5: LLM-Powered Intervention Decision

**R5.1**: WHEN outliers or related ideas are identified, the system SHALL construct a decision prompt for LLM including:
- Original text segments
- Similarity scores
- Author metadata
- Document context (previous 500 words)

**R5.2**: The system SHALL use LLM (Gemini or GPT-4) to decide WHETHER to post a comment based on:
- Relevance to document topic
- Potential value of highlighting the outlier/connection
- Avoidance of redundancy with previous comments
- Appropriateness of intervention timing

**R5.3**: The LLM SHALL return a structured JSON response: {should_comment: boolean, comment_text: string, confidence: float}.

**R5.4**: IF LLM confidence score <0.7, the system SHALL NOT post the comment and log the decision for human review.

**R5.5**: The system SHALL implement LLM prompt caching to reduce API costs for repeated document contexts.

**R5.6**: IF LLM API call fails or times out (>10 seconds), the system SHALL fall back to rule-based commenting with conservative thresholds.

#### R6: Automated Comment Posting

**R6.1**: WHEN LLM approves a comment, the system SHALL post the comment to Google Docs using Docs API at the relevant text position.

**R6.2**: The system SHALL format comments with clear attribution: "[AI Facilitator] {comment_text}".

**R6.3**: The system SHALL include metadata in comment: timestamp, confidence score, analysis type (outlier/related).

**R6.4**: IF comment posting fails due to API errors, the system SHALL retry once after 5 seconds, then log failure.

**R6.5**: The system SHALL prevent duplicate comments by checking if a comment already exists at the same text position.

**R6.6**: The system SHALL rate-limit comment posting to maximum 1 comment per 60 seconds per document to avoid spam.

**R6.7**: WHILE a document has ≥5 unresolved AI-generated comments, the system SHALL pause new comment posting until count drops below 3.

#### R7: Terminal-Based Researcher Interface

**R7.1**: The system SHALL display document changes in terminal output with:
- Timestamp of change
- Author identification
- Text preview (first 200 characters)
- Change type (new paragraph, edit, deletion)

**R7.2**: WHEN semantic analysis detects outliers or related ideas, the system SHALL display:
- Analysis type (outlier / related idea / convergent theme)
- Similarity scores and novelty metrics
- Affected text segments with author attribution
- LLM-generated comment suggestion with confidence score

**R7.3**: FOR EACH AI-generated suggestion, the system SHALL prompt researcher with options:
- `(y)` Post comment as-is
- `(n)` Reject and skip
- `(e)` Edit comment text before posting
- `(c)` Customize LLM prompt and regenerate

**R7.4**: The terminal interface SHALL support on-demand analysis commands:
- `analyze [perspective]` - Request LLM analysis from specific viewpoint (e.g., "analyze from conflict resolution perspective")
- `status` - Show current monitoring status and batch cycle countdown
- `history` - Display recent interventions and decisions
- `pause` / `resume` - Control batch processing

**R7.5**: The system SHALL log all researcher decisions with structured data:
- Decision type (approve / reject / edit / custom_prompt)
- Original AI suggestion
- Final posted comment (if approved)
- Timestamp and researcher ID
- Optional rationale text

**R7.6**: The terminal interface SHALL allow prompt customization before LLM calls:
- Display default prompt template
- Allow inline editing
- Show prompt token count
- Preview expected LLM behavior

**R7.7**: The system SHALL provide session statistics in terminal:
- Total contributions analyzed this session
- AI suggestions generated
- Researcher approval rate
- False positive rate (rejected suggestions)
- Average time to decision

### Specifications (Non-Functional Requirements)

#### S1: Performance

**S1.1**: The system SHALL process each batch cycle (document fetch → embedding → analysis → LLM → comment) in <60 seconds (95th percentile).

**S1.2**: The system SHALL handle documents up to 50,000 words without performance degradation.

**S1.3**: Vector database similarity searches SHALL complete in <2 seconds for 10,000 stored embeddings.

**S1.4**: The terminal interface SHALL respond to researcher commands within <500ms.

**S1.5**: Embedding generation SHALL achieve throughput of ≥100 text segments per minute.

#### S2: Scalability

**S2.1**: The system SHALL support horizontal scaling of worker processes for batch processing (minimum 3 workers).

**S2.2**: Vector database SHALL support partitioning by document_id for distributed storage.

**S2.3**: The system SHALL use connection pooling for Google API clients (minimum pool size: 5 connections).

**S2.4**: The system SHALL implement job queue (Redis/Celery) for asynchronous task processing.

#### S3: Reliability

**S3.1**: The system SHALL achieve 99.5% uptime during scheduled collaboration sessions.

**S3.2**: The system SHALL implement circuit breaker pattern for external API calls (Google, LLM, embedding services).

**S3.3**: IF vector database becomes unavailable, the system SHALL fall back to in-memory similarity search with persistence queue.

**S3.4**: The system SHALL persist all unprocessed batches to disk to survive service restarts without data loss.

**S3.5**: The system SHALL implement health check endpoint returning service status and dependency availability.

#### S4: Security

**S4.1**: The system SHALL store OAuth 2.0 refresh tokens encrypted at rest using AES-256.

**S4.2**: The system SHALL validate all Google API responses for signature authenticity to prevent injection attacks.

**S4.3**: The system SHALL implement rate limiting on terminal command inputs (100 commands/minute per researcher session).

**S4.4**: The system SHALL sanitize all user-generated text before passing to LLM to prevent prompt injection.

**S4.5**: The system SHALL log all security events (authentication failures, rate limit violations) to audit trail.

**S4.6**: The system SHALL use HTTPS for all external communications with minimum TLS 1.2.

#### S5: Observability

**S5.1**: The system SHALL emit structured logs with correlation IDs for distributed tracing across components.

**S5.2**: The system SHALL expose Prometheus-compatible metrics endpoint for monitoring.

**S5.3**: The system SHALL track key metrics: batch processing latency, embedding API latency, LLM decision time, comment posting success rate.

**S5.4**: The system SHALL alert on anomalies: API error rate >5%, batch processing lag >3 minutes, vector DB latency >5 seconds.

**S5.5**: The system SHALL maintain 30-day retention of application logs and 90-day retention of metrics data.

#### S6: Maintainability

**S6.1**: The system SHALL use configuration files (YAML/JSON) for all tunable parameters (thresholds, intervals, API endpoints).

**S6.2**: The system SHALL implement feature flags for gradual rollout of new analysis algorithms.

**S6.3**: The system SHALL provide CLI tools for common administrative tasks (session management, manual batch triggers, cache clearing).

**S6.4**: The system SHALL document all external API integrations with version compatibility matrix.

### Unwanted Behaviors (Error Handling & Prevention)

**U-001**: IF Google Docs API returns 429 (rate limit), THEN the system SHALL back off for exponential intervals (1s, 2s, 4s) and alert human facilitator.

**U-002**: IF embedding API returns errors for >20% of text segments in a batch, THEN the system SHALL pause processing and alert administrators.

**U-003**: IF LLM generates inappropriate or offensive comment text, THEN the system SHALL block the comment, log the incident, and use conservative fallback.

**U-004**: IF vector database latency exceeds 10 seconds, THEN the system SHALL skip similarity search for that batch and alert on degraded mode.

**U-005**: IF the same outlier is detected in consecutive batches, THEN the system SHALL suppress duplicate comments and increment recurrence counter.

**U-006**: IF comment posting rate exceeds 1 comment per 60 seconds, THEN the system SHALL queue additional comments and throttle posting.

**U-007**: IF OAuth tokens expire during operation, THEN the system SHALL attempt automatic refresh and notify user if manual re-authentication required.

**U-008**: IF terminal session is interrupted, THEN the system SHALL persist current state and allow researcher to resume from last checkpoint.

## Technical Architecture

### System Components

1. **Document Monitor Service**
   - Google Drive API change notification subscriber
   - Batch processing scheduler (90-120s intervals)
   - Document revision tracker

2. **Embedding Service**
   - SBERT/Gemini API integration
   - Vector normalization and storage
   - Batch embedding generation

3. **Vector Database**
   - ChromaDB or Pinecone
   - Similarity search engine
   - Metadata filtering support

4. **Analysis Engine**
   - Outlier detection algorithm
   - Related idea clustering
   - Novelty scoring

5. **LLM Decision Service**
   - Gemini/GPT-4 API integration
   - Prompt construction and caching
   - Structured response parsing

6. **Comment Posting Service**
   - Google Docs API integration
   - Rate limiting and deduplication
   - Retry logic with backoff

7. **Terminal Interface (Researcher Control)**
   - Rich terminal UI (Python `rich` library) or simple CLI
   - Interactive prompts for approval/rejection
   - Command interpreter for on-demand analysis
   - Session statistics display

8. **Research Data Logger**
   - Structured logging of all decisions
   - CSV/JSON export for analysis
   - Timestamped decision tracking
   - Researcher ID attribution

9. **Job Queue & Workers**
   - Redis/Celery for async processing
   - Worker pool for parallel batch processing
   - Task persistence and retry

### Technology Stack

#### Backend Services
- **Runtime**: Python 3.11+
- **Web Framework**: Flask 3.1.2 (async support via Quart if needed)
- **API Client**: google-api-python-client 2.187.0
- **OAuth**: google-auth 2.30.0, google-auth-oauthlib 1.2.0
- **Embedding**: sentence-transformers 5.1.2 (SBERT) OR google-generativeai 0.5.0 (Gemini)
- **Vector Database**: chromadb 1.3.4 OR pinecone-client 3.2.2
- **LLM**: google-generativeai 0.5.0 (Gemini) OR openai 1.40.0 (GPT-4)
- **Job Queue**: celery 5.4.0, redis 5.0.0
- **Async Support**: asyncio, aiohttp 3.9.0

#### Data Processing
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2 or all-mpnet-base-v2)
- **Similarity**: cosine_similarity from scikit-learn 1.5.0
- **Clustering**: scipy 1.13.0 (hierarchical clustering)

#### Terminal Interface
- **Terminal UI**: rich 13.7.0 (Python rich text and terminal UI)
- **CLI Framework**: click 8.1.7 or typer 0.9.0 (command-line interface)
- **Input Prompts**: prompt_toolkit 3.0.43 (interactive prompts)
- **Progress Display**: tqdm 4.66.0 (progress bars and status)

#### Infrastructure
- **HTTP Server**: Gunicorn 22.0.0 with async workers OR uvicorn 0.29.0
- **Reverse Proxy**: Nginx 1.24+ (production deployment)
- **Monitoring**: Prometheus client 0.20.0, Grafana for visualization
- **Logging**: structlog 24.1.0, python-json-logger 2.0.7

#### Development Tools
- **Testing**: pytest 8.2.0, pytest-asyncio 0.23.0
- **Mocking**: pytest-mock 3.14.0, responses 0.25.0
- **Linting**: ruff 0.5.0, mypy 1.10.0
- **Formatting**: black 24.4.0

### Data Flow (Wizard-of-Oz Human-in-the-Loop)

```
1. Google Doc Change Event
   ↓
2. Drive API Push Notification → Document Monitor Service
   ↓
3. Queue document for batch processing (90-120s interval)
   ↓
4. Batch Processor: Fetch changes via Docs API
   ↓
5. Display changes in Terminal Interface
   ↓
6. Extract text segments with author attribution
   ↓
7. Embedding Service: Generate vectors (SBERT/Gemini)
   ↓
8. Store embeddings in Vector DB (ChromaDB/Pinecone)
   ↓
9. Analysis Engine: Cosine similarity search
   ↓
10. Identify outliers (<0.6 similarity) & related ideas (>0.75 similarity)
    ↓
11. Display analysis results in Terminal Interface
    ↓
12. LLM Decision Service: Construct prompt + call Gemini/GPT-4
    ↓
13. Display LLM-generated comment suggestion in Terminal
    ↓
14. Researcher Review Loop:
    a. Display prompt: "Post this comment? (y/n/e/c)"
    b. IF (y): Post comment via Docs API → Go to 16
    c. IF (n): Skip and log rejection → Go to 16
    d. IF (e): Allow editing → Post edited version → Go to 16
    e. IF (c): Customize prompt → Regenerate LLM response → Go to 13
    ↓
15. Optional: On-demand analysis
    Researcher types: "analyze from [perspective]"
    → LLM generates custom analysis → Display in Terminal → Go to 14
    ↓
16. Log decision (approve/reject/edit) with timestamp and rationale
    ↓
17. Update Terminal statistics display (approval rate, session stats)
```

### API Integration Points

1. **Google Drive API v3**
   - `files.watch`: Subscribe to change notifications
   - Push notifications to webhook endpoint

2. **Google Docs API v1**
   - `documents.get`: Fetch document content and revisions
   - `documents.batchUpdate`: Post comments (createComment request)

3. **OAuth 2.0**
   - Scopes: `https://www.googleapis.com/auth/drive.readonly`, `https://www.googleapis.com/auth/documents`
   - Token storage: Encrypted at rest, automatic refresh

4. **Embedding APIs**
   - SBERT: Local inference (sentence-transformers library)
   - Gemini: `embedding-001` model via `google.generativeai.embed_content`

5. **Vector Database**
   - ChromaDB: Local/cloud deployment, persistent storage
   - Pinecone: Cloud-managed, serverless option

6. **LLM APIs**
   - Gemini: `gemini-1.5-pro` via `google.generativeai.GenerativeModel`
   - GPT-4: `gpt-4-turbo` via OpenAI Python client

## Design Decisions

### Batch Processing vs. Real-Time Per-Keystroke

**Decision**: Use 90-120 second batch intervals instead of per-keystroke processing.

**Rationale**:
- Prevents "chatty" and annoying interruptions to users
- Reduces API call volume and costs by 95%
- Allows semantic aggregation of related changes
- Balances real-time responsiveness with user experience

**Trade-offs**:
- Slight delay in outlier detection (acceptable for facilitation use case)
- Requires buffering and revision tracking
- More complex state management

### SBERT vs. Gemini Embeddings

**Decision**: Support both with configuration option, default to SBERT for cost efficiency.

**Rationale**:
- SBERT: Free, local inference, faster for small batches, proven accuracy
- Gemini: Cloud-based, potentially better for long-form text, easier scaling
- Allow users to choose based on budget and performance needs

**Trade-offs**:
- Dual implementation complexity
- Different embedding dimensions require separate vector DB indexes

### ChromaDB vs. Pinecone

**Decision**: Default to ChromaDB for self-hosted deployments, offer Pinecone for cloud.

**Rationale**:
- ChromaDB: Open-source, local/docker deployment, no external dependencies, free
- Pinecone: Managed service, better horizontal scaling, serverless option
- Most users prefer control over data (ChromaDB)

**Trade-offs**:
- ChromaDB requires operational overhead for production
- Pinecone has cost implications for large-scale usage

### LLM Decision Layer

**Decision**: Always use LLM to validate outlier/connection relevance before commenting.

**Rationale**:
- Prevents false positives and irrelevant comments
- Provides natural language explanation in comments
- Adapts to document context and topic
- Reduces facilitator intervention burden

**Trade-offs**:
- Adds 5-10 seconds latency per decision
- API costs ($0.01-0.05 per decision)
- Requires fallback logic for API failures

### Wizard-of-Oz Approach (Human-in-the-Loop)

**Decision**: All AI interventions require researcher approval before posting.

**Rationale**:
- Validates research hypothesis: Are AI interventions actually helpful?
- Prevents annoying/irrelevant automated comments
- Enables prompt experimentation and strategy testing
- Allows collection of approval/rejection data for analysis
- Classic research methodology: Test manually before automating
- Faster implementation (no complex dashboard UI)

**Trade-offs**:
- Requires researcher presence during collaboration sessions
- Not suitable for unmonitored/overnight sessions
- Higher researcher cognitive load than fully automated system
- Does not scale to multiple simultaneous documents

### Terminal Interface vs. Web Dashboard

**Decision**: Use simple terminal interface instead of web dashboard.

**Rationale**:
- 5-10x faster to implement (no React/Vue, WebSocket, real-time sync)
- Focuses development effort on core hypothesis (semantic analysis + LLM effectiveness)
- Sufficient for research validation (10-20 sessions with 5-10 researchers)
- Terminal UI enables rapid iteration on prompt strategies
- Can build dashboard later if research validates approach

**Trade-offs**:
- Less user-friendly than graphical dashboard
- Limited to single researcher per session
- No remote access (must be on same machine as backend)
- Minimal data visualization capabilities

### Comment Rate Limiting

**Decision**: Maximum 1 comment per 60 seconds, pause if >5 unresolved comments.

**Rationale**:
- Prevents overwhelming users with researcher-approved comments
- Allows time for participants to engage with comments
- Encourages resolution of existing comments before new ones
- Balances researcher intent with participant experience

**Trade-offs**:
- May miss highlighting time-sensitive outliers
- Requires queue management for pending comments

## Acceptance Criteria Summary

1. System successfully monitors Google Doc changes with <3 minute latency
2. Embedding generation achieves >95% success rate for text segments
3. Outlier detection accuracy >85% (validated against researcher judgment)
4. AI suggestion generation latency <3 minutes from contribution
5. Terminal interface displays suggestions within 5 seconds of analysis completion
6. Researcher approval rate >60% for AI-generated suggestions
7. Zero duplicate comments posted to same text position
8. System uptime >99.5% during research sessions
9. API costs <$5 per 1000 contributions analyzed (using SBERT + Gemini LLM)
10. Research data logging captures 100% of decisions with timestamps and rationale
11. Terminal interface command response time <500ms
12. Qualitative feedback from participants confirms AI interventions add value

## Open Questions (Research Phase)

1. What is the optimal approval threshold for researchers? (>60%? >70%?)
2. How do researchers customize prompts in practice? (What strategies emerge?)
3. Does semantic analysis + LLM intervention actually improve collaboration quality?
4. What is the false positive rate in real collaboration sessions?
5. Do participants find AI comments helpful or annoying?
6. Should the system auto-suggest prompt customizations based on document type?
7. What is the optimal similarity threshold for outlier detection across different collaboration contexts?
8. How long does it take researchers to make approve/reject decisions on average?
9. Would researchers benefit from batch approval (approve multiple suggestions at once)?
10. Should the system provide terminal UI themes or color coding for different analysis types?

## Future Research Questions (Post-Validation)

If Wizard-of-Oz testing validates the approach:
1. Should the system provide automated comment posting with confidence >0.9?
2. How to design web dashboard for remote multi-researcher collaboration?
3. Should the system learn from researcher feedback to improve LLM prompts?
4. What is the optimal batch interval for different collaboration intensities?
5. Should the system support multiple embedding models simultaneously for ensemble analysis?

## References

- Google Drive API v3: https://developers.google.com/drive/api/v3/reference
- Google Docs API v1: https://developers.google.com/docs/api/reference/rest
- sentence-transformers documentation: https://www.sbert.net/
- ChromaDB documentation: https://docs.trychroma.com/
- Gemini API documentation: https://ai.google.dev/docs
- OAuth 2.0 for Google APIs: https://developers.google.com/identity/protocols/oauth2

## Traceability

- **Related User Stories**: None (initial SPEC)
- **Related Issues**: None
- **Related PRs**: None
- **Dependencies**: Google Workspace API access, LLM API access, Vector DB setup
