---
name: start
description: Launch the complete idea-discovery pipeline in the background. Accepts a research direction and target venue, immediately returns the PID and monitoring commands, and runs unattended. Use when user says "run it", "start", "find ideas for me", "start pipeline", "launch", or provides a research direction with a venue.
argument-hint: "[research direction] -- venue: ICML"
allowed-tools: Bash(*)
---

# EAR — Background Launch

Research direction: $ARGUMENTS

## Execution Steps

### Step 1: Parse Arguments

Extract the following from `$ARGUMENTS`:

- **DIRECTION**: Everything before `--` (research direction, with surrounding quotation marks removed)
- **VENUE**: Value after `-- venue:`, defaulting to `ICML`

Supported formats:
- `"Explore the theory of LLM hallucinations" -- venue: NeurIPS`
- `LLM tool use hallucination -- venue: VLDB`
- `"Direction description"` (no venue → defaults to ICML)

### Step 2: Launch the Background Pipeline

Execute the following Bash commands (fully automatically, without waiting for completion):

```bash
cd /path/to/project   # Switch to the project root containing the skills
mkdir -p outputs logx

# Generate a timestamped log path
LOGFILE="logx/start_$(date +%Y%m%d_%H%M%S).log"

# Launch in the background
nohup bash run.sh "$DIRECTION" "$VENUE" > "$LOGFILE" 2>&1 &
echo $! > outputs/pipeline.pid
echo "$LOGFILE" > outputs/pipeline_logfile.txt
```

**Important**: Actually execute these commands with the `Bash` tool (substituting the parsed DIRECTION and VENUE); do not merely describe them.

### Step 3: Return Status Immediately

Immediately show the following to the user (do not wait for pipeline completion):

```
Pipeline launched in the background

Direction: [DIRECTION]
Venue: [VENUE]
PID: [actual PID]
Log: [LOGFILE path]

Monitoring commands:
  tail -f [LOGFILE]           # View progress in real time
  ./run.sh --status           # Check pipeline status
  cat outputs/PIPELINE_LOG.md # View stage decisions

Estimated duration: 30-60 minutes (depending on API speed)

Output files (on completion):
  outputs/CRITICAL_ANALYSIS.md    — landscape critique list
  outputs/IDEAS_FILTERED.md       — filtered ideas (4-6)
  outputs/SCREENING_RANKED.md     — multidimensional score ranking
  refine-logs/FINAL_PROPOSAL.md   — final refined proposal
  outputs/IDEA_DISCOVERY_REPORT.md — end-to-end summary
```

### Step 4: Verify Successful Launch

Execute with Bash:

```bash
sleep 2 && kill -0 $(cat outputs/pipeline.pid 2>/dev/null) 2>/dev/null && echo "✅ Process running" || echo "⚠️ Process not found; check the log"
# Show the first 10 log lines to confirm startup
head -5 "$LOGFILE" 2>/dev/null
```

## Rules

- **Return immediately**: After launch, do not wait for completion; tell the user the PID and monitoring method.
- **Fully autonomous**: Ask no questions; extract direction and venue from $ARGUMENTS.
- **Default venue**: Use `ICML` if no venue is specified.
- **Working directory**: Run all commands in the directory containing `run.sh` (the project root).
