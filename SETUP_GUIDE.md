# AI Facilitator Agent - Setup Guide

Complete guide to setting up and running the AI Facilitator Agent for Google Docs collaboration.

---

## Prerequisites

- **Python 3.11+** installed
- **Google Cloud account** with billing enabled
- **Google AI Studio account** (for Gemini API)
- **uv package manager** (recommended) or pip

---

## Step 1: Google Cloud Console Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Create Project"** or select existing project
3. Give your project a name (e.g., "AI Facilitator Agent")
4. Click **"Create"**

### 1.2 Enable Required APIs

1. In the Google Cloud Console, go to **APIs & Services > Library**
2. Search for and enable these APIs:
   - **Google Docs API**
   - **Google Drive API**

### 1.3 Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **"+ CREATE CREDENTIALS" > "OAuth client ID"**
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (for testing) or **Internal** (for organization)
   - App name: **AI Facilitator Agent**
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add the following scopes:
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/documents`
   - Test users: Add your email (for External apps)
   - Click **Save and Continue**

4. Back to **Create OAuth client ID**:
   - Application type: **Desktop app**
   - Name: **AI Facilitator Desktop Client**
   - Click **Create**

5. **Download credentials**:
   - Click the download button (⬇️) next to your new OAuth client
   - Save as `credentials.json` in project root (optional, for reference)
   - **Copy the Client ID and Client Secret** (you'll need these for .env)

### 1.4 Add Redirect URI

1. Click on your OAuth client name to edit
2. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8080/oauth2callback
   ```
3. Click **Save**

---

## Step 2: Gemini API Setup

### 2.1 Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **"Create API Key"**
3. Select your Google Cloud project (created in Step 1)
4. Click **"Create API key in existing project"**
5. **Copy the API key** (you'll need this for .env)

---

## Step 3: Project Setup

### 3.1 Clone/Navigate to Project

```bash
cd /path/to/my-awesome-project
```

### 3.2 Install Dependencies

**Using uv (recommended)**:
```bash
uv sync
```

**Or using pip**:
```bash
pip install -r requirements.txt
```

### 3.3 Create .env File

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:

```bash
# From Google Cloud Console OAuth credentials
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here

# OAuth redirect URI (must match Google Cloud Console)
GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2callback

# From Google AI Studio
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Choose Gemini model (default: gemini-2.5-flash-lite)
GEMINI_MODEL=gemini-2.5-flash-lite

# Optional: Encryption key for token storage (auto-generated if not provided)
ENCRYPTION_KEY=your_secure_random_string_here
```

**Security Note**: Never commit `.env` file to version control. It's already in `.gitignore`.

---

## Step 4: First Run & Authentication

### 4.1 Run the Application

```bash
uv run python -m src.app
```

### 4.2 Complete OAuth Flow

On first run, you'll see:

```
🔐 Starting OAuth authentication...

Please complete OAuth authentication:

1. Open this URL in your browser:
   https://accounts.google.com/o/oauth2/v2/auth?client_id=...

2. Authorize the application

3. Copy the authorization code from the redirect URL
```

**Steps**:
1. **Copy the URL** and open it in your browser
2. **Sign in** with your Google account
3. **Grant permissions** to access Google Docs and Drive
4. Browser will redirect to `http://localhost:8080/oauth2callback?code=...`
5. **Copy the authorization code** (everything after `code=`)
6. **Paste it** into the terminal when prompted

```
Enter authorization code: paste_your_code_here
```

7. You should see:
```
✅ Authentication successful!
```

### 4.3 Authentication Tokens

- Tokens are saved to `tokens.json` (encrypted)
- On subsequent runs, tokens are automatically refreshed
- You only need to authenticate once (unless tokens are revoked)

---

## Step 5: Using the Application

### 5.1 Basic Usage

Once authenticated, you'll see the interactive CLI:

```
======================================================================
  AI Facilitator Agent - Production CLI
======================================================================

✅ Authenticated with Google Workspace
✅ LLM Service: gemini-2.5-flash-lite
✅ Current Mode: outlier

Type 'help' for available commands or 'exit' to quit.

[OUTLIER] MANUAL >
```

### 5.2 Register a Google Doc

```
[OUTLIER] MANUAL > watch https://docs.google.com/document/d/YOUR_DOC_ID/edit

✅ Now watching document: YOUR_DOC_ID
   URL: https://docs.google.com/document/d/YOUR_DOC_ID
   Mode: outlier
```

### 5.3 List Watched Documents

```
[OUTLIER] MANUAL > list

📋 Watching 1 document(s):

   1. YOUR_DOC_ID
      URL: https://docs.google.com/document/d/YOUR_DOC_ID
      Last revision: None
```

### 5.4 Switch Agent Mode

```
[OUTLIER] MANUAL > mode summary

✅ Switched to summary mode
```

**Available modes**:
- `outlier` - Detect unique contributions
- `summary` - Identify themes and clusters
- `connect` - Find connections between contributors
- `question` - Generate Socratic questions

### 5.5 Analyze Documents

**Manual analysis**:
```
[SUMMARY] MANUAL > analyze

🔍 Analyzing 1 document(s) in summary mode...
📄 Fetching document: YOUR_DOC_ID
🤖 Running summary analysis...
✅ Analysis complete
   Confidence: 0.85

📊 Suggested Comment:
────────────────────────────────────────
📊 Discussion Summary

Main themes: collaboration, innovation

The document shows strong themes around...
────────────────────────────────────────

Post this comment? (y/n/e):
```

**Options**:
- `y` - Post comment as-is
- `n` - Reject comment
- `e` - Edit comment before posting

### 5.6 Enable Automatic Analysis

```
[SUMMARY] MANUAL > auto 60

✅ Automatic mode enabled (60s intervals)
```

Now the system will analyze documents every 60 seconds automatically.

**Available intervals**: 30, 60, 120 (seconds)

**Switch back to manual**:
```
[SUMMARY] AUTO > manual

✅ Switched to manual mode
```

### 5.7 Import Context Files

Add research context that will be included in LLM analysis:

```
[SUMMARY] MANUAL > import research_guidelines.txt

✅ Imported context file: research_guidelines.txt
```

**View imported files**:
```
[SUMMARY] MANUAL > context

📚 Context files (1):
   - research_guidelines.txt
```

### 5.8 Check Status

```
[SUMMARY] MANUAL > status

📊 Current Status:
   Mode: summary
   Scheduling: Manual
   Watched documents: 1
   Context files: 1
   LLM Model: gemini-2.5-flash-lite
```

---

## Available Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `watch <url>` | Register Google Docs URL | `watch https://docs.google.com/...` |
| `list` | List watched documents | `list` |
| `mode <type>` | Switch agent mode | `mode summary` |
| `analyze [mode]` | Trigger analysis | `analyze` or `analyze outlier` |
| `auto <interval>` | Enable automatic mode | `auto 60` |
| `manual` | Switch to manual mode | `manual` |
| `import <file>` | Import context file | `import guidelines.txt` |
| `context` | List context files | `context` |
| `status` | Show current status | `status` |
| `help` | Show help | `help` |
| `exit` | Exit application | `exit` |

---

## Troubleshooting

### Authentication Issues

**Problem**: "Invalid authorization code"
- **Solution**: Make sure you copied the entire code from the redirect URL
- Try authenticating again with a fresh URL

**Problem**: "Redirect URI mismatch"
- **Solution**: Verify that `GOOGLE_REDIRECT_URI` in `.env` matches the URI in Google Cloud Console exactly

### API Errors

**Problem**: "API not enabled"
- **Solution**: Go to Google Cloud Console and enable Google Docs API and Google Drive API

**Problem**: "Quota exceeded"
- **Solution**: Check your Gemini API usage at [Google AI Studio](https://makersuite.google.com/app/apikey)

**Problem**: "Invalid API key"
- **Solution**: Verify `GEMINI_API_KEY` in `.env` is correct

### Permission Issues

**Problem**: "Insufficient permissions"
- **Solution**: Make sure you granted all requested permissions during OAuth flow
- Delete `tokens.json` and re-authenticate

### Document Access Issues

**Problem**: "Document not found"
- **Solution**: Ensure your Google account has access to the document
- Verify the document ID is correct

---

## Development & Testing

### Run Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test module
uv run python -m pytest tests/test_gemini_llm_service.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=src --cov-report=html
```

### Check Code Quality

```bash
# Type checking
uv run python -m mypy src/

# Linting
uv run python -m ruff check src/

# Formatting
uv run python -m black src/
```

---

## Security Best Practices

1. **Never commit credentials**:
   - `.env` is in `.gitignore`
   - `tokens.json` is in `.gitignore`
   - `credentials.json` should be in `.gitignore`

2. **Use strong encryption key**:
   - Generate random encryption key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Add to `.env` as `ENCRYPTION_KEY`

3. **Limit OAuth scopes**:
   - Current scopes are minimal (readonly drive, docs comments)
   - Don't add unnecessary permissions

4. **Rotate API keys periodically**:
   - Gemini API keys can be rotated in Google AI Studio
   - OAuth credentials can be regenerated in Google Cloud Console

---

## Support & Documentation

- **Project Documentation**: See `PHASE_1_IMPLEMENTATION_REPORT.md`, `PHASE_2_IMPLEMENTATION_REPORT.md`, `PHASE_3_IMPLEMENTATION_REPORT.md`
- **Google Docs API**: [https://developers.google.com/docs/api](https://developers.google.com/docs/api)
- **Gemini API**: [https://ai.google.dev/docs](https://ai.google.dev/docs)
- **Issues**: Check `tests/` directory for test examples

---

## Quick Start Checklist

- [ ] Google Cloud project created
- [ ] Google Docs API enabled
- [ ] Google Drive API enabled
- [ ] OAuth credentials created
- [ ] Redirect URI added
- [ ] Gemini API key obtained
- [ ] `.env` file created and filled
- [ ] Dependencies installed (`uv sync`)
- [ ] Application runs (`uv run python -m src.app`)
- [ ] OAuth authentication completed
- [ ] First document watched
- [ ] First analysis performed

---

**You're now ready to use the AI Facilitator Agent!** 🎉

For questions or issues, refer to the test files in `tests/` directory for usage examples.
