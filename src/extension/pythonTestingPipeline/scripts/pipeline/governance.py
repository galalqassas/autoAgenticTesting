"""Ethical Governance Module - Transparency, Explainability, Accountability."""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Decision:
    """Agent decision record."""

    timestamp: str
    agent: str
    action: str
    rationale: str
    confidence: float
    inputs_used: dict


@dataclass
class Validation:
    """Validation check record."""

    timestamp: str
    validator: str
    target: str
    passed: bool
    reason: str


class GovernanceLog:
    """Logs agent decisions with governance metadata."""

    def __init__(self):
        self.decisions, self.validations = [], []
        self._start = time.time()

    def log_decision(
        self,
        agent: str,
        action: str,
        rationale: str,
        confidence: float = 0.8,
        inputs_used: dict = None,
    ) -> Decision:
        """Log decision with transparency metadata."""
        record = Decision(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            agent=agent,
            action=action,
            rationale=rationale,
            confidence=confidence,
            inputs_used=inputs_used or {},
        )
        self.decisions.append(record)
        return record

    def log_validation(
        self, validator: str, target: str, passed: bool, reason: str
    ) -> Validation:
        """Log validation result (accountability)."""
        record = Validation(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            validator=validator,
            target=target,
            passed=passed,
            reason=reason,
        )
        self.validations.append(record)
        return record

    def get_audit_trail(self) -> dict:
        """Get complete audit trail."""
        agents = list(set(d.agent for d in self.decisions))
        avg_conf = (
            sum(d.confidence for d in self.decisions) / len(self.decisions)
            if self.decisions
            else 0
        )
        failed = sum(1 for v in self.validations if not v.passed)

        return {
            "governance_version": "1.0",
            "pipeline_start": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(self._start)
            ),
            "decisions": [asdict(d) for d in self.decisions],
            "validations": [asdict(v) for v in self.validations],
            "summary": {
                "agents_involved": agents,
                "total_decisions": len(self.decisions),
                "average_confidence": round(avg_conf, 2),
                "failed_validations": failed,
                "status": "PASS" if failed == 0 else "REVIEW_NEEDED",
            },
        }

    def export_audit_trail(self, output_path: Path) -> Path:
        """Export audit trail to JSON."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.get_audit_trail(), f, indent=2)
        print(f"   📋 Governance audit: {output_path}")
        return output_path

    def reset(self):
        """Reset for new run."""
        self.decisions.clear()
        self.validations.clear()
        self._start = time.time()


# Global singleton
governance_log = GovernanceLog()
