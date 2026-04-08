---
title: SRE Incident Response OpenEnv
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 8000
pinned: true
---

# SRE Incident Response — OpenEnv Environment

## Overview
This environment simulates a Site Reliability Engineer (SRE) responding to production incidents in a synthetic 6-service microservice system. An AI agent observes alerts and metrics, then executes runbook actions to restore all services to a healthy state. It is built for the Meta x PyTorch OpenEnv Hackathon to train and evaluate AI agents for production incident response workflows.

## System Topology
```
gateway → api → db
                ↑
         api → cache
         api → queue → worker
```

## Tasks

### Task 1: Easy — Single Service Incident (max 10 steps)
A single service experiences an incident requiring one correct action to resolve. Example: API has high error_rate after a bad deploy → agent runs ROLLBACK_DEPLOY on api → episode ends. Grader scores: Start 1.0, -0.5 if any service unhealthy, -0.1 per no_effect, -0.15 per invalid, +0.1 speed bonus if resolved in 5 steps or fewer.

### Task 2: Medium — Cascading Failure (max 20 steps)
Multi-service incident where 2–3 services are unhealthy. One false positive alert is included. Agent needs 2–3 ordered actions to resolve. Example: db overloaded → api degraded → agent scales up db first, then restarts api. Grader scores: Start 1.0, -0.2 per unhealthy service, -0.1 per invalid, -0.2 per false positive acted on, +0.1 bonus if resolved in 12 steps or fewer.

### Task 3: Hard — Noisy Multi-Signal Incident (max 35 steps)
Complex incident with 3–5 services unhealthy and 2–3 false positive alerts included. Agent must filter noise and identify root cause, requiring 3–5 correct actions. Grader scores: Start 1.0, -0.15 per unhealthy service, -0.25 per harmful action, -0.15 per false positive acted on, +0.15 if all healthy, +0.1 additional if all healthy AND resolved in 20 steps or fewer.

## Action Space

| Action | Target | Effect |
|--------|--------|--------|
| RESTART_SERVICE | service | Sets latency=260, error=0.02, cpu=40 |
| ROLLBACK_DEPLOY | service | Same as restart if error_rate > 0.30, else no_effect |
| SCALE_UP | service, replicas | Reduces cpu by 30, latency by 50 |
| SCALE_DOWN | service, replicas | Increases cpu by 20. Harmful if service was healthy |
| DRAIN_QUEUE | queue | Fixes queue+worker to healthy metrics |
| SHIFT_TRAFFIC | from_service, to_service, pct | Moves traffic. Harmful if target goes > 80 cpu |
| TOGGLE_FEATURE_FLAG | flag, value=False | Sets api error_rate to 0.01 if value=False |
| CLEAR_CACHE | service | Sets cache to healthy metrics |
| OBSERVE | service | No state change |

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| step | int | Current step number |
| alerts | list[AlertItem] | Active alerts visible to agent |
| metrics | list[ServiceMetrics] | Current metrics for all 6 services |
| dependency_graph | dict | Service dependency map |
| incident_id | str | Active incident identifier |
| steps_remaining | int | Steps left in episode |
| last_action_result | str | Result of last action taken |

## Reward Function

| Event | Reward |
|-------|--------|
| Service transitions unhealthy→healthy | +0.4 |
| Correct root cause acted on | +0.3 |
| Any metric improves | +0.2 |
| Valid action no change | +0.0 |
| Invalid action | -0.2 |
| Action degrades healthy service | -0.3 |
| Acting on false positive | -0.2 |
| Step cost | -0.05 |
| Episode end | +grader score |

## Setup

### Run locally
```
pip install "openenv-core[core]>=0.2.1"
uv run server
```

### Run with Docker
```
docker build -t openenv-sre .
docker run -p 8000:8000 openenv-sre
```

### Run baseline agent
```
set HF_TOKEN=your_hf_token_here   (Windows)
export HF_TOKEN=your_hf_token_here (Linux/Mac)
python baseline_agent.py
```

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
