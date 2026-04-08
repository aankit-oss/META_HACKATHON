import json
from typing import Dict, Optional
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import SREAction, SREObservation, ServiceMetrics, AlertItem
except ImportError:
    from models import SREAction, SREObservation, ServiceMetrics, AlertItem


class OpenenvSreEnv(EnvClient[SREAction, SREObservation, State]):
    """
    Client for the SRE Incident Response OpenEnv environment.

    Maintains a persistent WebSocket connection to the environment server.
    Each client instance has its own dedicated session on the server.

    Example with running server:
        >>> with OpenenvSreEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset(task="easy", seed=42)
        ...     print(result.observation.incident_id)
        ...     result = client.step(SREAction(action_type="OBSERVE", service="api"))

    Example with Docker:
        >>> client = OpenenvSreEnv.from_docker_image("openenv-sre")
        >>> try:
        ...     result = client.reset(task="easy", seed=42)
        ...     result = client.step(SREAction(action_type="ROLLBACK_DEPLOY", service="api"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: SREAction) -> Dict:
        """Convert SREAction to JSON payload for step message."""
        payload = {"action_type": action.action_type}
        if action.service is not None:
            payload["service"] = action.service
        if action.replicas is not None:
            payload["replicas"] = action.replicas
        if action.queue is not None:
            payload["queue"] = action.queue
        if action.from_service is not None:
            payload["from_service"] = action.from_service
        if action.to_service is not None:
            payload["to_service"] = action.to_service
        if action.pct is not None:
            payload["pct"] = action.pct
        if action.flag is not None:
            payload["flag"] = action.flag
        if action.value is not None:
            payload["value"] = action.value
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[SREObservation]:
        """Parse server response into StepResult[SREObservation]."""
        obs_data = payload.get("observation", {})

        # Parse metrics list
        metrics = [
            ServiceMetrics(**m)
            for m in obs_data.get("metrics", [])
        ]

        # Parse alerts list — strip is_false_positive if present
        alerts = [
            AlertItem(
                alert_id=a.get("alert_id", ""),
                service=a.get("service", ""),
                severity=a.get("severity", "warning"),
                message=a.get("message", ""),
            )
            for a in obs_data.get("alerts", [])
        ]

        observation = SREObservation(
            step=obs_data.get("step", 0),
            alerts=alerts,
            metrics=metrics,
            dependency_graph=obs_data.get("dependency_graph", {}),
            incident_id=obs_data.get("incident_id", ""),
            steps_remaining=obs_data.get("steps_remaining", 0),
            last_action_result=obs_data.get("last_action_result", ""),
            task=obs_data.get("task", "easy"),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=payload.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State object."""
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )


# Alias used by inference.py
OpenenvSreClient = OpenenvSreEnv
