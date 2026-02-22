from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SOPElementType(Enum):
    STEP = "step"
    DECISION = "decision"


@dataclass
class SOPBranch:
    """One arm of a decision (e.g., 'If yes' or 'If no')."""

    condition_label: str
    steps: list[SOPElement] = field(default_factory=list)


@dataclass
class SOPDecision:
    """A decision point with two or more branches."""

    question: str
    branches: list[SOPBranch] = field(default_factory=list)


@dataclass
class SOPElement:
    """A single element in the SOP flow — either a step or a decision."""

    element_type: SOPElementType
    text: str
    step_number: Optional[int] = None
    decision: Optional[SOPDecision] = None


@dataclass
class SOPDocument:
    """Root container for a parsed SOP."""

    title: str
    elements: list[SOPElement] = field(default_factory=list)
