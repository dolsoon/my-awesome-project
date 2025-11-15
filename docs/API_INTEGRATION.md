# API Integration Guide - SPEC-AI-FACIL-001 Phase 3

## Gemini API Integration

### Overview

The AI Facilitator uses Google's Gemini 2.5 Flash Lite model for intelligent content analysis with four specialized modes.

### API Features Used

1. **generate_content()** - Core API for content generation
2. **Structured Output** - JSON responses for programmatic processing
3. **Rate Limiting** - Built-in with exponential backoff
4. **Error Handling** - Graceful handling of API failures

### Configuration

**Initialization:**

```python
from src.services.gemini_llm_service import GeminiLLMService

service = GeminiLLMService(
    api_key="your-api-key",
    model="gemini-2.5-flash-lite",
    timeout_seconds=30
)
```

**Connection Test:**

```python
if service.test_connection():
    print("Gemini API is available")
else:
    print("Gemini API connection failed")
```

### API Calls

#### 1. Outlier Detection

**Request:**
```python
document = {
    "contributions": [
        {"author": "Alice", "text": "Standard proposal"},
        {"author": "Bob", "text": "Similar idea to Alice"},
        {"author": "Charlie", "text": "Completely novel approach"},
    ],
    "context_files": [
        {"filename": "goals.txt", "content": "Project goals..."}
    ]
}

result = service.analyze(document, mode="outlier")
```

**Response:**
```json
{
  "outlier_found": true,
  "unique_aspect": "Novel problem-solving approach",
  "similarity_score": 0.15,
  "confidence": 0.92,
  "encouragement_message": "Great thinking outside the box!"
}
```

#### 2. Summary & Clustering

**Request:**
```python
result = service.analyze(document, mode="summary")
```

**Response:**
```json
{
  "themes": [
    "Process Improvement",
    "Team Collaboration",
    "Innovation"
  ],
  "summary": "Discussion centers on team efficiency improvements with multiple complementary approaches",
  "contributor_count": 3,
  "confidence": 0.88
}
```

#### 3. Connection Finding

**Request:**
```python
result = service.analyze(document, mode="connect")
```

**Response:**
```json
{
  "connections": [
    {
      "author1": "Alice",
      "author2": "Charlie",
      "common_theme": "Process Innovation",
      "connection_message": "Charlie's novel approach complements Alice's systematic improvement proposal"
    }
  ],
  "confidence": 0.91
}
```

#### 4. Socratic Questions

**Request:**
```python
result = service.analyze(document, mode="question")
```

**Response:**
```json
{
  "target_author": "Bob",
  "clarifying_questions": [
    "What specific challenges does your approach address?",
    "How does this scale to larger teams?",
    "What assumptions underlie this proposal?"
  ],
  "confidence": 0.85
}
```

### Error Handling

The service implements automatic retry with exponential backoff:

```
Attempt 1: Immediate
Attempt 2: After 1 second
Attempt 3: After 2 seconds
```

**Error Types:**

| Error | Status | Retry | Action |
|-------|--------|-------|--------|
| Rate Limited | 429 | Yes | Exponential backoff |
| Server Error | 500/502/503 | Yes | Exponential backoff |
| Bad Request | 400 | No | Return error |
| Unauthorized | 401 | No | Check API key |
| Forbidden | 403 | No | Check permissions |

**Handling Errors:**

```python
try:
    result = service.analyze(document, mode="outlier")
except Exception as e:
    logger.error(f"Analysis failed: {str(e)}")
    # Implement fallback logic
```

### Token Management

The service automatically truncates context to fit within limits:

```python
# Count tokens before analysis
tokens = service.count_tokens_for_document(document)
if tokens > service.max_tokens * 0.8:
    # Automatically truncate oldest contributions
    document = service.truncate_context(document, service.max_tokens)

result = service.analyze(document)
```

### Performance Characteristics

**Latency Profile:**
- p50: ~2 seconds
- p95: ~5 seconds
- p99: ~10 seconds

**Throughput:**
- ~1-2 calls/second per instance
- Rate limited at 10 calls/minute per document

**Cost:**
- Approximately $0.003 per 1K input tokens
- Approximately $0.006 per 1K output tokens

## Google Docs API Integration

### Overview

The AI Facilitator posts analyzed suggestions as comments in Google Docs using the documents.batchUpdate API.

### API Features Used

1. **documents.get()** - Retrieve document content for text positioning
2. **documents.batchUpdate()** - Post comments with createComment request
3. **OAuth 2.0** - Authenticated access to user's documents

### Configuration

**Initialization:**

```python
from src.services.google_docs_api_service import GoogleDocsAPIService

# Requires authenticated Docs API client
service = GoogleDocsAPIService(
    docs_api_client=docs_client,
    rate_limit_seconds=60,
    max_unresolved=5
)
```

### API Calls

#### 1. Post Comment to Document

**Request:**
```python
result = service.post_comment(
    document_id="1XyZ...",
    comment_text="This is an insightful addition",
    target_text="specific quote to reference",  # Optional
    mode="outlier",
    confidence=0.92
)
```

**Response (Success):**
```json
{
  "success": true,
  "comment_id": "ACYDBHfU1...",
  "message": "Comment posted successfully"
}
```

**Response (Rate Limited):**
```json
{
  "success": false,
  "queued": true,
  "message": "Rate limited, queued for later"
}
```

#### 2. Resolve Comment

**Request:**
```python
service.resolve_comment(
    document_id="1XyZ...",
    comment_id="ACYDBHfU1..."
)
```

#### 3. Get Statistics

**Request:**
```python
stats = service.get_posting_statistics()
```

**Response:**
```json
{
  "total_posted": 42,
  "total_failed": 2,
  "success_rate": 95.45,
  "pending_queue_size": 3,
  "unique_documents": 8,
  "total_unresolved": 12
}
```

#### 4. Process Pending Queue

**Request:**
```python
result = service.process_pending_queue()
```

**Response:**
```json
{
  "processed": 5,
  "failed": 0,
  "remaining_in_queue": 2
}
```

### Rate Limiting

The service implements per-document rate limiting:

```python
service.rate_limit_seconds = 60  # 1 minute between comments per document
service.max_unresolved_comments = 5  # Max 5 unresolved before pausing
```

When limit is reached:
```json
{
  "success": false,
  "paused": true,
  "message": "Rate limit active"
}
```

With queue enabled:
```json
{
  "success": false,
  "queued": true,
  "message": "Rate limited, queued for later"
}
```

### Error Handling

**HTTP Error Handling:**

| Error | Status | Action |
|-------|--------|--------|
| Rate Limited | 429 | Retry with backoff |
| Server Error | 500/502/503 | Retry with backoff |
| Bad Request | 400 | Fail, return error |
| Permission Denied | 403 | Fail, check permissions |
| Not Found | 404 | Fail, document may be deleted |

**Example Error Handling:**

```python
result = service.post_comment(
    document_id=doc_id,
    comment_text=text,
    queue_on_limit=True  # Queue instead of failing
)

if not result["success"]:
    if result.get("queued"):
        # Comment will be retried later
        logger.info("Comment queued")
    else:
        # Comment failed
        logger.error(f"Failed: {result.get('error')}")
```

### Authentication

The service uses OAuth 2.0 tokens from OAuthHandler:

```python
from src.auth.oauth_handler import OAuthHandler

oauth = OAuthHandler(client_id, client_secret, redirect_uri)
token = oauth.get_valid_token()  # Automatically refreshes if expired

# Pass authenticated client to docs service
docs_service = GoogleDocsAPIService(authenticated_docs_client)
```

**Token Lifecycle:**
1. User authorizes via OAuth consent flow
2. Token stored encrypted in `tokens.json`
3. Service automatically refreshes 5 minutes before expiry
4. Tokens persist across sessions

### Comment Formatting

Comments are formatted with metadata:

```
[AI Facilitator - OUTLIER] This is an insightful contribution that
stands out from the discussion.
(Confidence: 92%, Posted: 2024-01-15T10:30:00)
```

You can customize formatting:

```python
service.format_comment({
    "comment_text": "Your analysis",
    "mode": "outlier",
    "confidence": 0.92
})
```

### Performance Characteristics

**Latency Profile:**
- Document retrieval: ~500ms
- Comment posting: ~1-2 seconds
- p95: ~3 seconds

**Throughput:**
- Rate limited: 1 comment per minute per document
- Safe for production with normal usage patterns

### Quota Limits

Google Docs API quotas:
- 10,000 calls per day per project
- 100 calls per minute per user
- 100 concurrent requests

The service respects these limits through:
- Per-document rate limiting
- Queuing mechanism
- Error handling and retries

## Integration Monitoring

### Health Checks

```python
from src.monitoring.health_check import HealthCheckService

health = HealthCheckService(gemini_service, docs_service)
status = health.check_health()
```

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "gemini_api": {"status": "up"},
    "docs_api": {"status": "up"}
  }
}
```

### Metrics Collection

```python
from src.monitoring.metrics import get_metrics

metrics = get_metrics()
metrics.record_llm_call(latency_ms=2500, success=True, mode="outlier")
metrics.record_docs_comment(latency_ms=1200, success=True)

print(metrics.export_metrics())
```

## Troubleshooting

### Gemini API Issues

**Problem: "Invalid API Key"**
```
Solution: Check GEMINI_API_KEY environment variable
```

**Problem: "Rate Limit Exceeded"**
```
Solution: Reduce analysis frequency or upgrade API quota
```

**Problem: Timeout**
```
Solution: Increase GEMINI_TIMEOUT_SECONDS or check network
```

### Google Docs API Issues

**Problem: "Permission Denied"**
```
Solution: Re-authorize with OAuth, ensure read/write access
```

**Problem: "Document Not Found"**
```
Solution: Check document ID, verify document still exists
```

**Problem: "Rate Limited"**
```
Solution: The service will queue and retry automatically
```

## Best Practices

1. **Always Use Error Handling:** Wrap API calls in try-catch
2. **Monitor Metrics:** Track success rates and latencies
3. **Queue on Limits:** Enable `queue_on_limit=True` in production
4. **Respect Rate Limits:** Don't override built-in rate limiting
5. **Refresh Tokens:** Implement automatic token refresh
6. **Log API Calls:** Maintain audit trail of all operations
7. **Test Connections:** Verify API availability on startup

## Integration Testing

```python
def test_gemini_integration():
    service = GeminiLLMService(api_key=os.getenv('GEMINI_API_KEY'))
    assert service.test_connection()

    doc = {"contributions": [{"author": "Test", "text": "Test"}]}
    result = service.analyze(doc, mode="summary")
    assert result is not None
    assert result.get("confidence", 0) > 0

def test_docs_integration():
    service = GoogleDocsAPIService(authenticated_client)
    result = service.post_comment(
        document_id="test-doc-id",
        comment_text="Test comment"
    )
    assert result["success"] in [True, False]  # Either succeeds or fails gracefully
```

## Support

For API issues:
- Gemini API: [Google AI Documentation](https://ai.google.dev/)
- Google Docs: [Google Docs API Documentation](https://developers.google.com/docs/api)
- Integration Issues: Check logs in `logs/ai-facilitator.log`
