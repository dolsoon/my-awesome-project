# Researcher Guide - Using AI Facilitator Agent

## Overview

The AI Facilitator Agent is an intelligent system that analyzes collaborative contributions in Google Docs and provides feedback through four specialized modes.

## Getting Started

### Prerequisites

- Google account with Docs access
- Terminal or command-line interface
- Internet connection

### Starting the Interface

```bash
python -m src.ui.terminal_interface
```

You'll see a welcome screen:

```
┌─────────────────────────────────┐
│   AI Facilitator Agent          │
│   SPEC-AI-FACIL-001 Phase 3     │
│                                 │
│   Current Mode: Manual          │
│   Document: Not connected       │
└─────────────────────────────────┘

Type 'help' for commands
>
```

## Core Commands

### 1. Authentication & Document Setup

**Connect to Document:**
```
> auth
```

Follow OAuth flow to authorize the agent to access your Google Docs.

**Register Document:**
```
> document <document-id>
```

Gets the document ID from the URL:
```
https://docs.google.com/document/d/{DOCUMENT_ID}/edit
```

**Check Status:**
```
> status
```

Shows current connection and mode status.

### 2. Analysis Modes

The agent supports four analysis modes:

#### Mode 1: Outlier Detection

Identifies unique and distinctive contributions.

```
> analyze outlier
```

**Output Example:**
```
Found unique contribution from Alex:
  Unique Aspect: Novel approach to problem solving
  Similarity: 0.2 (very unique)
  Message: "Great thinking outside the box!"
  Confidence: 0.95
```

#### Mode 2: Summary & Clustering

Groups contributions by theme and summarizes patterns.

```
> analyze summary
```

**Output Example:**
```
Discussion Summary:
  Themes Identified:
  - Process Improvement (3 contributors)
  - Team Collaboration (2 contributors)
  - Risk Management (2 contributors)

  Summary: Team is focused on improving workflow efficiency
  Confidence: 0.88
```

#### Mode 3: Connection Finding

Identifies connections between ideas from different authors.

```
> analyze connect
```

**Output Example:**
```
Connections Found:
  Alex's automation idea → connects to → Jordan's workflow insight
    Common theme: Efficiency improvement
    "Consider combining automation with workflow redesign"

  Maya's risk framework → connects to → Sam's monitoring approach
    Common theme: System reliability
    "These complement each other well"

  Confidence: 0.92
```

#### Mode 4: Socratic Questions

Generates thoughtful questions to deepen thinking.

```
> analyze question
```

**Output Example:**
```
Questions for Alex:
  1. "What specific challenges does your approach address?"
  2. "How would this scale to larger teams?"
  3. "What assumptions underlie your proposal?"

  Target Author: Alex
  Confidence: 0.85
```

### 3. Mode Management

**Switch to Manual Mode** (One-time analysis):
```
> mode manual
```

**Switch to Automatic Mode** (Periodic analysis):
```
> mode auto
```

**Set Analysis Interval:**
```
> interval 120
```

Sets analysis to run every 120 seconds in automatic mode.

**Check Next Analysis Time:**
```
> countdown
```

Shows seconds until next automatic analysis.

### 4. Context Management

**Import Context Files:**
```
> import /path/to/context.txt
```

Adds reference material to inform analysis (e.g., project specifications, existing research).

**List Imported Context:**
```
> list_context
```

Shows all imported context files and their sizes.

**Remove Context:**
```
> remove_context <filename>
```

Removes a context file from analysis.

### 5. Decision Management

**View Analysis Suggestions:**
```
> approve
```

Shows pending suggestions requiring your decision.

**Approve Suggestion:**
```
> approve <id>
```

Accept the suggestion and post as comment.

**Reject Suggestion:**
```
> reject <id>
```

Decline the suggestion without posting.

**Edit Suggestion:**
```
> edit <id>
```

Modify the suggestion before posting (e.g., soften language, clarify).

### 6. History & Reporting

**View Recent Decisions:**
```
> history
```

Shows your last 10 approval/rejection decisions.

**Export Session Report:**
```
> export csv
```

Saves decisions and statistics to CSV file.

**View Statistics:**
```
> stats
```

Shows approval rates, modes used, confidence averages.

## Advanced Usage

### Confidence Threshold

The agent won't post comments if confidence is below the threshold (default: 70%).

**Set Custom Threshold:**
```
> confidence 0.8
```

Only posts suggestions with 80%+ confidence.

### Contribution Context

See what the agent analyzed:

```
> show_last_analysis
```

Displays:
- Contributions analyzed
- Context files used
- Prompts sent to AI
- Full response received

### Performance Monitoring

Check system performance:

```
> metrics
```

Shows:
- Analysis latency (avg, p95, p99)
- API success rates
- Comment posting success rate
- Total approvals by mode

## Best Practices

### 1. Start with Manual Mode

When beginning:
1. Use manual mode to review suggestions before posting
2. Adjust confidence threshold based on your comfort level
3. Switch to automatic after building familiarity

### 2. Effective Context Files

Create context files with:
- Project goals and requirements
- Existing research or standards
- Key constraints or guidelines
- Expected outcomes

```
# Good context file format:
Project: Research Team Collaboration
Goal: Improve cross-team knowledge sharing
Standards: Use evidence-based methodology
Constraints: Budget limited to $X
```

### 3. Monitor Approval Rates

If rejection rate is high:
- Lower confidence threshold
- Add more context files
- Check mode appropriateness

If posting too many comments:
- Increase rate limit interval
- Raise confidence threshold
- Review mode settings

### 4. Use Editing Feature

Always review before posting if:
- Dealing with sensitive topics
- Working with new team members
- Content might impact team dynamics

### 5. Regular Export

Export statistics regularly:
```
> export csv
```

Track patterns:
- Which modes are most valuable
- Approval rate trends
- Team response to different suggestion types

## Troubleshooting

### "Rate limit active"

The agent posted too recently. Wait for the interval to elapse:

```
> countdown        # Check time remaining
> interval 30      # Reduce interval if needed
```

### "Too many unresolved comments"

The document has many pending comments. Either:
1. Resolve existing comments in Google Docs
2. Increase `max_unresolved_comments` setting
3. Wait before posting new comments

### "Confidence below threshold"

The AI isn't confident in the suggestion. You can:
1. Add more context files
2. Lower the confidence threshold
3. Try a different analysis mode

### "Analysis timeout"

The analysis took too long. Try:
1. Reduce number of contributions to analyze
2. Remove some context files
3. Increase timeout setting

## Keyboard Shortcuts

```
↑         Previous command in history
↓         Next command in history
Tab       Auto-complete command
Ctrl+C    Cancel current analysis
Ctrl+D    Exit program
```

## Advanced Examples

### Example 1: Team Brainstorm Session

```bash
> mode auto          # Automatic mode for ongoing session
> interval 120       # Check every 2 minutes
> analyze outlier    # Find unique ideas
> analyze connect    # Find connections
> analyze question   # Deepen thinking
```

Monitor how team responds to suggestions.

### Example 2: Research Paper Review

```bash
> import research_standards.txt
> import project_goals.txt
> confidence 0.9        # Only high confidence suggestions
> mode manual           # Review each suggestion
> analyze summary       # Identify research themes
```

### Example 3: Learning Community

```bash
> import learning_objectives.txt
> import pedagogy_best_practices.txt
> analyze question       # Encourage deeper thinking
> analyze connect        # Find peer learning opportunities
> stats                  # Track learning progression
```

## Reporting Issues

If you encounter issues:

1. **Collect Information:**
   ```
   > metrics              # Performance metrics
   > history             # Recent decisions
   > show_last_analysis  # Last analysis details
   ```

2. **Check Logs:**
   ```
   tail -f logs/ai-facilitator.log
   ```

3. **Contact Support:**
   - Include error message
   - Share relevant log lines
   - Describe what you were doing

## FAQ

**Q: Will my comments sound artificial?**
A: Comments are reviewed by you before posting, and you can edit them.

**Q: Can I trust the AI's analysis?**
A: The confidence score indicates reliability. Review high-impact suggestions carefully.

**Q: How much does it cost?**
A: Costs depend on API usage (Gemini API + Google Docs API).

**Q: Can I use custom AI models?**
A: Currently uses Gemini API. Future versions may support other models.

**Q: How often should I check the system?**
A: Set interval based on your workflow. Recommended: every 30-120 seconds.

## Support

- Documentation: See README.md
- Deployment Help: See DEPLOYMENT.md
- API Integration: See API_INTEGRATION.md
- Issues: Create GitHub issue with logs and reproduction steps

---

**Happy collaborating! The AI Facilitator is here to enhance team conversations.**
