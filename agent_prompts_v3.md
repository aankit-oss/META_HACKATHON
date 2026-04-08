# Agent Prompts v3 — openenv-sre
# Based on actual openenv init scaffold structure
# You are the orchestrator. Follow the phase order table.

---

## CRITICAL — READ BEFORE ANYTHING

openenv init already created the project scaffold.
The HTTP server, WebSocket, /reset, /step, /state endpoints are ALL handled
automatically by create_app() in app.py. Do not touch app.py.
Do not rewrite the server. Do not add FastAPI routes manually.

Your agents only fill in the SRE logic inside the scaffolded files.

---

## ACTUAL PROJECT STRUCTURE (from openenv init)

```
openenv-sre/
│   client.py                          ← DO NOT TOUCH
│   models.py                          ← ANTIGRAVITY REWRITES THIS
│   openenv.yaml                       ← KILOCODE UPDATES THIS
│   pyproject.toml                     ← DO NOT TOUCH
│   README.md                          ← KILOCODE REWRITES THIS
│   __init__.py                        ← DO NOT TOUCH
│
└───server/
    │   app.py                         ← DO NOT TOUCH
    │   Dockerfile                     ← KILOCODE UPDATES THIS
    │   openenv_sre_environment.py     ← ANTIGRAVITY REWRITES THIS
    │   requirements.txt               ← KILOCODE UPDATES THIS
    │   __init__.py                    ← DO NOT TOUCH
    │
    ├───data/                          ← GEMINI CLI CREATES THIS
    │       incidents_easy.json
    │       incidents_medium.json
    │       incidents_hard.json
    │
    └───graders/                       ← ANTIGRAVITY CREATES THIS
            __init__.py
            easy_grader.py
            medium_grader.py
            hard_grader.py
```

New files to create:
- `server/data/` folder + 3 JSON files (Gemini CLI)
- `server/graders/` folder + 4 files (Antigravity)
- `baseline_agent.py` at root level (Antigravity)

---

## PHASE ORDER — YOUR ORCHESTRATION TABLE

| Phase | Agent | Job | Verify Before Next Phase |
|-------|-------|-----|--------------------------|
| 1 | Kilocode | Update openenv.yaml, Dockerfile, requirements.txt, README.md | 4 files updated, no syntax errors |
| 2 | Gemini CLI | Create server/data/ + 3 incident JSON files + simulator_spec.md | 30 incidents exist, all fields present |
| 3 | Antigravity | Rewrite models.py | `python -c "from models import SREAction, SREObservation"` passes |
| 4 | Antigravity | Rewrite server/openenv_sre_environment.py | `uv run server` starts on port 8000 |
| 5 | Antigravity | Create server/graders/ + 3 grader files | All graders return float in [0.0, 1.0] |
| 6 | Antigravity | Create baseline_agent.py | Script runs, prints 3 scores |
| 7 | OpenCode | Git commit + push to GitHub | Commit visible on GitHub |
| 8 | YOU | HF Space deploy | Space URL returns 200 on /schema |
| 9 | Antigravity | Final validation | openenv validate passes |
| 10 | OpenCode | Final push to GitHub + HF Space | Both updated |

---

## KILOCODE — PHASE 1

Tell Kilocode:
> "Read agent_prompts_v3.md. Your section is KILOCODE PHASE 1. Follow only your section."

---

### YOUR JOB
Update 4 existing files. Do not create new files. Do not touch app.py or any Python logic.

### FILE 1 — openenv.yaml (UPDATE, do not replace entirely)

Replace the existing content with:
```yaml
spec_version: 1
name: openenv_sre
type: space
runtime: fastapi
app: server.app:app
port: 8000

description: >
  SRE Incident Response environment. Agent observes synthetic microservice
  alerts and metrics, executes runbook actions to restore system health.
  Simulates real on-call SRE workflows for agent training and evaluation.

tasks:
  - id: easy
    description: Single-service incident, one correct action required
    max_steps: 10
    difficulty: easy
  - id: medium
    description: Multi-service cascading incident, ordered action sequence
    max_steps: 20
    difficulty: medium
  - id: hard
    description: Noisy multi-signal incident with false positives and trade-offs
    max_steps: 35
    difficulty: hard

services:
  - gateway
  - api
  - db
  - cache
  - queue
  - worker

reward_range: [-1.0, 1.0]
score_range: [0.0, 1.0]
```

### FILE 2 — server/requirements.txt (UPDATE)

Replace contents with:
```
fastapi
uvicorn[standard]
pydantic>=2.0.0
openenv-core>=0.2.1
openai>=1.0.0
huggingface_hub>=0.20.0
pytest>=8.0.0
```

### FILE 3 — server/Dockerfile (UPDATE)

Replace contents with:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN adduser --disabled-password --gecos "" appuser
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/schema || exit 1
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Also create `.dockerignore` in project root:
```
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.env
venv/
env/
.git/
uv.lock
*.egg-info/
```

### FILE 4 — README.md (REWRITE)

Put this HF Spaces front matter at the very top:
```
---
title: SRE Incident Response OpenEnv
emoji: 🚨
colorFrom: red
colorTo: orange
sdk: docker
app_port: 8000
pinned: true
---
```

Then these sections in order:

```
# SRE Incident Response — OpenEnv Environment

## Overview
3 sentences: what it simulates, why it matters for AI agents,
built for Meta x PyTorch OpenEnv Hackathon.

## System Topology
Include this ASCII diagram:
gateway → api → db
                ↑
         api → cache
         api → queue → worker

## Tasks
### Task 1: Easy — Single Service Incident (max 10 steps)
### Task 2: Medium — Cascading Failure (max 20 steps)
### Task 3: Hard — Noisy Multi-Signal Incident (max 35 steps)
For each: scenario, correct resolution, how grader scores it.

## Action Space
Table: Action | Target | Effect
RESTART_SERVICE, ROLLBACK_DEPLOY, SCALE_UP, SCALE_DOWN,
DRAIN_QUEUE, SHIFT_TRAFFIC, TOGGLE_FEATURE_FLAG, CLEAR_CACHE, OBSERVE

## Observation Space
Table: Field | Type | Description
step, alerts, metrics, dependency_graph, incident_id,
steps_remaining, last_action_result

## Reward Function
Table: Event | Reward
Service transitions unhealthy→healthy: +0.4
Correct root cause acted on: +0.3
Any metric improves: +0.2
Valid action no change: +0.0
Invalid action: -0.2
Action degrades healthy service: -0.3
Acting on false positive: -0.2
Step cost: -0.05
Episode end: +grader score

## Setup
### Run locally
pip install "openenv-core[core]>=0.2.1"
uv run server

### Run with Docker
docker build -t openenv-sre .
docker run -p 8000:8000 openenv-sre

### Run baseline agent
set HF_TOKEN=your_hf_token_here   (Windows)
export HF_TOKEN=your_hf_token_here (Linux/Mac)
python baseline_agent.py

## Baseline Scores
| Task   | Model                    | Score | Steps |
|--------|--------------------------|-------|-------|
| easy   | Qwen/Qwen2.5-72B-Instruct | TBD  | TBD   |
| medium | Qwen/Qwen2.5-72B-Instruct | TBD  | TBD   |
| hard   | Qwen/Qwen2.5-72B-Instruct | TBD  | TBD   |

## HF Space
[PLACEHOLDER — paste Space URL here after deploy]

## License
MIT
```

### DONE CRITERIA
Reply DONE when all 4 files are updated and .dockerignore exists.
List each filename in your reply.

---

## GEMINI CLI — PHASE 2

Tell Gemini CLI:
> "Read agent_prompts_v3.md. Your section is GEMINI CLI PHASE 2. Follow only your section."

---

### YOUR JOB
Create the incident data files and simulator spec.
Your large context window is why you have this job — keep all 30 incidents
consistent across 6 services, 6 incident types, 3 difficulty levels.

Create folder `server/data/` and these files inside it:
- `incidents_easy.json`
- `incidents_medium.json`
- `incidents_hard.json`

Also create `simulator_spec.md` in the project root.

### INCIDENT JSON FORMAT

Each incident object must have exactly these fields:
```json
{
  "incident_id": "easy_001",
  "incident_type": "BAD_DEPLOY",
  "description": "One sentence describing what went wrong.",
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

### METRIC RANGES

Healthy services:
- latency_ms: 80–290
- error_rate: 0.00–0.04
- cpu_pct: 20–75
- healthy: true

Unhealthy services:
- latency_ms: 400–2000
- error_rate: 0.08–0.65
- cpu_pct: 82–98
- healthy: false

### DEPENDENCY GRAPH (cascade effects must respect this)
```
gateway → api → db
                ↑
         api → cache
         api → queue → worker
```
If db is unhealthy, api should also show degraded metrics.
If queue is unhealthy, worker should also show degraded metrics.

### incidents_easy.json — 10 incidents
- Types: BAD_DEPLOY or QUEUE_BACKUP only
- Exactly 1 service unhealthy
- 0 false positive alerts
- ground_truth_actions: exactly 1 action

### incidents_medium.json — 10 incidents
- Types: DB_OVERLOAD or CACHE_MISS_STORM only
- Exactly 2–3 services unhealthy
- Exactly 1 false positive alert per incident
- ground_truth_actions: 2–3 actions in correct order

### incidents_hard.json — 10 incidents
- Types: REGION_PARTIAL or CASCADING only
- Exactly 3–5 services unhealthy
- Exactly 2–3 false positive alerts per incident
- ground_truth_actions: 3–5 actions in correct order

### RULES
- No two incidents have identical initial_metrics
- incident_id unique across all 30: easy_001–easy_010, medium_001–medium_010, hard_001–hard_010
- ground_truth_actions format: "ACTION_NAME:target" e.g. "ROLLBACK_DEPLOY:api"

### simulator_spec.md — create in project root

Write exact before/after metric values for all 9 actions:
```
## RESTART_SERVICE(service)
After: latency_ms=260, error_rate=0.02, cpu_pct=40, healthy=recompute
Result: "success"

## ROLLBACK_DEPLOY(service)
If error_rate > 0.30: same as RESTART_SERVICE, result="success"
If error_rate <= 0.30: result="no_effect"

## SCALE_UP(service, replicas)
After: cpu_pct = max(10, cpu_pct - 30), latency_ms = max(80, latency_ms - 50)
Result: "success"

## SCALE_DOWN(service, replicas)
After: cpu_pct = min(100, cpu_pct + 20)
If service was healthy before: result="harmful"
Else: result="success"

## DRAIN_QUEUE(queue)
queue: latency_ms=150, error_rate=0.01, cpu_pct=30
worker: latency_ms=200, error_rate=0.01, cpu_pct=35
Both: healthy=recompute, result="success"

## SHIFT_TRAFFIC(from_service, to_service, pct)
from_service.cpu_pct = max(10, cpu_pct - pct*0.3)
to_service.cpu_pct = cpu_pct + pct*0.2
If to_service.cpu_pct > 80 after: result="harmful"
Else: result="success"

## TOGGLE_FEATURE_FLAG(flag, value=False)
api.error_rate=0.01, api.healthy=recompute, result="success"
If value=True: result="no_effect"

## CLEAR_CACHE(service)
cache: latency_ms=120, error_rate=0.01, cpu_pct=25, healthy=True
Result: "success"

## OBSERVE(service)
No state change. Result: "no_effect"

## INVALID action_type
Result: "invalid"

## Health recompute rule
healthy = True if latency_ms < 300 AND error_rate < 0.05 AND cpu_pct < 80
```

### DONE CRITERIA
Reply DONE when:
- server/data/incidents_easy.json exists with exactly 10 incidents
- server/data/incidents_medium.json exists with exactly 10 incidents
- server/data/incidents_hard.json exists with exactly 10 incidents
- simulator_spec.md exists in project root

---

## ANTIGRAVITY — PHASE 3 (Rewrite models.py)

Tell Antigravity:
> "Read agent_prompts_v3.md. Your section is ANTIGRAVITY PHASE 3. Follow only your section."

---

### YOUR JOB
Rewrite models.py at the project root.
Keep the same import style as the original — it uses openenv.core.env_server.types.
Replace the echo models with SRE models.

```python
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the SRE Incident Response OpenEnv environment.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import Optional


class ServiceMetrics(Action):
    """Metrics for a single microservice."""
    service: str = Field(..., description="Service name")
    latency_ms: float = Field(..., description="p99 latency in milliseconds")
    error_rate: float = Field(..., description="Error rate 0.0-1.0")
    cpu_pct: float = Field(..., description="CPU utilization percentage")
    healthy: bool = Field(..., description="True if all thresholds met")


class SREAction(Action):
    """Runbook action the agent can execute."""
    action_type: str = Field(..., description=(
        "One of: RESTART_SERVICE, ROLLBACK_DEPLOY, SCALE_UP, SCALE_DOWN, "
        "DRAIN_QUEUE, SHIFT_TRAFFIC, TOGGLE_FEATURE_FLAG, CLEAR_CACHE, OBSERVE"
    ))
    service: Optional[str] = Field(default=None, description="Target service name")
    replicas: Optional[int] = Field(default=None, description="Number of replicas for scaling")
    queue: Optional[str] = Field(default=None, description="Queue name for DRAIN_QUEUE")
    from_service: Optional[str] = Field(default=None, description="Source for SHIFT_TRAFFIC")
    to_service: Optional[str] = Field(default=None, description="Destination for SHIFT_TRAFFIC")
    pct: Optional[int] = Field(default=None, description="Percentage for SHIFT_TRAFFIC")
    flag: Optional[str] = Field(default=None, description="Feature flag name")
    value: Optional[bool] = Field(default=None, description="Feature flag value")


class AlertItem(Action):
    """A single alert (is_false_positive hidden from agent)."""
    alert_id: str = Field(..., description="Unique alert identifier")
    service: str = Field(..., description="Service that triggered alert")
    severity: str = Field(..., description="warning or critical")
    message: str = Field(..., description="Human-readable alert message")


class SREObservation(Observation):
    """What the agent sees each step."""
    step: int = Field(default=0, description="Current step number")
    alerts: list[AlertItem] = Field(default_factory=list, description="Active alerts visible to agent")
    metrics: list[ServiceMetrics] = Field(default_factory=list, description="Current metrics for all 6 services")
    dependency_graph: dict = Field(default_factory=dict, description="Service dependency map")
    incident_id: str = Field(default="", description="Active incident identifier")
    steps_remaining: int = Field(default=10, description="Steps left in episode")
    last_action_result: str = Field(default="reset", description="Result of last action taken")
    task: str = Field(default="easy", description="Current task difficulty")
```

### DONE CRITERIA
Run this and reply DONE only when it passes:
```
python -c "from models import SREAction, SREObservation, ServiceMetrics, AlertItem; print('models ok')"
```

---

## ANTIGRAVITY — PHASE 4 (Rewrite openenv_sre_environment.py)

Tell Antigravity:
> "Read agent_prompts_v3.md. Your section is ANTIGRAVITY PHASE 4. Follow only your section."

---

### YOUR JOB
Rewrite server/openenv_sre_environment.py.
Keep the same class structure and imports as the original.
The class must still extend Environment from openenv.core.
Read simulator_spec.md for exact action effects.

```python
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
SRE Incident Response Environment Implementation.

Agent observes microservice alerts and metrics, executes runbook actions
to restore system health. Simulates real on-call SRE workflows.
"""

import json
import random
from pathlib import Path
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import SREAction, SREObservation, ServiceMetrics, AlertItem
except ImportError:
    from models import SREAction, SREObservation, ServiceMetrics, AlertItem

DATA_DIR = Path(__file__).parent / "data"

DEPENDENCY_GRAPH = {
    "gateway": ["api"],
    "api": ["db", "cache", "queue"],
    "queue": ["worker"],
    "db": [],
    "cache": [],
    "worker": []
}

HEALTHY_THRESHOLDS = {"latency_ms": 300, "error_rate": 0.05, "cpu_pct": 80}

VALID_ACTIONS = [
    "RESTART_SERVICE", "ROLLBACK_DEPLOY", "SCALE_UP", "SCALE_DOWN",
    "DRAIN_QUEUE", "SHIFT_TRAFFIC", "TOGGLE_FEATURE_FLAG", "CLEAR_CACHE", "OBSERVE"
]

SUPPORTS_CONCURRENT_SESSIONS: bool = True


class OpenenvSreEnvironment(Environment):
    """
    SRE Incident Response environment.

    The agent observes alerts and metrics from a 6-service microservice system
    and executes runbook actions to resolve incidents and restore system health.

    Tasks:
        easy:   1 service affected, 1 action needed, max 10 steps
        medium: 2-3 services affected, ordered actions, max 20 steps
        hard:   3-5 services affected, false positives, max 35 steps
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._metrics: dict[str, dict] = {}
        self._incident: dict = {}
        self._action_history: list = []
        self._last_result: str = "reset"
        self._task: str = "easy"
        self._max_steps: int = 10
        self._seed: int | None = None

    def reset(self, task: str = "easy", seed: int | None = None) -> SREObservation:
        """Reset environment and load a new incident."""
        self._task = task
        self._seed = seed
        self._max_steps = {"easy": 10, "medium": 20, "hard": 35}[task]
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._action_history = []
        self._last_result = "reset"

        # Load incident
        incidents = self._load_incidents(task)
        rng = random.Random(seed)
        self._incident = rng.choice(incidents)

        # Init metrics from incident
        self._metrics = {
            k: dict(v) for k, v in self._incident["initial_metrics"].items()
        }

        return self._make_observation()

    def step(self, action: SREAction) -> SREObservation:  # type: ignore[override]
        """Execute a runbook action and return updated observation."""
        self._state.step_count += 1

        prev_healthy = {s: m["healthy"] for s, m in self._metrics.items()}
        result = self._apply_action(action)
        self._last_result = result
        self._action_history.append({
            "action": action.model_dump(),
            "result": result,
            "step": self._state.step_count
        })

        reward = self._compute_reward(action, result, prev_healthy)
        terminated = all(m["healthy"] for m in self._metrics.values())
        truncated = self._state.step_count >= self._max_steps

        obs = self._make_observation()
        obs.done = terminated or truncated

        if terminated or truncated:
            score = self._grade()
            obs.reward = reward + score
            obs.metadata = {"episode_score": score, "resolved": terminated}
        else:
            obs.reward = reward

        return obs

    @property
    def state(self) -> State:
        return self._state

    # ── private helpers ──────────────────────────────────────────────────────

    def _load_incidents(self, difficulty: str) -> list[dict]:
        path = DATA_DIR / f"incidents_{difficulty}.json"
        with open(path) as f:
            return json.load(f)

    def _make_observation(self) -> SREObservation:
        """Build observation — strips is_false_positive from alerts."""
        alerts_visible = [
            AlertItem(
                alert_id=a["alert_id"],
                service=a["service"],
                severity=a["severity"],
                message=a["message"]
            )
            for a in self._incident.get("alerts", [])
            if not a.get("is_false_positive", False) or True  # show all, hide field
        ]
        # Strip false positives entirely — agent cannot see which are false
        alerts_visible = [
            AlertItem(
                alert_id=a["alert_id"],
                service=a["service"],
                severity=a["severity"],
                message=a["message"]
            )
            for a in self._incident.get("alerts", [])
        ]
        metrics_list = [
            ServiceMetrics(**m) for m in self._metrics.values()
        ]
        return SREObservation(
            step=self._state.step_count,
            alerts=alerts_visible,
            metrics=metrics_list,
            dependency_graph=DEPENDENCY_GRAPH,
            incident_id=self._incident.get("incident_id", ""),
            steps_remaining=self._max_steps - self._state.step_count,
            last_action_result=self._last_result,
            task=self._task,
            done=False,
            reward=0.0
        )

    def _recompute_health(self, service: str) -> None:
        m = self._metrics[service]
        m["healthy"] = (
            m["latency_ms"] < HEALTHY_THRESHOLDS["latency_ms"] and
            m["error_rate"] < HEALTHY_THRESHOLDS["error_rate"] and
            m["cpu_pct"] < HEALTHY_THRESHOLDS["cpu_pct"]
        )

    def _apply_action(self, action: SREAction) -> str:
        """Apply action using simulator_spec.md rules. Returns result string."""
        atype = action.action_type

        if atype not in VALID_ACTIONS:
            return "invalid"

        if atype == "RESTART_SERVICE":
            if not action.service or action.service not in self._metrics:
                return "invalid"
            m = self._metrics[action.service]
            m["latency_ms"] = 260
            m["error_rate"] = 0.02
            m["cpu_pct"] = 40
            self._recompute_health(action.service)
            return "success"

        elif atype == "ROLLBACK_DEPLOY":
            if not action.service or action.service not in self._metrics:
                return "invalid"
            m = self._metrics[action.service]
            if m["error_rate"] > 0.30:
                m["latency_ms"] = 260
                m["error_rate"] = 0.02
                m["cpu_pct"] = 40
                self._recompute_health(action.service)
                return "success"
            return "no_effect"

        elif atype == "SCALE_UP":
            if not action.service or action.service not in self._metrics:
                return "invalid"
            m = self._metrics[action.service]
            m["cpu_pct"] = max(10, m["cpu_pct"] - 30)
            m["latency_ms"] = max(80, m["latency_ms"] - 50)
            self._recompute_health(action.service)
            return "success"

        elif atype == "SCALE_DOWN":
            if not action.service or action.service not in self._metrics:
                return "invalid"
            was_healthy = self._metrics[action.service]["healthy"]
            m = self._metrics[action.service]
            m["cpu_pct"] = min(100, m["cpu_pct"] + 20)
            self._recompute_health(action.service)
            return "harmful" if was_healthy else "success"

        elif atype == "DRAIN_QUEUE":
            if "queue" not in self._metrics:
                return "invalid"
            self._metrics["queue"].update({"latency_ms": 150, "error_rate": 0.01, "cpu_pct": 30})
            self._metrics["worker"].update({"latency_ms": 200, "error_rate": 0.01, "cpu_pct": 35})
            self._recompute_health("queue")
            self._recompute_health("worker")
            return "success"

        elif atype == "SHIFT_TRAFFIC":
            if not action.from_service or not action.to_service:
                return "invalid"
            if action.from_service not in self._metrics or action.to_service not in self._metrics:
                return "invalid"
            pct = action.pct or 20
            self._metrics[action.from_service]["cpu_pct"] = max(
                10, self._metrics[action.from_service]["cpu_pct"] - pct * 0.3
            )
            self._metrics[action.to_service]["cpu_pct"] += pct * 0.2
            self._recompute_health(action.from_service)
            self._recompute_health(action.to_service)
            if self._metrics[action.to_service]["cpu_pct"] > 80:
                return "harmful"
            return "success"

        elif atype == "TOGGLE_FEATURE_FLAG":
            if action.value is False:
                self._metrics["api"]["error_rate"] = 0.01
                self._recompute_health("api")
                return "success"
            return "no_effect"

        elif atype == "CLEAR_CACHE":
            self._metrics["cache"].update({"latency_ms": 120, "error_rate": 0.01, "cpu_pct": 25, "healthy": True})
            return "success"

        elif atype == "OBSERVE":
            return "no_effect"

        return "invalid"

    def _compute_reward(self, action: SREAction, result: str,
                        prev_healthy: dict[str, bool]) -> float:
        reward = -0.05  # step cost
        if result == "invalid":
            return reward - 0.2
        if result == "harmful":
            return reward - 0.3
        newly_healthy = sum(
            1 for s, was in prev_healthy.items()
            if not was and self._metrics[s]["healthy"]
        )
        if newly_healthy > 0:
            reward += 0.4 * newly_healthy
        if action.service == self._incident.get("ground_truth_root_cause"):
            reward += 0.3
        if result == "success" and newly_healthy == 0:
            reward += 0.2
        return reward

    def _grade(self) -> float:
        difficulty = self._task
        if difficulty == "easy":
            from graders.easy_grader import grade
        elif difficulty == "medium":
            from graders.medium_grader import grade
        else:
            from graders.hard_grader import grade

        initial = {"metrics": list(self._incident["initial_metrics"].values())}
        final = {"metrics": list(self._metrics.values())}
        return grade(initial, final, self._action_history)
```

### DONE CRITERIA
Run this and reply DONE only when it passes:
```
cd openenv-sre
uv run server
```
Server must start on port 8000 with no import errors.
Open http://localhost:8000/schema in browser — must return JSON.

---

## ANTIGRAVITY — PHASE 5 (Graders)

Tell Antigravity:
> "Read agent_prompts_v3.md. Your section is ANTIGRAVITY PHASE 5. Follow only your section."

---

### YOUR JOB
Create server/graders/ folder and 4 files.

### FILE 1 — server/graders/__init__.py
Empty file.

### FILE 2 — server/graders/easy_grader.py
```python
def grade(initial_state: dict, final_state: dict, action_history: list) -> float:
    score = 1.0
    unhealthy = [m for m in final_state["metrics"] if not m["healthy"]]
    if unhealthy:
        score -= 0.5
    for entry in action_history:
        result = entry.get("result", "")
        if result == "no_effect":
            score -= 0.1
        if result == "invalid":
            score -= 0.15
    if not unhealthy and len(action_history) <= 5:
        score += 0.1  # speed bonus
    return max(0.0, min(1.0, score))
```

### FILE 3 — server/graders/medium_grader.py
```python
def grade(initial_state: dict, final_state: dict, action_history: list) -> float:
    score = 1.0
    unhealthy_count = sum(1 for m in final_state["metrics"] if not m["healthy"])
    score -= unhealthy_count * 0.2
    for entry in action_history:
        if entry.get("result") == "invalid":
            score -= 0.1
        if entry.get("acted_on_false_positive"):
            score -= 0.2
    if unhealthy_count == 0 and len(action_history) <= 12:
        score += 0.1
    return max(0.0, min(1.0, score))
```

### FILE 4 — server/graders/hard_grader.py
```python
def grade(initial_state: dict, final_state: dict, action_history: list) -> float:
    score = 1.0
    unhealthy_count = sum(1 for m in final_state["metrics"] if not m["healthy"])
    score -= unhealthy_count * 0.15
    for entry in action_history:
        if entry.get("result") == "harmful":
            score -= 0.25
        if entry.get("acted_on_false_positive"):
            score -= 0.15
    if unhealthy_count == 0:
        score += 0.15
    if unhealthy_count == 0 and len(action_history) <= 20:
        score += 0.1
    return max(0.0, min(1.0, score))
```

### DONE CRITERIA
Run this and reply DONE only when it passes:
```python
python -c "
from server.graders.easy_grader import grade
final = {'metrics': [{'healthy': True}] * 6}
initial = {'metrics': [{'healthy': False}] * 6}
score = grade(initial, final, [])
assert 0.0 <= score <= 1.0
print('graders ok:', score)
"
```

---

## ANTIGRAVITY — PHASE 6 (Baseline Agent)

Tell Antigravity:
> "Read agent_prompts_v3.md. Your section is ANTIGRAVITY PHASE 6. Follow only your section."

---

### YOUR JOB
Create baseline_agent.py at the project root (same level as models.py).
Uses HF Inference Router with openai library. No Gemini. No external key.
Reads HF_TOKEN from environment variable.

```python
"""
Baseline agent for SRE Incident Response OpenEnv environment.
Uses Hugging Face Inference Router (OpenAI-compatible API).
Set HF_TOKEN environment variable before running.

Windows:  set HF_TOKEN=hf_your_token_here
Linux/Mac: export HF_TOKEN=hf_your_token_here
"""

import os
import json
import time
from openai import OpenAI
from server.openenv_sre_environment import OpenenvSreEnvironment
from models import SREAction

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

MODEL = "Qwen/Qwen2.5-72B-Instruct"

SYSTEM_PROMPT = """You are an on-call SRE agent responding to a production incident.
You observe alerts and metrics from a microservice system (gateway, api, db, cache, queue, worker).
Your goal: execute runbook actions to restore ALL services to healthy state.
Healthy = latency_ms < 300 AND error_rate < 0.05 AND cpu_pct < 80.

Respond ONLY with a single valid JSON object matching this schema. Raw JSON, no markdown:
{
  "action_type": "RESTART_SERVICE|ROLLBACK_DEPLOY|SCALE_UP|SCALE_DOWN|DRAIN_QUEUE|SHIFT_TRAFFIC|TOGGLE_FEATURE_FLAG|CLEAR_CACHE|OBSERVE",
  "service": "service_name or null",
  "replicas": null,
  "queue": null,
  "from_service": null,
  "to_service": null,
  "pct": null,
  "flag": null,
  "value": null
}"""


def run_episode(task: str) -> dict:
    env = OpenenvSreEnvironment()
    obs = env.reset(task=task, seed=42)
    total_reward = 0.0
    steps = 0

    while True:
        prompt = f"""Incident: {obs.incident_id}
Steps remaining: {obs.steps_remaining}
Last action result: {obs.last_action_result}

ALERTS:
{json.dumps([a.model_dump() for a in obs.alerts], indent=2)}

METRICS:
{json.dumps([m.model_dump() for m in obs.metrics], indent=2)}

Choose the best single runbook action. Reply JSON only."""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1,
            )
            raw = response.choices[0].message.content.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            action = SREAction.model_validate_json(raw)
        except Exception as e:
            print(f"  Step {steps+1} parse error: {e} — using OBSERVE fallback")
            action = SREAction(action_type="OBSERVE", service="api")

        obs = env.step(action)
        total_reward += obs.reward
        steps += 1
        print(f"  Step {steps}: {action.action_type}({action.service or ''}) → reward={obs.reward:.3f}")

        if obs.done:
            break

    episode_score = obs.metadata.get("episode_score", 0.0) if obs.metadata else 0.0
    resolved = obs.metadata.get("resolved", False) if obs.metadata else False

    return {
        "task": task,
        "score": round(episode_score, 4),
        "total_reward": round(total_reward, 4),
        "steps": steps,
        "resolved": resolved
    }


if __name__ == "__main__":
    if "HF_TOKEN" not in os.environ:
        print("ERROR: HF_TOKEN environment variable not set.")
        print("Windows:   set HF_TOKEN=hf_your_token_here")
        print("Linux/Mac: export HF_TOKEN=hf_your_token_here")
        exit(1)

    results = []
    for task in ["easy", "medium", "hard"]:
        print(f"\nRunning {task} task...")
        result = run_episode(task)
        results.append(result)
        print(f"  Score: {result['score']} | Steps: {result['steps']} | Resolved: {result['resolved']}")

    print("\n=== BASELINE SCORES ===")
    for r in results:
        print(f"{r['task']:8} → score: {r['score']:.4f}  steps: {r['steps']}")
```

### DONE CRITERIA
Set HF_TOKEN in your terminal then run:
```
python baseline_agent.py
```
All 3 tasks must complete and print real scores (not all 0.0).
Reply DONE with the 3 scores printed.

---

## OPENCODE — PHASE 7 (Git + GitHub Push)

Tell OpenCode:
> "Read agent_prompts_v3.md. Your section is OPENCODE PHASE 7. Follow only your section."

---

### YOUR JOB
Stage all files and push to GitHub. No code changes.

```bash
git add .
git status
```

Confirm these files are staged before committing:
```
models.py
openenv.yaml
README.md
.dockerignore
baseline_agent.py
simulator_spec.md
server/openenv_sre_environment.py
server/requirements.txt
server/Dockerfile
server/graders/__init__.py
server/graders/easy_grader.py
server/graders/medium_grader.py
server/graders/hard_grader.py
server/data/incidents_easy.json
server/data/incidents_medium.json
server/data/incidents_hard.json
```

If any file is missing — stop and list what is missing. Do not commit.

If all present:
```bash
git commit -m "feat: SRE incident response OpenEnv environment

- 6-service microservice topology (gateway, api, db, cache, queue, worker)
- 3 tasks: easy/medium/hard with deterministic graders
- 30 incident templates with ground truth actions
- HF Inference Router baseline agent (Qwen2.5-72B)
- openenv init scaffold preserved"

git push origin main
```

### DONE CRITERIA
Reply DONE with the GitHub commit URL.

---

## PHASE 8 — YOU DEPLOY TO HF SPACE (manual)

Do this after OpenCode Phase 7 is confirmed done.

```powershell
# Install HF CLI if not already installed
pip install huggingface_hub

# Login with your HF token
huggingface-cli login
# paste your HF token when asked

# Push to HF Space
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/openenv-sre
git push space main
```

Wait 3–5 minutes for Space to build. Then verify:
```powershell
curl https://YOUR_HF_USERNAME-openenv-sre.hf.space/schema
```
Must return JSON with action and observation schemas.

---

## ANTIGRAVITY — PHASE 9 (Validation)

Tell Antigravity:
> "Read agent_prompts_v3.md. Your section is ANTIGRAVITY PHASE 9. Follow only your section."

---

### YOUR JOB
Run validation. Fix any errors. Do not add features.

```bash
# Step 1 — openenv validate
openenv validate

# Step 2 — local server test
uv run server &
curl http://localhost:8000/schema
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "easy", "seed": 42}'

# Step 3 — baseline one more time to confirm scores
python baseline_agent.py
```

Paste baseline scores into README.md replacing TBD values.

### DONE CRITERIA
Reply DONE with:
- openenv validate result
- /schema curl response (first 3 lines)
- 3 baseline scores

---

## OPENCODE — PHASE 10 (Final Push)

Tell OpenCode:
> "Read agent_prompts_v3.md. Your section is OPENCODE PHASE 10. Follow only your section."

---

### YOUR JOB
Final commit after baseline scores added to README. Push everywhere.

```bash
git add README.md
git diff --cached --stat
git commit -m "docs: add baseline scores and hf space url"
git push origin main
git push space main
```

### DONE CRITERIA
Reply DONE with GitHub commit URL and HF Space URL.
