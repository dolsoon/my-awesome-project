# Implementation Plan: SPEC-AI-FACIL-001

## TAG BLOCK
```yaml
---
spec_id: SPEC-AI-FACIL-001
plan_version: 1.1.0
created: 2025-11-15
updated: 2025-11-15
status: ready
estimated_complexity: high
---
```

## Overview

This implementation plan outlines the phased approach to building the AI Facilitator research tool with Wizard-of-Oz human-in-the-loop design. The system prioritizes core semantic analysis and LLM capabilities with a terminal-based researcher interface, enabling rapid validation of research hypotheses before investing in full automation or dashboard UI.

## REVISION HISTORY

### Version 1.1.0 (2025-11-15)
- **CHANGED**: Reduced from 6 phases to 5 phases
- **COMBINED**: Phase 4 now includes LLM Decision + Terminal Interface (previously separate)
- **REVISED**: Phase 5 renamed to "Production Hardening & Research Data Collection" (removed dashboard tasks)
- **ADDED**: Terminal UI implementation tasks in Phase 4
- **ADDED**: Research data collection and analysis tools in Phase 5
- **REMOVED**: All real-time dashboard tasks (React/Vue, WebSocket)

## Implementation Phases

### Phase 1: Foundation & Google API Integration (Primary Goal)

**Objective**: Establish core infrastructure for Google Docs monitoring and OAuth authentication.

**Deliverables**:
- OAuth 2.0 authentication flow with Google Workspace
- Document monitoring service with Drive API push notifications
- Basic batch processing scheduler (90-120s intervals)
- Document revision tracking to prevent duplicate processing
- Initial project structure and configuration management

**Technical Tasks**:
1. Set up Python 3.11+ project structure with virtual environment
2. Install core dependencies:
   - `google-api-python-client==2.187.0`
   - `google-auth==2.30.0`
   - `google-auth-oauthlib==1.2.0`
   - `flask==3.1.2`
   - `redis==5.0.0`
   - `celery==5.4.0`
3. Implement OAuth 2.0 flow:
   - Create OAuth consent screen in Google Cloud Console
   - Implement `/auth/login` and `/auth/callback` endpoints
   - Store encrypted refresh tokens (AES-256) in secure storage
   - Implement automatic token refresh logic
4. Create Document Monitor Service:
   - Implement Drive API `files.watch` subscription
   - Set up webhook endpoint for push notifications
   - Create batch processing scheduler using Celery beat
   - Implement document change fetcher using Docs API `documents.get`
5. Build revision tracking system:
   - Store last processed revision ID per document
   - Detect and extract new text changes since last revision
   - Handle edge cases (document deletions, permission changes)
6. Set up Redis for job queue and state storage
7. Create configuration management (YAML/JSON files for thresholds, intervals)
8. Implement basic logging with structlog

**Acceptance Criteria**:
- OAuth flow successfully authenticates and stores tokens
- Document changes trigger batch processing within 90-120 seconds
- System correctly fetches only new changes (no duplicates)
- Batch scheduler runs reliably without missed cycles
- All API errors logged with correlation IDs

**Dependencies**: Google Cloud Platform account, OAuth credentials

---

### Phase 2: Embedding & Vector Database Integration (Primary Goal)

**Objective**: Implement semantic embedding generation and vector storage for similarity analysis.

**Deliverables**:
- Embedding service with SBERT and Gemini support
- Vector database integration (ChromaDB primary, Pinecone optional)
- Text segmentation and preprocessing pipeline
- Embedding storage with metadata (author, timestamp, position)

**Technical Tasks**:
1. Install embedding dependencies:
   - `sentence-transformers==5.1.2` (SBERT)
   - `google-generativeai==0.5.0` (Gemini)
   - `chromadb==1.3.4` (Vector DB)
   - `scikit-learn==1.5.0` (cosine similarity)
2. Create Embedding Service:
   - Implement SBERT embedding generation using `all-mpnet-base-v2` model
   - Implement Gemini embedding generation using `embedding-001`
   - Add configuration toggle for model selection
   - Implement vector normalization to unit length
   - Batch embedding generation (max 20 segments per API call)
3. Build text preprocessing pipeline:
   - Extract paragraphs/sentences from document changes
   - Attribute text segments to authors using Docs API metadata
   - Filter out very short contributions (<15 words)
   - Handle special characters and formatting
4. Integrate ChromaDB:
   - Set up persistent storage (local filesystem or Docker volume)
   - Create collection with metadata schema: `{text, author, timestamp, document_id, position}`
   - Implement embedding storage with batch upsert
   - Create indexes for efficient similarity search
5. Implement similarity search:
   - Cosine similarity calculation using scikit-learn
   - Query vector database for top-k similar embeddings
   - Filter results by document_id and time window (last 100 contributions)
6. Add error handling:
   - Retry logic for embedding API failures
   - Fallback to alternative model if primary fails
   - Logging for failed segments with text samples

**Acceptance Criteria**:
- Embeddings generated for 100+ text segments per minute
- Vector database stores embeddings with all required metadata
- Similarity search returns results in <2 seconds for 10,000 embeddings
- System gracefully handles embedding API failures
- Embedding generation success rate >95%

**Dependencies**: Phase 1 completion, ChromaDB setup

---

### Phase 3: Analysis Engine (Outlier Detection & Related Ideas) (Primary Goal)

**Objective**: Build intelligent analysis algorithms for identifying outliers and connecting related ideas.

**Deliverables**:
- Outlier detection algorithm with configurable thresholds
- Related idea clustering and connection logic
- Novelty scoring system
- Moving window similarity comparison

**Technical Tasks**:
1. Install analysis dependencies:
   - `scipy==1.13.0` (hierarchical clustering)
   - `numpy==1.26.0` (numerical operations)
2. Implement Outlier Detection:
   - Calculate average cosine similarity for each new embedding against all recent embeddings
   - Identify outliers with similarity <0.6 (configurable threshold)
   - Compute novelty score: `novelty = (1 - max_similarity) * contribution_length_weight`
   - Rank outliers by novelty score
   - Limit to top 3 outliers per batch
3. Build Related Idea Connection:
   - Perform pairwise similarity search for embeddings >0.75 similarity
   - Filter pairs from different authors
   - Group related ideas into clusters using hierarchical clustering (threshold 0.7)
   - Identify "convergent themes" (clusters with ≥3 different authors)
   - Limit to maximum 5 related idea pairs per batch
4. Implement moving window logic:
   - Maintain cache of last 100 contributions per document
   - Evict oldest embeddings when window exceeds limit
   - Store evicted embeddings in long-term storage for analytics
5. Create deduplication logic:
   - Track previously detected outliers
   - Suppress duplicate outlier alerts in consecutive batches
   - Increment recurrence counter for persistent outliers
6. Add configuration for thresholds:
   - Outlier similarity threshold (default: 0.6)
   - Related idea similarity threshold (default: 0.75)
   - Minimum contribution length (default: 15 words)
   - Moving window size (default: 100)

**Acceptance Criteria**:
- Outlier detection identifies unique ideas with >85% accuracy (validated against human judgment)
- Related idea connections show >75% relevance (human-rated)
- Analysis completes in <10 seconds per batch (50 contributions)
- No duplicate outlier alerts for same text
- Moving window maintains correct size across batches

**Dependencies**: Phase 2 completion

---

### Phase 4: LLM Decision Service, Comment Posting & Terminal Interface (Primary Goal)

**Objective**: Integrate LLM for intelligent commenting decisions, implement comment posting, and build terminal-based researcher interface for human-in-the-loop control.

**Deliverables**:
- LLM decision service with Gemini and GPT-4 support
- Structured prompt construction for outlier/connection evaluation
- Comment posting service with rate limiting and deduplication
- Terminal UI for researcher interaction and approval workflow
- Research data logging system
- Fallback logic for LLM failures

**Technical Tasks**:
1. Install LLM dependencies:
   - `google-generativeai==0.5.0` (Gemini)
   - `openai==1.40.0` (GPT-4)
2. Create LLM Decision Service:
   - Implement prompt construction including:
     - Original text segments
     - Similarity scores
     - Author metadata
     - Document context (previous 500 words)
   - Use Gemini `gemini-1.5-pro` or GPT-4 `gpt-4-turbo`
   - Parse structured JSON response: `{should_comment: boolean, comment_text: string, confidence: float}`
   - Implement prompt caching to reduce API costs
   - Add confidence threshold filter (default: 0.7)
3. Build Comment Posting Service:
   - Integrate Google Docs API `documents.batchUpdate` with `createComment` request
   - Format comments with clear attribution: `[AI Facilitator] {comment_text}`
   - Include metadata: timestamp, confidence score, analysis type
   - Implement position mapping for comment anchoring
4. Implement rate limiting:
   - Maximum 1 comment per 60 seconds per document
   - Pause commenting when ≥5 unresolved AI comments exist
   - Queue pending comments with priority ordering
5. Add deduplication:
   - Check for existing comments at same text position
   - Compare comment text similarity to prevent near-duplicates
   - Track posted comments in database with document + position hash
6. Create fallback logic:
   - If LLM API fails/times out, use rule-based commenting
   - Conservative thresholds for fallback: novelty >0.8, similarity >0.85
   - Alert human facilitator when fallback mode activated
7. Implement retry mechanism:
   - Retry comment posting once after 5 seconds on API error
   - Log failures for manual review
   - Persist failed comments to retry queue

8. Build Terminal Interface:
   - Install terminal UI dependencies: `rich==13.7.0`, `click==8.1.7`, `prompt_toolkit==3.0.43`
   - Create main terminal application with command loop
   - Display document changes in real-time (timestamp, author, text preview)
   - Show semantic analysis results (outliers, related ideas, clusters)
   - Display LLM-generated comment suggestions with confidence scores

9. Implement Researcher Approval Workflow:
   - Interactive prompts: "Post this comment? (y/n/e/c)"
   - (y) Post as-is → Call comment posting service
   - (n) Reject and log → Skip to next suggestion
   - (e) Edit mode → Open text editor → Post edited version
   - (c) Customize prompt → Display LLM prompt → Allow editing → Regenerate

10. Add On-Demand Analysis Commands:
    - `analyze [perspective]` - Trigger custom LLM analysis
    - `status` - Show batch cycle countdown and session stats
    - `history` - Display last 10 decisions with outcomes
    - `pause` / `resume` - Control batch processing
    - `help` - Show available commands

11. Create Research Data Logger:
    - Structured logging of all decisions (approve/reject/edit/custom)
    - CSV export: timestamp, decision_type, original_suggestion, final_comment, researcher_id, rationale
    - JSON export for programmatic analysis
    - Session statistics: approval_rate, false_positive_rate, avg_decision_time

12. Build Session Statistics Display:
    - Real-time terminal dashboard (using rich panels)
    - Total contributions analyzed this session
    - AI suggestions generated (count, types)
    - Researcher approval rate (running percentage)
    - False positive rate (rejected / total)
    - Average time to decision

**Acceptance Criteria**:
- LLM decision latency <10 seconds (95th percentile)
- Comment posting success rate >98% (excluding rate limit pauses)
- Terminal interface displays suggestions within 5 seconds
- Researcher can approve/reject/edit suggestions interactively
- All decisions logged with timestamps and rationale
- On-demand analysis commands work correctly
- Session statistics update in real-time
- Terminal UI responsive (<500ms command execution)
- Zero duplicate comments at same position
- Fallback mode activates correctly on LLM failures
- Rate limiting prevents comment spam

**Dependencies**: Phase 3 completion, LLM API access, terminal UI libraries

---

### Phase 5: Production Hardening & Research Data Collection (Final Goal)

**Objective**: Prepare system for research deployment with monitoring, testing, reliability improvements, and comprehensive research data collection capabilities.

**Deliverables**:
- Comprehensive test suite (unit, integration, end-to-end)
- Monitoring and alerting infrastructure
- Research data export and analysis tools
- Session recording and playback capabilities
- Production deployment configuration
- Documentation and researcher onboarding guides

**Technical Tasks**:
1. Implement testing:
   - Unit tests for all services (pytest)
   - Integration tests for API flows (pytest-asyncio)
   - Mock Google APIs (responses, pytest-mock)
   - Test coverage >85% for critical paths
   - Load testing for batch processing (locust or k6)
2. Set up monitoring:
   - Prometheus client for metrics export
   - Grafana dashboards for visualization
   - Key metrics: batch latency, API errors, embedding throughput, LLM decision time
   - Alerting rules: error rate >5%, batch lag >3 minutes, vector DB latency >5 seconds
3. Implement observability:
   - Structured logging with correlation IDs
   - Distributed tracing (OpenTelemetry if multi-service)
   - Log aggregation (ELK stack or cloud equivalent)
   - 30-day log retention, 90-day metrics retention
4. Production configuration:
   - Environment-based config (dev, staging, production)
   - Secrets management (Google Secret Manager or HashiCorp Vault)
   - Feature flags for gradual rollout
   - Database backup and restore procedures
5. Deployment setup:
   - Docker containerization
   - Gunicorn/Uvicorn with async workers
   - Nginx reverse proxy configuration
   - Health check endpoints (`/health`, `/ready`)
   - Graceful shutdown handling
6. Create documentation:
   - Architecture diagram (Wizard-of-Oz design)
   - API documentation (OpenAPI spec)
   - Researcher onboarding guide (terminal UI usage)
   - Troubleshooting guide
   - Configuration reference
   - Research protocol documentation

7. Implement reliability patterns:
   - Circuit breaker for external APIs
   - Exponential backoff with jitter
   - Graceful degradation modes
   - Database connection pooling
   - Job queue persistence

8. Build research data analysis tools:
   - Python scripts for CSV/JSON data analysis
   - Approval rate calculation and visualization
   - False positive rate tracking
   - Decision time distribution analysis
   - Researcher behavior pattern identification

9. Create session recording system:
   - Record all terminal interactions (commands, outputs)
   - Session playback for review and analysis
   - Anonymize researcher IDs for data sharing
   - Export session summaries (approval decisions, timing, outcomes)

10. Develop researcher training materials:
    - Terminal UI tutorial with screenshots
    - Prompt customization best practices
    - Example sessions with annotated decisions
    - Troubleshooting common issues
    - Research ethics guidelines (informed consent, data handling)

**Acceptance Criteria**:
- Test coverage ≥85% for critical code paths
- All tests pass in CI/CD pipeline
- Monitoring dashboards show real-time system health
- Alerts trigger correctly on simulated failures
- Production deployment completes without errors
- System achieves 99.5% uptime SLA during research sessions
- Researcher onboarding guide enables self-service training in <2 hours
- Research data export captures 100% of decisions with complete metadata
- Session recording system successfully replays past interactions
- Data analysis tools generate approval rate, false positive rate, and timing statistics

**Dependencies**: Phases 1-4 completion

---

## Technical Approach

### Architecture Pattern

**Wizard-of-Oz modular design** with clear separation of concerns:
- Document Monitor Service (batch scheduling, API polling)
- Embedding Service (SBERT/Gemini integration)
- Analysis Engine (outlier detection, clustering)
- LLM Decision Service (Gemini/GPT-4 integration)
- Terminal Interface (researcher interaction and control)
- Research Data Logger (decision tracking and export)
- Comment Posting Service (Docs API integration)
- Job Queue (Celery workers, Redis)

### Technology Stack Summary

**Core Language**: Python 3.11+ (type hints, async/await support)

**Web Framework**: Flask 3.1.2 (REST API, OAuth), upgrade to Quart if async needed

**Job Queue**: Celery 5.4.0 + Redis 5.0.0 (distributed task processing)

**Embedding**: sentence-transformers 5.1.2 (SBERT local) OR google-generativeai 0.5.0 (Gemini cloud)

**Vector DB**: chromadb 1.3.4 (self-hosted) OR pinecone-client 3.2.2 (cloud)

**LLM**: google-generativeai 0.5.0 (Gemini) OR openai 1.40.0 (GPT-4)

**Terminal UI**: rich 13.7.0 + click 8.1.7 + prompt_toolkit 3.0.43

**Monitoring**: Prometheus client 0.20.0 + Grafana

**Testing**: pytest 8.2.0, pytest-asyncio 0.23.0

**Research Tools**: pandas 2.2.0, matplotlib 3.8.0 (data analysis and visualization)

### Risks & Mitigation

**Risk 1: Google API Rate Limits**
- **Mitigation**: Implement exponential backoff, cache document content, batch API calls, monitor quota usage
- **Fallback**: Increase batch interval if approaching quota limits

**Risk 2: LLM API Costs Exceed Budget**
- **Mitigation**: Use prompt caching, implement conservative confidence thresholds, set monthly spend limits
- **Fallback**: Fall back to rule-based commenting if budget exhausted

**Risk 3: Embedding Model Accuracy Insufficient**
- **Mitigation**: Test multiple models (SBERT vs. Gemini), use ensemble approach, validate with human feedback
- **Fallback**: Allow manual threshold tuning per document type

**Risk 4: Vector Database Performance Degradation**
- **Mitigation**: Implement partitioning by document_id, use efficient indexing, monitor query latency
- **Fallback**: Fall back to in-memory search with reduced window size

**Risk 5: Researcher Approval Bottleneck**
- **Mitigation**: Wizard-of-Oz design explicitly accepts researcher as bottleneck for validation phase
- **Fallback**: Batch approval mode for low-risk suggestions (future enhancement)

**Risk 6: Researcher Approval Rate Too Low (<60%)**
- **Mitigation**: Iterative prompt tuning based on rejection patterns, on-demand custom analysis
- **Fallback**: If approval rate <40%, may indicate semantic analysis ineffective (research finding)

**Risk 7: OAuth Token Expiration During Long Sessions**
- **Mitigation**: Implement automatic token refresh, monitor token expiry, alert on refresh failures
- **Fallback**: Graceful error handling with user notification

**Risk 8: Complex Document Structures (Tables, Images, Code Blocks)**
- **Mitigation**: Focus on plain text paragraphs, skip non-text elements, handle edge cases
- **Fallback**: Log unsupported content types, display in terminal for researcher awareness

**Risk 9: Terminal UI Complexity for Non-Technical Researchers**
- **Mitigation**: Comprehensive onboarding guide, simple command set, rich UI with visual feedback
- **Fallback**: Video tutorial, pair researcher training sessions, command cheat sheet

---

## Phase Dependencies

```
Phase 1 (Foundation)
    ↓
Phase 2 (Embedding & Vector DB)
    ↓
Phase 3 (Analysis Engine)
    ↓
Phase 4 (LLM, Comment Posting & Terminal Interface)
    ↓
Phase 5 (Production Hardening & Research Data Collection)
```

**Critical Path**: Phases 1 → 2 → 3 → 4 → 5 (fully sequential)

**Parallel Opportunities**:
- Terminal UI can be prototyped during Phase 3 (basic display only)
- Testing (Phase 5) can begin incrementally during Phases 3-4
- Research data analysis tools can be developed in parallel with Phase 4 completion

---

## Success Metrics

### Technical Metrics
- Batch processing latency <60 seconds (95th percentile)
- Embedding generation throughput >100 segments/minute
- Vector DB query latency <2 seconds
- LLM decision time <10 seconds
- Comment posting success rate >98%
- System uptime >99.5%

### Quality Metrics
- Outlier detection accuracy >85% (human validation)
- LLM decision confidence >0.7 for 80%+ of comments
- Zero duplicate comments
- Related idea relevance >75% (human-rated)

### Research Metrics
- Researcher approval rate >60% for AI suggestions
- False positive rate <40% (rejected suggestions / total)
- Qualitative feedback: AI interventions improve collaboration
- Average time to decision <30 seconds per suggestion
- API costs <$5 per 1000 contributions
- Session completion rate >90% (researchers complete planned sessions)

---

## Post-Validation Improvements (If Research Hypothesis Confirmed)

**Phase 2.0: Semi-Automation (Conditional on >70% Approval Rate)**
- Automated comment posting for high-confidence suggestions (>0.9)
- Batch approval mode for low-risk suggestions
- Researcher notification system (Slack/email) for review queue

**Phase 3.0: Full Dashboard (Conditional on Multi-Researcher Need)**
- Web dashboard for remote multi-researcher collaboration
- Real-time WebSocket updates and visualization
- Collaborative prompt tuning interface
- Analytics and insights dashboard

**Phase 4.0: Advanced Features (Conditional on Scaled Deployment)**
- Multi-language support (non-English documents)
- Machine learning from researcher feedback to improve prompts
- Support for multiple embedding models simultaneously (ensemble)
- Advanced visualization (network graphs of idea connections)
- API for third-party integrations

---

## Configuration Management

All tunable parameters will be configurable via YAML/JSON:

```yaml
batch_processing:
  interval_seconds: 100  # 90-120 range
  max_segments_per_batch: 50

embedding:
  model: "sbert"  # sbert | gemini
  sbert_model_name: "all-mpnet-base-v2"
  batch_size: 20

analysis:
  outlier_similarity_threshold: 0.6
  related_similarity_threshold: 0.75
  min_contribution_length_words: 15
  moving_window_size: 100
  max_outliers_per_batch: 3
  max_related_pairs_per_batch: 5

llm:
  provider: "gemini"  # gemini | openai
  model: "gemini-1.5-pro"
  confidence_threshold: 0.7
  timeout_seconds: 10

comment_posting:
  rate_limit_seconds: 60
  max_unresolved_comments: 5
  retry_count: 1
  retry_delay_seconds: 5

vector_db:
  type: "chromadb"  # chromadb | pinecone
  persist_directory: "./data/chromadb"

logging:
  level: "INFO"
  format: "json"
  retention_days: 30

monitoring:
  metrics_enabled: true
  prometheus_port: 9090
  alert_error_rate_threshold: 0.05
```

---

## Next Steps

After SPEC approval:
1. Set up development environment (Python 3.11+, virtual environment)
2. Create Google Cloud Platform project and enable APIs
3. Obtain OAuth credentials and test authentication flow
4. Begin Phase 1 implementation
5. Set up CI/CD pipeline for automated testing
6. Create staging environment for integration testing
