"""Governed, provider-neutral AI teaching-support contracts.

The package contains only read-only contracts and injected provider orchestration.
It deliberately has no network client: application wiring must supply an approved
provider implementation explicitly.
"""

from .contracts import (
    GroundingBlockV1,
    GroundingFactV1,
    ProviderRequestV1,
    ProviderResponseV1,
)
from .grounding import GroundingViolation, validate_grounded_text
from .orchestrator import ProviderOrchestrator, ProviderTier
from .policy import PolicyViolation, validate_teaching_output

__all__ = [
    "GroundingBlockV1",
    "GroundingFactV1",
    "GroundingViolation",
    "PolicyViolation",
    "ProviderOrchestrator",
    "ProviderRequestV1",
    "ProviderResponseV1",
    "ProviderTier",
    "validate_grounded_text",
    "validate_teaching_output",
]
