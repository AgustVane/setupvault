from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field

from setupvault.core.exceptions import FilterError


@dataclass(frozen=True)
class FilterRule:
    """A single include or exclude pattern.

    Patterns are glob-style (``fnmatch``) by default, or raw regex
    when ``is_regex=True``.
    """

    pattern: str
    is_regex: bool = False
    is_exclude: bool = True

    def __post_init__(self) -> None:
        if not self.pattern:
            raise FilterError("Filter pattern must not be empty.")

    def matches(self, value: str) -> bool:
        """Return True if *value* matches this rule."""
        if self.is_regex:
            return bool(re.search(self.pattern, value))
        return fnmatch.fnmatch(value, self.pattern)


@dataclass(frozen=True)
class Filter:
    """A collection of include/exclude rules for filtering data.

    Processing order:
        1. If any include rule matches, the value is **included**.
        2. If any exclude rule matches, the value is **excluded**.
        3. If no rules match at all, the value is **included** (default-include).

    This means exclude rules take precedence over include rules.
    """

    includes: tuple[FilterRule, ...] = ()
    excludes: tuple[FilterRule, ...] = ()

    def is_included(self, value: str) -> bool:
        """Determine whether *value* passes the filter."""
        matched_exclude = any(r.matches(value) for r in self.excludes)
        matched_include = any(r.matches(value) for r in self.includes)

        if matched_exclude:
            return False
        if matched_include:
            return True
        return True

    @classmethod
    def from_lists(
        cls,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> Filter:
        """Build a Filter from plain pattern strings."""
        return cls(
            includes=tuple(
                FilterRule(p, is_exclude=False) for p in (include_patterns or [])
            ),
            excludes=tuple(
                FilterRule(p, is_exclude=True) for p in (exclude_patterns or [])
            ),
        )
