# Unit tests for trie
# tests/unit/test_domain_trie.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.vpn.domain_trie import DomainTrie


class TestDomainTrie:
    def setup_method(self):
        self.trie = DomainTrie(wildcard_root=True)
        for d in ["ads.example.com", "tracker.evil.org", "doubleclick.net"]:
            self.trie.insert(d)

    def test_exact_match(self):
        assert self.trie.contains("ads.example.com") is True

    def test_subdomain_blocked_wildcard_root(self):
        assert self.trie.contains("sub.ads.example.com") is True

    def test_unrelated_domain_not_blocked(self):
        assert self.trie.contains("google.com") is False

    def test_parent_domain_not_blocked(self):
        # Only ads.example.com is blocked, not example.com itself
        assert self.trie.contains("other.example.com") is False

    def test_len_accurate(self):
        assert len(self.trie) == 3

    def test_contains_operator(self):
        assert "doubleclick.net" in self.trie

    def test_clear(self):
        self.trie.clear()
        assert len(self.trie) == 0
        assert self.trie.contains("ads.example.com") is False

    def test_bulk_insert(self):
        trie   = DomainTrie()
        count  = trie.bulk_insert(iter(["a.com", "b.com", "c.com"]))
        assert count == 3
        assert len(trie) == 3

    def test_wildcard_insert(self):
        trie = DomainTrie(wildcard_root=False)
        trie.insert("*.example.com")
        assert trie.contains("sub.example.com") is True
        assert trie.contains("other.example.com") is True