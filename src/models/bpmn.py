from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BPMNNodeType(Enum):
    START_EVENT = "startEvent"
    END_EVENT = "endEvent"
    TASK = "task"
    EXCLUSIVE_GATEWAY = "exclusiveGateway"
    CONVERGING_GATEWAY = "convergingGateway"


@dataclass
class BPMNNode:
    """A node in the BPMN process graph."""

    id: str
    node_type: BPMNNodeType
    name: str
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 80.0


@dataclass
class Waypoint:
    """A coordinate point for sequence flow routing."""

    x: float
    y: float


@dataclass
class BPMNSequenceFlow:
    """A directed edge between two BPMN nodes."""

    id: str
    source_ref: str
    target_ref: str
    name: str = ""
    waypoints: list[Waypoint] = field(default_factory=list)


@dataclass
class BPMNProcess:
    """A complete BPMN process ready for XML serialization."""

    id: str = "Process_1"
    name: str = "SOP Process"
    nodes: list[BPMNNode] = field(default_factory=list)
    sequence_flows: list[BPMNSequenceFlow] = field(default_factory=list)
