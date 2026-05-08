# Unit tests for parser
# tests/unit/test_blocklist_parser.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.vpn.blocklist_parser import parse_lines, _is_valid_domain


class TestBlocklistParser:
    def test_adguard_domain_extracted(self):
        lines = ["||ads.example.com^"]
        assert "ads.example.com" in list(parse_lines(iter(lines)))

    def test_adguard_with_options(self):
        lines = ["||tracker.com^$third-party,script"]
        assert "tracker.com" in list(parse_lines(iter(lines)))

    def test_exception_rule_skipped(self):
        lines = ["@@||safe.example.com^"]
        assert "safe.example.com" not in list(parse_lines(iter(lines)))

    def test_element_hiding_skipped(self):
        lines = ["example.com##.banner"]
        result = list(parse_lines(iter(lines)))
        assert not any("banner" in d for d in result)

    def test_comment_skipped(self):
        lines = ["! This is a comment", "# Also a comment"]
        assert list(parse_lines(iter(lines))) == []

    def test_url_pattern_skipped(self):
        lines = ["-ad-manager/", "&rb=uuid", "/banner.jpg"]
        assert list(parse_lines(iter(lines))) == []

    def test_valid_domain_check(self):
        assert _is_valid_domain("example.com") is True
        assert _is_valid_domain("sub.example.co.uk") is True
        assert _is_valid_domain("localhost") is False
        assert _is_valid_domain(".example.com") is False
        assert _is_valid_domain("") is False

    def test_hosts_format(self):
        lines = ["0.0.0.0 malware.com", "127.0.0.1 ads.bad.org"]
        result = list(parse_lines(iter(lines), "plain"))
        assert "malware.com" in result or "ads.bad.org" in result

    def test_adblock_header_skipped(self):
        lines = ["[Adblock Plus 2.0]", "||ads.com^"]
        result = list(parse_lines(iter(lines)))
        assert "ads.com" in result
        assert "[adblock plus 2.0]" not in result