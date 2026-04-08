# PROJECT DESCRIPTION — openenv-sre
# Read this before reading agent_prompts_v3.md
# Every agent must read this file first.

---

## WHAT THIS PROJECT IS

This is an OpenEnv environment for the Meta x PyTorch Hackathon.
The environment simulates a Site Reliability Engineer (SRE) responding to
production incidents in a synthetic 6-service microservice system.

An AI agent observes alerts and metrics, then executes runbook actions
(like restarting a service or rolling back a deploy) to restore all services
to a healthy state. The environment scores the agent's performance from 0.0 to 1.0.

This is NOT a game. It is a real-world workflow simulation used to train
and evaluate AI agents for production incident response.

---

## HOW THE PROJECT WAS STARTED

The project was initialized using the official OpenEnv CLI:
```
pip install "openenv-core[core]>=0.2.1"
openenv init openenv-sre
```

This generated a scaffold with an echo environment as a placeholder.
The agents' job is to REPLACE the echo placeholder logic with SRE logic.
The scaffold infrastructure (HTTP server, WebSocket, endpoints) must NOT be touched.

---

## THE SYSTEM BEING SIMULATED

A microservice system with 6 services connected in this topology:

```
gateway → api → db
                ↑
         api → cache
         api → queue → worker
```

Each service has 3 metrics at every step:
- latency_ms — response time in milliseconds
- error_rate — fraction of requests failing (0.0 to 1.0)
- cpu_pct — CPU usage percentage

A service is HEALTHY when ALL THREE conditions are true:
- latency_ms < 300
- error_rate < 0.05
- cpu_pct < 80

A service is UNHEALTHY when ANY ONE condition is violated.

The episode ends when either:
- ALL 6 services are healthy (success), or
- The agent runs out of steps (failure)

---

## THE 6 INCIDENT TYPES

| Incident Type | What Happened | Which Services Affected |
|---------------|---------------|------------------------|
| BAD_DEPLOY | A bad code deployment broke the api service | api |
| QUEUE_BACKUP | Worker stopped processing, queue filled up | queue, worker |
| DB_OVERLOAD | Database saturated from too many connections | db, api |
| CACHE_MISS_STORM | Cache was cleared, all reads now hitting db | cache, db, api |
| REGION_PARTIAL | Gateway dropping 30% of traffic | gateway, api |
| CASCADING | Multiple failures triggered by db overload | db, cache, api, gateway |

---

## THE 3 TASKS

### Task 1 — Easy (max 10 steps)
- 1 service unhealthy
- Incident types: BAD_DEPLOY or QUEUE_BACKUP only
- 0 false positive alerts
- Agent needs 1 correct action to resolve
- Example: api has high error_rate → agent runs ROLLBACK_DEPLOY on api → episode ends

### Task 2 — Medium (max 20 steps)
- 2–3 services unhealthy
- Incident types: DB_OVERLOAD or CACHE_MISS_STORM only
- 1 false positive alert included (agent cannot see which alert is false)
- Agent needs 2–3 actions in correct order to resolve
- Example: db overloaded → api degraded → agent scales up db first, then restarts api

### Task 3 — Hard (max 35 steps)
- 3–5 services unhealthy
- Incident types: REGION_PARTIAL or CASCADING only
- 2–3 false positive alerts included
- Agent needs 3–5 actions, must filter noise and choose correct runbook
- Example: cascading failure with 3 false alerts — agent must identify true root cause

---

## THE 9 RUNBOOK ACTIONS

These are the ONLY actions the agent can take. No others exist.

| Action | Required Params | What It Does |
|--------|----------------|--------------|
| RESTART_SERVICE | service | Sets service to: latency=260, error=0.02, cpu=40 |
| ROLLBACK_DEPLOY | service | Same as restart IF error_rate > 0.30, else no_effect |
| SCALE_UP | service, replicas | Reduces cpu by 30, latency by 50 |
| SCALE_DOWN | service, replicas | Increases cpu by 20. "harmful" if service was healthy |
| DRAIN_QUEUE | queue | Fixes queue+worker to healthy metrics |
| SHIFT_TRAFFIC | from_service, to_service, pct | Moves traffic. "harmful" if target goes > 80 cpu |
| TOGGLE_FEATURE_FLAG | flag, value=False | Sets api error_rate to 0.01 if value=False |
| CLEAR_CACHE | service | Sets cache to healthy metrics |
| OBSERVE | service | No state change. Returns "no_effect" |

Each action returns one of these result strings:
- "success" — action worked and changed state
- "no_effect" — action was valid but did nothing useful
- "invalid" — wrong action type or missing required param
- "harmful" — action ran but made a healthy service worse

---

## REWARD FUNCTION

The agent receives a reward signal every step:

| Event | Reward |
|-------|--------|
| Step cost (applied every step, always) | -0.05 |
| Invalid action | -0.20 additional |
| Harmful action | -0.30 additional |
| Any service transitions unhealthy → healthy | +0.40 per service |
| Action targets the correct root cause service | +0.30 |
| Valid action that improves any metric | +0.20 |
| Episode end | + grader score added to final step reward |

---

## GRADING (scores 0.0 to 1.0)

### Easy grader
- Start at 1.0
- Any service still unhealthy at end: -0.5
- Each no_effect action: -0.1
- Each invalid action: -0.15
- Resolved in 5 or fewer steps: +0.1 bonus
- Minimum: 0.0

### Medium grader
- Start at 1.0
- Each service still unhealthy: -0.2
- Each invalid action: -0.1
- Each time agent acted on a false positive: -0.2
- Resolved in 12 or fewer steps: +0.1 bonus
- Minimum: 0.0

### Hard grader
- Start at 1.0
- Each service still unhealthy: -0.15
- Each harmful action: -0.25
- Each false positive acted on: -0.15
- All services healthy at end: +0.15 bonus
- All healthy AND resolved in 20 or fewer steps: +0.1 additional bonus
- Minimum: 0.0

---

## THE INCIDENT DATA FORMAT

All 30 incidents are stored in JSON files in server/data/.
Each incident is a dictionary with these exact fields:

```json
{
  "incident_id": "easy_001",
  "incident_type": "BAD_DEPLOY",
  "description": "A bad deployment to the api service caused a 42% error rate.",
  "initial_metrics": {
    "gateway": {"service": "gateway", "latency_ms": 145, "error_rate": 0.02, "cpu_pct": 38, "healthy": true},
    "api":     {"service": "api",     "latency_ms": 890, "error_rate": 0.42, "cpu_pct": 71, "healthy": false},
    "db":      {"service": "db",      "latency_ms": 180, "error_rate": 0.01, "cpu_pct": 45, "healthy": true},
    "cache":   {"service": "cache",   "latency_ms": 95,  "error_rate": 0.00, "cpu_pct": 22, "healthy": true},
    "queue":   {"service": "queue",   "latency_ms": 210, "error_rate": 0.02, "cpu_pct": 31, "healthy": true},
    "worker":  {"service": "worker",  "latency_ms": 340, "error_rate": 0.03, "cpu_pct": 44, "healthy": true}
  },
  "alerts": [
    {
      "alert_id": "alert_001",
      "service": "api",
      "severity": "critical",
      "message": "API error rate exceeded 40% — possible bad deploy",
      "is_false_positive": false
    }
  ],
  "ground_truth_root_cause": "api",
  "ground_truth_actions": ["ROLLBACK_DEPLOY:api"],
  "difficulty": "easy"
}
```

The field "is_false_positive" is NEVER shown to the agent.
It is only used by the grader to check if the agent acted on a false alert.

---

## WHAT OPENENV INIT ALREADY BUILT (DO NOT TOUCH)

The scaffold created by `openenv init` includes a working HTTP server
powered by `create_app()` from openenv-core. This automatically provides:

- POST /reset — resets the environment
- POST /step — executes one action
- GET /state — returns current state
- GET /schema — returns action and observation schemas
- WS /ws — WebSocket for persistent sessions
- GET /web — browser UI for manual interaction

None of these need to be written by agents.
The only file agents need to rewrite is `openenv_sre_environment.py`
which contains the environment logic (currently a placeholder echo env).

---

## WHAT THE BASELINE AGENT DOES

The baseline agent is a Python script that:
1. Creates an environment instance for each task (easy, medium, hard)
2. Calls the Hugging Face Inference Router API using the OpenAI client library
3. Sends the current observation to `Qwen/Qwen2.5-72B-Instruct` model
4. Parses the model's JSON response into an SREAction
5. Steps the environment with that action
6. Repeats until the episode is done
7. Prints the final score for each task

It uses your HF token (not Gemini, not OpenAI) via:
- base_url: https://router.huggingface.co/v1
- api_key: your HF_TOKEN environment variable

---

## KEY TECHNICAL CONSTRAINTS EVERY AGENT MUST KNOW

1. Python version is 3.11. f-strings with walrus operators and match/case are fine.
2. Pydantic v2 is used. Use `model_dump()` not `.dict()`. Use `model_validate_json()` not `parse_raw()`.
3. The environment class must extend `Environment` from `openenv.core.env_server.interfaces`.
4. The `reset()` method signature accepts `task` and `seed` params.
5. The `step()` method must return an `SREObservation` with `done`, `reward`, and `metadata` fields.
6. `state` is a property returning a `State` object from `openenv.core.env_server.types`.
7. All imports from openenv use try/except with both relative and absolute paths — keep this pattern.
8. The graders live in `server/graders/` and are imported inside `_grade()` to avoid circular imports.
9. The incident data lives in `server/data/` — the path is resolved using `Path(__file__).parent / "data"`.
10. app.py uses `create_app()` — this is the ONLY way the server is wired. Do not add routes to app.py.

---

## WHAT HAPPENS IF AN AGENT HALLUCINATES

Common hallucinations to watch for and reject:

| Hallucination | Reality |
|--------------|---------|
| Agent tries to create app.py from scratch | app.py already exists and works. Reject. |
| Agent adds Flask or custom FastAPI routes | create_app() handles all routes. Reject. |
| Agent uses `.dict()` on Pydantic models | Must use `.model_dump()`. Fix it. |
| Agent imports from `gymnasium` | This project uses openenv-core, not gymnasium. Reject. |
| Agent creates a `requirements.txt` at root | requirements.txt lives in `server/`. Root has `pyproject.toml`. |
| Agent uses `GEMINI_API_KEY` | Baseline uses `HF_TOKEN` only. Reject. |
| Agent writes `time.sleep()` in baseline | Not needed. HF router has no 15 RPM limit. Remove it. |
| Agent creates new endpoint files | All endpoints come from create_app(). Reject. |

---

## FILE OWNERSHIP — WHO WRITES WHAT

| File | Owner | Action |
|------|-------|--------|
| models.py | Antigravity | Rewrite with SRE models |
| server/openenv_sre_environment.py | Antigravity | Rewrite with SRE logic |
| server/graders/__init__.py | Antigravity | Create empty |
| server/graders/easy_grader.py | Antigravity | Create |
| server/graders/medium_grader.py | Antigravity | Create |
| server/graders/hard_grader.py | Antigravity | Create |
| baseline_agent.py | Antigravity | Create at root |
| server/data/incidents_easy.json | Gemini CLI | Create — 10 incidents |
| server/data/incidents_medium.json | Gemini CLI | Create — 10 incidents |
| server/data/incidents_hard.json | Gemini CLI | Create — 10 incidents |
| simulator_spec.md | Gemini CLI | Create at root |
| openenv.yaml | Kilocode | Update |
| server/Dockerfile | Kilocode | Update |
| server/requirements.txt | Kilocode | Update |
| README.md | Kilocode | Rewrite |
| .dockerignore | Kilocode | Create |
| app.py | NOBODY | Do not touch |
| client.py | NOBODY | Do not touch |
| pyproject.toml | NOBODY | Do not touch |
| __init__.py files (existing) | NOBODY | Do not touch |

---

# MANUAL WORK GUIDE — FOR YOU (THE HUMAN)
# Everything in this section is YOUR job. No agent does this.

---

## BEFORE YOU START — ONE-TIME SETUP

These are done once. Never again.

**Step 1 — Create GitHub repo**
- Go to github.com/new
- Name: openenv-sre
- Public
- No template, no README, no .gitignore
- Click Create
- Copy the repo URL

**Step 2 — Connect your project folder to GitHub**
Open PowerShell inside your openenv-sre folder:
```powershell
git init
git remote add origin YOUR_GITHUB_REPO_URL
git add .
git commit -m "initial scaffold from openenv init"
git push -u origin main
```

**Step 3 — Create HF Space**
- Go to huggingface.co/new-space
- Space name: openenv-sre
- SDK: Docker
- Visibility: Public
- Click Create Space

**Step 4 — Get HF write token**
- Go to huggingface.co/settings/tokens
- Click New Token
- Name it anything
- Permission: Check "Make calls to Inference Providers" under Inference
- Copy the token (starts with hf_)
- Save it somewhere safe

**Step 5 — Set your HF token in PowerShell**
```powershell
$env:HF_TOKEN="hf_your_token_here"
```
Do this every time you open a new PowerShell window before running baseline_agent.py.
Or set it permanently (only need to do once):
```powershell
[System.Environment]::SetEnvironmentVariable("HF_TOKEN","hf_your_token_here","User")
```
Then close and reopen PowerShell.

---

## YOUR JOBS DURING THE BUILD (phase by phase)

### Before Phase 1
- Confirm all 4 terminals are open and `cd`'d into openenv-sre
- Verify with `pwd` or `cd` in each terminal — all must show same path

### After Phase 1 (Kilocode done)
Check these yourself:
```powershell
cat openenv.yaml        # should show tasks: easy, medium, hard
cat server/Dockerfile   # should show EXPOSE 8000
```

### After Phase 2 (Gemini CLI done)
Check these yourself:
```powershell
# Count incidents in each file — must be 10 each
python -c "import json; data=json.load(open('server/data/incidents_easy.json')); print(len(data), 'easy incidents')"
python -c "import json; data=json.load(open('server/data/incidents_medium.json')); print(len(data), 'medium incidents')"
python -c "import json; data=json.load(open('server/data/incidents_hard.json')); print(len(data), 'hard incidents')"
```

### After Phase 3 (Antigravity models done)
Check yourself:
```powershell
python -c "from models import SREAction, SREObservation, ServiceMetrics; print('models ok')"
```
If this fails, tell Antigravity the exact error before moving to Phase 4.

### After Phase 4 (Antigravity environment done)
Check yourself:
```powershell
uv run server
```
Open browser at http://localhost:8000/schema
Must return JSON. Must NOT show an error page.
Press Ctrl+C to stop the server after checking.

### After Phase 5 (Antigravity graders done)
Check yourself:
```powershell
python -c "
from server.graders.easy_grader import grade as eg
from server.graders.medium_grader import grade as mg
from server.graders.hard_grader import grade as hg
f = {'metrics': [{'healthy': True}]*6}
i = {'metrics': [{'healthy': False}]*6}
print('easy:', eg(i, f, []))
print('medium:', mg(i, f, []))
print('hard:', hg(i, f, []))
"
```
All 3 must print a number between 0.0 and 1.0.

### After Phase 6 (Antigravity baseline done)
Set your HF token then run:
```powershell
$env:HF_TOKEN="hf_your_token_here"
python baseline_agent.py
```
Must print 3 scores. If any score is 0.00 and all steps say OBSERVE,
the HF token is wrong or the model call failed. Tell Antigravity the exact error.

### After Phase 7 (OpenCode GitHub push done)
- Open github.com in browser
- Go to your openenv-sre repo
- Confirm all files are visible
- Confirm the commit message matches what OpenCode wrote

### Phase 8 — HF SPACE DEPLOY (your manual job)
This is the most important manual step. Do it carefully.

```powershell
# Only needed once — adds HF Space as a git remote
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/openenv-sre

# Push code to HF Space
git push space main
```

Wait 3–5 minutes. Watch the build logs on your Space page.

Then verify the Space is working:
```powershell
curl https://YOUR_HF_USERNAME-openenv-sre.hf.space/schema
```
Must return JSON. If it returns an error or times out, check the build
logs on the Space page for the error before moving to Phase 9.

### After Phase 9 (Antigravity validation done)
- Check that README.md now has real numbers in the Baseline Scores table
- Confirm openenv validate passed (Antigravity will report this)

### After Phase 10 (OpenCode final push done)
**Pre-submission checklist — do this yourself:**

```powershell
# Test 1 — schema endpoint
curl https://YOUR_HF_USERNAME-openenv-sre.hf.space/schema

# Test 2 — reset endpoint
curl -X POST https://YOUR_HF_USERNAME-openenv-sre.hf.space/reset `
  -H "Content-Type: application/json" `
  -d "{`"task`":`"easy`",`"seed`":42}"

# Test 3 — Docker build
docker build -t openenv-sre .
```

All 3 must succeed before you submit.

---

## SUBMISSION (you do this, April 7 before 11:59 PM IST)

1. Go to the hackathon dashboard at scaler.com
2. Click Submit
3. Paste your HF Space URL:
   `https://huggingface.co/spaces/YOUR_HF_USERNAME/openenv-sre`
4. Click confirm

That is it. Do not submit until curl tests above pass.

---

## IF SOMETHING BREAKS — YOUR DECISION TREE

**Agent is stuck on same error for 20+ minutes:**
→ Copy the exact error text
→ Tell that agent: "Stop. The error is: [paste error]. Fix only this error. Nothing else."

**Server starts but /schema returns 404:**
→ The app.py create_app() call is broken
→ Tell Antigravity: "uv run server starts but /schema returns 404. Check that app.py create_app() is still intact and that openenv_sre_environment.py imports are correct."

**Baseline prints all 0.00 scores:**
→ Check HF token is set: `echo $env:HF_TOKEN`
→ If token is set, tell Antigravity: "baseline_agent.py runs but all scores are 0.00. The model is likely returning non-JSON. Add a print(raw) line before action = SREAction.model_validate_json(raw) to see what the model is actually returning."

**HF Space build fails:**
→ Click "Build logs" on your Space page
→ Find the first ERROR line
→ If it says "module not found" — requirements.txt is missing a package. Add it and push again.
→ If it says "port already in use" — the Dockerfile EXPOSE port doesn't match app_port in README front matter. Both must be 8000.

**Git push to space is rejected:**
→ Run: `git push space main --force`
→ Only use force push on the space remote, never on origin.

---

## THINGS YOU MUST NEVER DO

- Never edit files while an agent is actively writing them
- Never run `git push origin main --force`
- Never close a terminal mid-phase
- Never submit before /schema curl returns valid JSON
- Never move to the next phase before verifying the current one yourself
- Never share your HF token in any chat, file, or commit
