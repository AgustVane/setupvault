from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TypeVar

from setupvault.core.exceptions import MergeError

T = TypeVar("T")


class MergeStrategy(Enum):
    """Strategies for resolving conflicts during merge/restore."""

    KEEP_NEWER = auto()
    """Keep the file with the newer modification time."""

    KEEP_OLDER = auto()
    """Keep the file with the older modification time."""

    KEEP_SOURCE = auto()
    """Keep the source version (from the snapshot)."""

    KEEP_DEST = auto()
    """Keep the destination version (currently on disk)."""

    INTERACTIVE = auto()
    """Prompt the user for each conflict."""


@dataclass(frozen=True)
class MergeResult:
    """The outcome of a merge operation for a single item."""

    item: str
    strategy_used: MergeStrategy
    applied: bool
    detail: str = ""


class ThreeWayMerger:
    """Generic three-way merge helper.

    Compares three versions of an item:
    - *base*: the original state (before any changes).
    - *source*: the new version (from snapshot or incoming).
    - *destination*: the current version on disk.

    The merger detects whether the source or destination has diverged
    from base and applies the selected strategy accordingly.
    """

    def __init__(self, strategy: MergeStrategy = MergeStrategy.KEEP_NEWER) -> None:
        self.strategy = strategy

    def merge(
        self,
        item_id: str,
        base: T | None,
        source: T | None,
        destination: T | None,
    ) -> MergeResult:
        """Resolve a single three-way merge.

        Args:
            item_id: Identifier for this item (used in error messages).
            base: The original common ancestor value.
            source: The incoming value (from the snapshot).
            destination: The current value on disk.

        Returns:
            A MergeResult indicating the action taken.
        """
        if source == destination:
            return MergeResult(item_id, self.strategy, True, "Unchanged")

        if base == destination:
            return MergeResult(
                item_id, self.strategy, True, "Applied source (destination unchanged from base)"
            )

        if base == source:
            return MergeResult(
                item_id, self.strategy, True, "Kept destination (source unchanged from base)"
            )

        if self.strategy == MergeStrategy.KEEP_NEWER:
            return MergeResult(
                item_id, self.strategy, True, "Would require mtime comparison (delegated)"
            )

        if self.strategy == MergeStrategy.KEEP_SOURCE:
            return MergeResult(item_id, self.strategy, True, "Applied source")

        if self.strategy == MergeStrategy.KEEP_DEST:
            return MergeResult(item_id, self.strategy, True, "Kept destination")

        if self.strategy == MergeStrategy.KEEP_OLDER:
            return MergeResult(
                item_id, self.strategy, True, "Would require mtime comparison (delegated)"
            )

        if self.strategy == MergeStrategy.INTERACTIVE:
            return MergeResult(item_id, self.strategy, False, "Awaiting user decision")

        raise MergeError(f"Unknown merge strategy: {self.strategy}")
