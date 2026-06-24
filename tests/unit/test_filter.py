import pytest

from setupvault.core.exceptions import FilterError
from setupvault.core.filter import Filter, FilterRule


class TestFilterRule:
    def test_empty_pattern_raises(self) -> None:
        with pytest.raises(FilterError, match="must not be empty"):
            FilterRule("")

    def test_glob_matching(self) -> None:
        rule = FilterRule("*.json")
        assert rule.matches("snapshot.json")
        assert rule.matches("config.json")
        assert not rule.matches("readme.md")

    def test_regex_matching(self) -> None:
        rule = FilterRule(r"^firefox", is_regex=True)
        assert rule.matches("firefox-developer-edition")
        assert not rule.matches("firebird")


class TestFilter:
    def test_default_include(self) -> None:
        f = Filter()
        assert f.is_included("anything") is True

    def test_exclude_rule(self) -> None:
        f = Filter(excludes=(FilterRule("*.log"),))
        assert f.is_included("debug.log") is False
        assert f.is_included("config.json") is True

    def test_include_rule_without_exclude(self) -> None:
        f = Filter(includes=(FilterRule("*.json"),))
        assert f.is_included("data.json") is True
        assert f.is_included("data.yaml") is True

    def test_exclude_overrides_include(self) -> None:
        f = Filter(
            includes=(FilterRule("*.json"),),
            excludes=(FilterRule("secret.json"),),
        )
        assert f.is_included("data.json") is True
        assert f.is_included("secret.json") is False

    def test_from_lists_empty(self) -> None:
        f = Filter.from_lists()
        assert f.is_included("anything") is True

    def test_from_lists_with_patterns(self) -> None:
        f = Filter.from_lists(
            include_patterns=["*.py"],
            exclude_patterns=["test_*"],
        )
        assert f.is_included("main.py") is True
        assert f.is_included("test_main.py") is False
        assert f.is_included("readme.md") is True
