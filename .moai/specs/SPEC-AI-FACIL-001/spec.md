# SPEC-AI-FACIL-001: AI Facilitator Agent for Google Docs Collaboration

## TAG BLOCK
```yaml
---
spec_id: SPEC-AI-FACIL-001
title: "AI Facilitator Agent for Google Docs Collaboration"
version: 2.0.0
status: draft
created: 2025-11-15
updated: 2025-11-15
author: @user
priority: high
---
```

## HISTORY

### Version 2.0.0 (2025-11-15)
- **MAJOR SIMPLIFICATION**: Removed embedding/vector database complexity (SBERT, ChromaDB, Pinecone)
- **CHANGED**: LLM-only approach - pass full document context directly to LLM for all analysis
- **ADDED**: 4 distinct agent modes (outlier detection, summary, connections, questions)
- **ADDED**: Context file import feature (.txt files to augment LLM knowledge)
- **REMOVED**: Embedding Service, Vector Database, Semantic Similarity Calculations
- **SIMPLIFIED**: 5 phases → 3 phases (4.5 weeks timeline)
- **RATIONALE**: Prove concept with simplest implementation. LLMs excel at semantic analysis without embeddings.

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

A simplified research tool that monitors shared Google Docs and uses LLM-powered analysis to facilitate collaboration through 4 distinct agent modes. Researchers select modes via terminal (outlier detection, summary, connections, questions) and approve all AI interventions before posting. The system passes full document context directly to LLMs without embeddings or vector databases, enabling rapid validation of semantic facilitation strategies.

## Business Context

### Problem Statement
In collaborative document editing sessions, facilitators need intelligent support for **4 distinct tasks**:

1. **Incentivize Unique Concepts**: Highlighting truly novel ideas that differ from group consensus
2. **Overview Prevalent Ideas**: Summarizing common themes and clusters to show researchers discussion patterns
3. **Foster Connections**: Connecting contributors with similar perspectives to encourage collaboration
4. **Give Clarifying Questions**: Socratic questioning to deepen contributor thinking

Human facilitators cannot perform all 4 tasks simultaneously in real-time, leading to missed opportunities for synthesis and innovation.

### Solution Overview
An LLM-powered research tool with 4 selectable agent modes:

**System Architecture**:
- Monitors Google Docs changes using batch processing (90-120 second intervals)
- Passes full document context directly to LLM (no embeddings/vector DB)
- Researcher selects agent mode via terminal: `mode outlier`, `mode summary`, `mode connect`, `mode question`
- LLM analyzes contributions using mode-specific prompt templates
- Generates intervention suggestions (encouragement, summaries, connections, questions)
- Researcher approves/edits/rejects suggestions via terminal (y/n/e)
- Posts approved comments to Google Docs
- Supports context file import to augment LLM knowledge (.txt files)

**Key Simplification**: All semantic analysis handled by LLM. No separate embedding service or vector database needed.

### Success Criteria
- LLM analysis latency <15 seconds per batch
- Researcher approval rate >60% overall (mode-specific targets vary)
- Outlier mode approval: >60% | Summary mode: >70% | Connect mode: >50% | Question mode: >65%
- System uptime >99.5% during research sessions
- Zero duplicate comments posted
- Context import success rate: 100%
- Qualitative feedback confirms AI interventions improve collaboration

## EARS Requirements

### Environment (System Context)

**E-001**: The system SHALL operate as a web service accessible via HTTPS endpoints.

**E-002**: The system SHALL integrate with Google Workspace APIs (Drive API, Docs API) using OAuth 2.0 authentication.

**E-003**: The system SHALL support multiple concurrent document monitoring sessions (minimum 10 simultaneous documents).

**E-004**: The system SHALL interface with LLM services (Gemini or GPT-4) for all semantic analysis and intervention generation.

**E-005**: The system SHALL provide a terminal-based interface for researcher interaction, mode selection, and approval control.

**E-006**: The system SHALL process document changes in batch intervals of 90-120 seconds to prevent interruption fatigue.

**E-007**: The system SHALL log all researcher decisions (approve, edit, reject) with timestamps and rationale for research analysis.

**E-008**: The system SHALL support 4 distinct agent modes selectable by researcher: outlier detection, summary, connections, questions.

**E-009**: The system SHALL allow importing .txt context files to augment LLM analysis with domain knowledge, guidelines, or meeting notes.

### Assumptions (Design Constraints)

**A-001**: The system ASSUMES Google Docs API rate limits allow for batch polling every 90-120 seconds.

**A-002**: The system ASSUMES users have granted OAuth 2.0 permissions for document read/write access.

**A-003**: The system ASSUMES LLM API calls for analysis complete within 15 seconds per batch.

**A-004**: The system ASSUMES LLMs (Gemini 1.5 Pro or GPT-4) have sufficient context window to handle full document text (up to 128K tokens).

**A-005**: The system ASSUMES network latency between components averages <100ms.

**A-006**: The system ASSUMES document changes per batch interval average <50 distinct contributions.

**A-007**: The system ASSUMES imported context files are plain text (.txt) and total <50,000 characters per session.

### Requirements (Functional Specifications)

#### R1: Real-Time Document Monitoring

**R1.1**: WHEN a Google Doc is registered for monitoring, the system SHALL subscribe to change notifications via Google Drive API push notifications.

**R1.2**: WHEN a change notification is received, the system SHALL add the document to the batch processing queue.

**R1.3**: The system SHALL process queued documents every 90-120 seconds (configurable batch interval).

**R1.4**: WHEN a batch processing cycle begins, the system SHALL fetch all text changes since the last processed timestamp using Google Docs API.

**R1.5**: The system SHALL track document revision IDs to prevent duplicate processing of the same changes.

**R1.6**: IF the Google Docs API returns rate limit errors, the system SHALL implement exponential backoff with maximum retry of 3 attempts.

**R1.7**: The system SHALL log all document access events with timestamps, user IDs, and change summaries.

#### R2: LLM-Based Analysis with 4 Agent Modes

**R2.1**: WHEN new contributions are detected, the system SHALL pass full document context to LLM including:
- All document text (up to 128K tokens)
- Author attribution for each contribution
- Timestamps and contribution sequence
- Imported context files (if any)

**R2.2**: The system SHALL support 4 agent modes selectable via terminal command:
- `mode outlier` - Outlier/unique idea detection mode
- `mode summary` - Clustering and summary mode
- `mode connect` - Similarity/connection detection mode
- `mode question` - Socratic questioning mode

**R2.3**: The terminal SHALL display current active mode prominently (e.g., `[MODE: Outlier Detection]`).

**R2.4**: The system SHALL use mode-specific LLM prompt templates optimized for each analysis type.

**R2.5**: The system SHALL manage LLM context token usage to stay within 128K token limit (Gemini 1.5 Pro or GPT-4).

**R2.6**: IF token limit is approached, the system SHALL truncate oldest contributions while preserving imported context files.

#### R2A: Mode-Specific Analysis Requirements

**R2A.1 - Outlier Mode**: WHEN in outlier mode, the LLM SHALL:
- Analyze new contribution semantic uniqueness compared to all previous contributions
- Calculate similarity score (0.0-1.0) representing deviation from group consensus
- Generate encouragement message if similarity <0.3: "🌟 Unique idea detected! This perspective hasn't been explored yet."
- Provide reasoning for uniqueness assessment

**R2A.2 - Summary Mode**: WHEN in summary mode, the LLM SHALL:
- Group similar contributions into clusters
- Identify common themes and perspectives
- Generate summary output format:
  ```
  Summary of current discussion:
  - Group 1 (N people): [theme description]
  - Group 2 (M people): [theme description]
  ```
- Include representative contributors for each cluster

**R2A.3 - Connect Mode**: WHEN in connect mode, the LLM SHALL:
- Find contributors with semantically similar ideas
- Identify collaboration opportunities
- Generate connection message: "@CurrentUser, your idea is similar to @OtherUser's point about [topic]!"
- Explain the connection rationale

**R2A.4 - Question Mode**: WHEN in question mode, the LLM SHALL:
- Analyze contribution depth and assumptions
- Generate thought-provoking Socratic questions
- Example: "Interesting point! Have you considered how this might work for [edge case]?"
- Focus on deepening contributor thinking, not criticism

#### R3: Context File Import

**R3.1**: The terminal SHALL support command: `import context.txt` to add files to LLM context.

**R3.2**: The system SHALL store imported files in session and prepend to every LLM prompt: "Background context: [file contents]".

**R3.3**: The terminal SHALL support commands:
- `list context` - Show all imported files with sizes
- `remove context.txt` - Remove file from context

**R3.4**: The system SHALL validate imported files:
- File format: Plain text (.txt) only
- File size: <10,000 characters per file
- Total context: <50,000 characters across all files

**R3.5**: IF file validation fails, the system SHALL display error message and reject import.

**R3.6**: The system SHALL track context token usage and warn researcher if approaching limits.

#### R4: LLM-Powered Intervention Generation

**R4.1**: WHEN analysis is triggered (batch or on-demand), the system SHALL construct mode-specific prompt including:
- Full document text
- Imported context files
- Mode-specific analysis instructions
- Output format requirements (JSON structure)

**R4.2**: The system SHALL use LLM (Gemini 1.5 Pro or GPT-4) with structured output parsing.

**R4.3**: The LLM SHALL return JSON response: `{should_comment: boolean, comment_text: string, confidence: float, reasoning: string}`.

**R4.4**: The system SHALL parse LLM response and display in terminal for researcher approval.

**R4.5**: IF LLM API call fails or times out (>15 seconds), the system SHALL display error and allow retry or skip.

**R4.6**: The system SHALL implement LLM prompt caching to reduce API costs for repeated document contexts (where supported).

#### R5: Comment Posting

**R5.1**: WHEN researcher approves comment (y), the system SHALL post to Google Docs using Docs API at relevant text position.

**R5.2**: The system SHALL format comments with mode attribution: `[AI Facilitator - {Mode}] {comment_text}`.

**R5.3**: The system SHALL include metadata in comment: timestamp, mode, confidence score.

**R5.4**: IF comment posting fails due to API errors, the system SHALL retry once after 5 seconds, then log failure.

**R5.5**: The system SHALL prevent duplicate comments by checking if a comment already exists at the same text position.

**R5.6**: The system SHALL rate-limit comment posting to maximum 1 comment per 60 seconds per document to avoid spam.

**R5.7**: WHILE a document has ≥5 unresolved AI-generated comments, the system SHALL pause new comment posting until count drops below 3.

#### R6: Terminal-Based Researcher Interface

**R6.1**: The system SHALL display document changes in terminal output with:
- Timestamp of change
- Author identification
- Text preview (first 200 characters)
- Change type (new paragraph, edit, deletion)

**R6.2**: WHEN LLM analysis completes, the system SHALL display:
- Current agent mode (e.g., `[MODE: Outlier Detection]`)
- Analysis results (unique ideas, clusters, connections, questions)
- LLM-generated intervention suggestion with confidence score
- LLM reasoning for suggestion

**R6.3**: FOR EACH AI-generated suggestion, the system SHALL prompt researcher with options:
- `(y)` Post comment as-is
- `(n)` Reject and skip
- `(e)` Edit comment text before posting

**R6.4**: The terminal interface SHALL support mode selection commands:
- `mode outlier` - Switch to outlier detection mode
- `mode summary` - Switch to summary/clustering mode
- `mode connect` - Switch to connection detection mode
- `mode question` - Switch to Socratic question mode

**R6.5**: The terminal interface SHALL support additional commands:
- `analyze` - Trigger immediate LLM analysis (batch cycle independent)
- `status` - Show current mode, monitoring status, batch cycle countdown
- `history` - Display recent interventions and decisions
- `pause` / `resume` - Control batch processing
- `import <file>` - Import context file
- `list context` - Show imported context files
- `remove <file>` - Remove context file

**R6.6**: The system SHALL log all researcher decisions with structured data:
- Decision type (approve / reject / edit)
- Agent mode active
- Original AI suggestion
- Final posted comment (if approved)
- Timestamp and researcher ID
- Optional rationale text

**R6.7**: The system SHALL provide session statistics in terminal:
- Total contributions analyzed this session
- AI suggestions generated (by mode)
- Researcher approval rate overall and per mode
- Average time to decision
- Imported context files count and total size

### Specifications (Non-Functional Requirements)

#### S1: Performance

**S1.1**: The system SHALL process each batch cycle (document fetch → LLM analysis → comment) in <60 seconds (95th percentile).

**S1.2**: The system SHALL handle documents up to 50,000 words (approximately 65,000 tokens) without performance degradation.

**S1.3**: LLM analysis calls SHALL complete in <15 seconds (95th percentile) for documents up to 128K tokens.

**S1.4**: The terminal interface SHALL respond to researcher commands within <500ms.

**S1.5**: Context file import SHALL validate and load files within <2 seconds per file.

#### S2: Scalability

**S2.1**: The system SHALL support horizontal scaling of worker processes for batch processing (minimum 3 workers).

**S2.2**: The system SHALL use connection pooling for Google API clients (minimum pool size: 5 connections).

**S2.3**: The system SHALL implement job queue (Redis/Celery) for asynchronous task processing.

**S2.4**: The system SHALL handle up to 10 simultaneous document monitoring sessions with independent LLM contexts.

#### S3: Reliability

**S3.1**: The system SHALL achieve 99.5% uptime during scheduled collaboration sessions.

**S3.2**: The system SHALL implement circuit breaker pattern for external API calls (Google, LLM services).

**S3.3**: IF LLM API becomes unavailable, the system SHALL queue analysis tasks and alert researcher to retry later.

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

### System Components (Simplified)

1. **Document Monitor Service**
   - Google Drive API change notification subscriber
   - Batch processing scheduler (90-120s intervals)
   - Document revision tracker

2. **LLM Analysis Service** (Core - replaces Embedding + Vector DB + Analysis Engine)
   - Gemini/GPT-4 API integration
   - Mode-specific prompt templates (4 modes)
   - Full document context management
   - Token counting and truncation
   - Structured response parsing (JSON)
   - Prompt caching (where supported)

3. **Context Manager**
   - Imported context file storage
   - Token usage tracking
   - Context file validation (.txt format, size limits)
   - Context prepending to LLM prompts

4. **Comment Posting Service**
   - Google Docs API integration
   - Rate limiting and deduplication
   - Retry logic with backoff

5. **Terminal Interface (Researcher Control)**
   - Rich terminal UI (Python `rich` library)
   - Interactive prompts for approval/rejection (y/n/e)
   - Mode selection commands (mode outlier/summary/connect/question)
   - Context file import commands (import/list/remove)
   - Session statistics display with per-mode breakdown

6. **Research Data Logger**
   - Structured logging of all decisions with agent mode
   - CSV/JSON export for analysis
   - Timestamped decision tracking
   - Researcher ID attribution

7. **Job Queue & Workers**
   - Redis/Celery for async processing
   - Worker pool for parallel batch processing
   - Task persistence and retry

### Technology Stack (Simplified)

#### Backend Services
- **Runtime**: Python 3.11+
- **Web Framework**: Flask 3.1.2 (async support via Quart if needed)
- **API Client**: google-api-python-client 2.187.0
- **OAuth**: google-auth 2.30.0, google-auth-oauthlib 1.2.0
- **LLM**: google-generativeai 0.5.0 (Gemini) OR openai 1.12.0 (GPT-4)
- **Job Queue**: celery 5.4.0, redis 5.0.0
- **Async Support**: asyncio, aiohttp 3.9.0

#### Data Processing
- **Token Counting**: tiktoken 0.5.2 (manage LLM context limits)
- **Text Parsing**: Built-in Python (no external libraries needed)

#### Terminal Interface
- **Terminal UI**: rich 13.7.0 (Python rich text and terminal UI)
- **CLI Framework**: click 8.1.7 (command-line interface)
- **Input Prompts**: prompt_toolkit 3.0.43 (interactive prompts)

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

#### Removed Dependencies (v2.0 Simplification)
- ❌ sentence-transformers 5.1.2 (SBERT embeddings)
- ❌ chromadb 1.3.4 (vector database)
- ❌ pinecone-client 3.2.2 (alternative vector DB)
- ❌ scikit-learn 1.5.0 (cosine similarity)
- ❌ scipy 1.13.0 (hierarchical clustering)
- ✅ Replaced with: LLM-only analysis (10x simpler, 3x faster to build)

### Data Flow (Simplified LLM-Only Approach)

```
1. Google Doc Change Event
   ↓
2. Drive API Push Notification → Document Monitor Service
   ↓
3. Queue document for batch processing (90-120s interval)
   ↓
4. Batch Processor: Fetch full document content via Docs API
   ↓
5. Display changes in Terminal Interface with current agent mode [MODE: X]
   ↓
6. Construct LLM prompt:
   - Full document text with author attribution
   - Imported context files (if any)
   - Mode-specific analysis instructions (outlier/summary/connect/question)
   - Token count check (<128K tokens)
   ↓
7. LLM Analysis Service: Call Gemini/GPT-4
   ↓
8. LLM performs ALL analysis:
   - Outlier mode: Compare new contributions to all previous, calculate similarity
   - Summary mode: Group contributions into clusters, identify themes
   - Connect mode: Find similar ideas from different authors
   - Question mode: Generate Socratic questions based on contribution
   ↓
9. Display LLM-generated intervention suggestion in Terminal
   - Analysis results (uniqueness scores, clusters, connections, questions)
   - Suggested comment text
   - Confidence score and reasoning
   ↓
10. Researcher Review Loop:
    a. Display prompt: "Post this comment? (y/n/e)"
    b. IF (y): Post comment via Docs API → Go to 12
    c. IF (n): Skip and log rejection → Go to 12
    d. IF (e): Allow editing → Post edited version → Go to 12
    ↓
11. Optional: Mode switching or on-demand analysis
    - `mode [type]`: Switch agent mode
    - `analyze`: Trigger immediate analysis
    - `import [file]`: Add context file → Prepend to future LLM prompts
    ↓
12. Log decision (approve/reject/edit) with mode, timestamp, rationale
    ↓
13. Update Terminal statistics display (approval rate per mode, session stats)
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

4. **LLM APIs** (Primary - All Analysis)
   - Gemini: `gemini-1.5-pro` via `google.generativeai.GenerativeModel` (128K context window)
   - GPT-4: `gpt-4-turbo` or `gpt-4o` via OpenAI Python client (128K context window)
   - Structured output: JSON mode for consistent response parsing

5. **Token Management**
   - tiktoken library for token counting
   - Context window management (<128K tokens)
   - Truncation strategy: Oldest contributions first, preserve context files

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

### LLM-Only Analysis (No Embeddings/Vector DB)

**Decision**: Pass full document context directly to LLM for all semantic analysis. No separate embedding generation or vector database.

**Rationale (v2.0 Simplification)**:
- **Proof of concept first**: Validate LLM facilitation effectiveness before optimizing
- **LLMs excel at semantic analysis**: Gemini/GPT-4 already understand similarity, clustering, uniqueness
- **10x simpler architecture**: Eliminate 3 complex subsystems (Embedding Service, Vector DB, Similarity Search)
- **3x faster to build**: 5 phases → 3 phases (4.5 weeks vs 7+ weeks)
- **Sufficient for research scale**: <1000 contributions per session fits easily in 128K context window
- **Lower costs initially**: No vector DB hosting, no embedding API calls (only LLM calls)

**When to add embeddings** (future if needed):
- Scaling to 10,000+ contributions per document (exceeds LLM context window)
- Sub-second analysis latency required (LLM takes 10-15s, embeddings <2s)
- Cost optimization for high-volume production (embeddings cheaper than repeated LLM calls at scale)

**Trade-offs**:
- ✅ Simplicity: No embedding pipeline, no vector DB operations
- ✅ Speed to market: 30% faster development timeline
- ❌ Latency: 15 seconds vs 5 seconds for embedding approach
- ❌ Scalability ceiling: 128K tokens (~100K words) vs unlimited with vector DB

### 4 Agent Modes Design

**Decision**: Implement 4 distinct agent modes (outlier, summary, connect, question) instead of single generic facilitator.

**Rationale**:
- **Clear value propositions**: Each mode solves specific facilitation need
- **Mode-specific prompts**: Optimized LLM instructions per analysis type
- **Researcher control**: Select facilitation strategy based on session goals
- **Measurable outcomes**: Track approval rates per mode to validate effectiveness

**Mode Selection Strategy**:
- Outlier mode: Encourage unique perspectives, surface minority views
- Summary mode: Help researchers track discussion themes, identify consensus
- Connect mode: Foster collaboration by linking similar contributors
- Question mode: Deepen thinking through Socratic questioning

**Trade-offs**:
- ✅ Focused analysis: Each mode optimized for specific task
- ✅ Research insights: Per-mode approval rates reveal which interventions work
- ❌ Researcher overhead: Must manually switch modes (vs auto-detection)
- ❌ Implementation complexity: 4 prompt templates vs 1 generic

### Context File Import

**Decision**: Allow researchers to import .txt files to augment LLM knowledge.

**Rationale**:
- **Domain expertise**: Import research paper abstracts, project guidelines
- **Session continuity**: Import meeting notes from previous sessions
- **Flexibility**: Researchers control what context is relevant
- **Simple implementation**: Prepend text to LLM prompts, no complex integration

**Trade-offs**:
- ✅ Powerful capability: Context-aware analysis without training custom models
- ✅ Researcher autonomy: Full control over background knowledge
- ❌ Token usage: Context files consume limited 128K window
- ❌ Manual process: Researcher must curate and import files

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

## Acceptance Criteria Summary (v2.0 Simplified)

1. System successfully monitors Google Doc changes with <3 minute latency
2. LLM analysis completes in <15 seconds (95th percentile)
3. Terminal interface displays suggestions within 5 seconds of LLM response
4. Researcher approval rate >60% overall (mode-specific targets):
   - Outlier mode: >60%
   - Summary mode: >70%
   - Connect mode: >50%
   - Question mode: >65%
5. Zero duplicate comments posted to same text position
6. System uptime >99.5% during research sessions
7. API costs <$10 per 1000 contributions analyzed (LLM-only approach)
8. Research data logging captures 100% of decisions with mode, timestamps, rationale
9. Terminal interface command response time <500ms
10. Context file import success rate: 100% for valid .txt files
11. Mode switching works correctly across all 4 agent modes
12. Qualitative feedback from participants confirms AI interventions add value

## Open Questions (Research Phase - v2.0)

1. Which agent mode is most effective? (Outlier, Summary, Connect, or Question?)
2. Do researchers switch modes frequently or stick to one preferred mode?
3. How much do imported context files improve analysis quality?
4. What is the optimal approval threshold for each mode? (Currently: 50-70%)
5. Does LLM-only analysis match embedding-based accuracy for outlier detection?
6. Do participants find AI comments helpful or annoying (qualitative feedback)?
7. How long does it take researchers to make approve/reject decisions on average?
8. Would researchers benefit from batch approval (approve multiple suggestions at once)?
9. What is the false positive rate per mode in real collaboration sessions?
10. Should the system auto-detect optimal mode based on document type?

## Future Research Questions (Post-Validation - v2.0)

If Wizard-of-Oz testing validates the LLM-only approach:
1. Should the system provide automated comment posting with confidence >0.9 for high-approval modes?
2. When to add embeddings/vector DB for scale? (>1000 contributions? >10,000?)
3. Should the system learn from researcher feedback to refine mode-specific prompts?
4. What is the optimal batch interval for different collaboration intensities?
5. Should the system support hybrid mode (combine outlier + question, or summary + connect)?
6. How to design multi-researcher collaboration (multiple terminals, shared context)?

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
