from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LEditSession:
    """Tiny in-process session for the interactive CLI."""

    history: list[dict[str, object]] = field(default_factory=list)

    def record(self, receipt: dict[str, object]) -> dict[str, object]:
        self.history.append(receipt)
        return receipt

    def last(self) -> dict[str, object] | None:
        return self.history[-1] if self.history else None
