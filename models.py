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


# Aliases for app.py backward compatibility (app.py cannot be modified).
OpenenvSreAction = SREAction
OpenenvSreObservation = SREObservation
