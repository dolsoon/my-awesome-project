# Deployment Guide - SPEC-AI-FACIL-001 Phase 3

## Production Deployment Overview

This guide covers deploying the AI Facilitator Agent to production with real Gemini and Google Docs API integration.

## Prerequisites

- Python 3.11+
- Google Cloud Project with Gemini API enabled
- Google OAuth 2.0 credentials for Google Workspace
- Environment with secure secret management

## Installation

### 1. Clone Repository and Install Dependencies

```bash
git clone <repository-url>
cd ai-facilitator-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy and configure the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Required API Keys
GEMINI_API_KEY=your-actual-gemini-api-key
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
ENCRYPTION_KEY=min-32-character-encryption-key
```

### 3. Verify Dependencies

```bash
# Run tests to verify setup
python -m pytest tests/ -v

# Check test coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Configuration

### Environment Variables

Key environment variables for production:

```
GEMINI_API_KEY          - Gemini API key (REQUIRED)
GOOGLE_CLIENT_ID        - OAuth client ID (REQUIRED)
GOOGLE_CLIENT_SECRET    - OAuth client secret (REQUIRED)
ENCRYPTION_KEY          - Token encryption key (REQUIRED)
ENVIRONMENT            - Set to "production"
LOG_LEVEL              - INFO, WARNING, ERROR, DEBUG
RATE_LIMIT_SECONDS     - Seconds between document comments (default: 60)
CONFIDENCE_THRESHOLD   - Minimum confidence for analysis (default: 0.7)
```

### Configuration File

Production configuration in `config/production.yaml`:

- API timeouts and retry policies
- Rate limiting settings
- Feature flags
- Logging configuration
- Security settings

## API Key Management

### Gemini API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable the "Generative Language API"
4. Create an API key or OAuth credentials
5. Add key to `.env`: `GEMINI_API_KEY=<key>`

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "Credentials"
3. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Redirect URIs: `http://localhost:8080/auth/callback` (development) or your production URL
4. Add credentials to `.env`:
   - `GOOGLE_CLIENT_ID=<client-id>`
   - `GOOGLE_CLIENT_SECRET=<client-secret>`

## Running the Application

### Development Mode

```bash
# Run terminal UI interface
python -m src.ui.terminal_interface
```

### Production Mode

```bash
# Set environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO

# Run application
python main.py  # or your entry point
```

### Health Check

```bash
# Check service health
curl http://localhost:8080/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "checks": {
    "gemini_api": {"status": "up"},
    "docs_api": {"status": "up"}
  },
  "metrics": { ... }
}
```

## Monitoring & Observability

### Metrics Available

The service tracks:

**Gemini API Metrics:**
- Call count and success rate
- Latency (p50, p95, p99)
- Error rates by type

**Google Docs Metrics:**
- Comment posting success rate
- Latency distribution
- Unresolved comments per document

**Approval Metrics:**
- Total approvals by mode
- Confidence distribution

### Viewing Metrics

```bash
# Get current metrics
curl http://localhost:8080/metrics

# Get health status
curl http://localhost:8080/health
```

### Logging

Logs are written to `logs/ai-facilitator.log`:

```bash
# Watch logs in real-time
tail -f logs/ai-facilitator.log

# Search logs
grep "ERROR" logs/ai-facilitator.log
grep "GEMINI" logs/ai-facilitator.log
```

## Security Checklist

### Before Production Deployment

- [ ] API keys stored in secure environment (not in code)
- [ ] Encryption keys rotated and secured
- [ ] OAuth tokens encrypted at rest
- [ ] CORS restrictions configured
- [ ] Rate limiting enabled
- [ ] Input validation enabled
- [ ] Logging does not expose sensitive data
- [ ] SSL/TLS certificates valid
- [ ] Dependency vulnerability scan passed

### Running Security Audit

```bash
# Check for dependency vulnerabilities
pip audit

# Run static security analysis
python -m bandit -r src/

# Check for API key leaks
grep -r "GEMINI_API_KEY" src/ --include="*.py"
grep -r "api_key=" src/ --include="*.py"
```

## Troubleshooting

### Gemini API Connection Issues

```bash
# Test Gemini API connection
python -c "
from src.services.gemini_llm_service import GeminiLLMService
service = GeminiLLMService(api_key='your-key')
print(service.test_connection())
"
```

**Common Issues:**
- Invalid API key: Check `GEMINI_API_KEY` is set correctly
- Rate limited: Reduce analysis frequency or check quota
- Timeout: Increase `GEMINI_TIMEOUT_SECONDS` or check network

### Google Docs API Issues

```bash
# Check OAuth token validity
python -c "
from src.auth.oauth_handler import OAuthHandler
handler = OAuthHandler('client_id', 'secret', 'uri')
print(handler.get_valid_token())
"
```

**Common Issues:**
- Permission denied (403): Check user has document access
- Rate limited (429): Implement exponential backoff
- Invalid token: Refresh OAuth token

### Memory Issues

Monitor memory usage:

```bash
# Check memory usage
ps aux | grep python

# Profile memory
python -m memory_profiler main.py
```

If high memory:
- Reduce `METRICS_RETENTION_SECONDS`
- Limit `MAX_CONTRIBUTIONS`
- Clear token storage periodically

## Scaling Considerations

### Horizontal Scaling

For production with multiple instances:

1. **Use external token storage** (Redis/Memcached)
2. **Centralized logging** (CloudLogging, ELK)
3. **Load balancing** with sticky sessions for OAuth
4. **Rate limiting** at load balancer level

### Performance Tuning

```bash
# Benchmark Gemini API performance
python -c "
import time
from src.services.gemini_llm_service import GeminiLLMService

service = GeminiLLMService(api_key='your-key')
start = time.time()
result = service.analyze({...})
print(f'Latency: {time.time() - start}ms')
"
```

## Backup & Recovery

### Token Backup

```bash
# Backup tokens
cp tokens.json tokens.json.backup

# Restore from backup
cp tokens.json.backup tokens.json
```

### Log Rotation

Logs are automatically rotated when reaching 100MB:

```bash
# Check log size
du -h logs/

# Archive old logs
gzip logs/ai-facilitator.log.1
```

## Version Updates

### Update Dependencies

```bash
# Check for updates
pip list --outdated

# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade google-generativeai
```

### Backwards Compatibility

- Phase 3 is compatible with Phase 1 and Phase 2 schemas
- No data migration needed
- Mock API responses still work during testing

## Support & Monitoring

### Alerting

Configure alerts for:
- Gemini API success rate < 80%
- Google Docs API success rate < 98%
- Service health check failures
- Memory usage > 90%
- Error rate spikes

### Incident Response

1. Check health status: `curl http://localhost:8080/health`
2. Review logs: `tail -f logs/ai-facilitator.log`
3. Check metrics: `curl http://localhost:8080/metrics`
4. Restart service if needed
5. Contact support with logs and metrics

## Next Steps

- Set up monitoring dashboards (Grafana/CloudMonitoring)
- Configure alerting rules
- Establish backup and recovery procedures
- Plan for load testing
- Document runbooks for common issues
