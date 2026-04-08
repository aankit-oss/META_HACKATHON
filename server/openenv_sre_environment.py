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
        """Build observation — shows all alerts but hides is_false_positive field."""
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
        try:
            if difficulty == "easy":
                from server.graders.easy_grader import grade
            elif difficulty == "medium":
                from server.graders.medium_grader import grade
            else:
                from server.graders.hard_grader import grade
        except ImportError:
            if difficulty == "easy":
                from graders.easy_grader import grade
            elif difficulty == "medium":
                from graders.medium_grader import grade
            else:
                from graders.hard_grader import grade

        initial = {"metrics": list(self._incident["initial_metrics"].values())}
        final = {"metrics": list(self._metrics.values())}
        return grade(initial, final, self._action_history)
