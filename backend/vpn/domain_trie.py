# Trie data structure for fast lookup
# backend/vpn/domain_trie.py
"""
Compressed domain trie for O(k) lookup where k = number of domain labels.
Memory efficient — shared prefix compression.
Thread-safe reads after build (no writes during runtime).
"""
from typing import Optional, Dict, Iterator
import threading


class TrieNode:
    __slots__ = ("children", "is_end", "wildcard")

    def __init__(self):
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end:   bool = False
        self.wildcard: bool = False   # matches any subdomain


class DomainTrie:
    """
    Stores domains in reverse label order for efficient subdomain matching.
    E.g., "ads.example.com" → ["com", "example", "ads"]

    Supports:
    - Exact match: "ads.example.com"
    - Wildcard: "*.example.com" blocks all subdomains
    - Suffix match: "example.com" blocks "x.example.com" if wildcard_root=True
    """

    def __init__(self, wildcard_root: bool = True):
        self._root = TrieNode()
        self._lock = threading.RLock()
        self._count = 0
        self._wildcard_root = wildcard_root  # block all subdomains of inserted domains

    def insert(self, domain: str) -> None:
        domain = domain.strip().lower()
        if not domain or domain.startswith("#"):
            return

        wildcard = domain.startswith("*.")
        if wildcard:
            domain = domain[2:]

        labels = domain.split(".")
        labels.reverse()  # TLD first for efficient traversal

        with self._lock:
            node = self._root
            for label in labels:
                if label not in node.children:
                    node.children[label] = TrieNode()
                node = node.children[label]
            node.is_end   = True
            node.wildcard = wildcard or self._wildcard_root
            self._count  += 1

    def contains(self, domain: str) -> bool:
        """Check if domain (or any parent domain) is in the trie."""
        domain = domain.strip().lower()
        if not domain:
            return False

        labels = domain.split(".")
        labels.reverse()

        node = self._root
        for i, label in enumerate(labels):
            if label not in node.children:
                return False
            node = node.children[label]
            # If we hit a wildcard/suffix node, everything below is blocked
            if node.is_end and node.wildcard:
                return True

        return node.is_end

    def bulk_insert(self, domains: Iterator[str]) -> int:
        """Insert many domains; returns count inserted."""
        before = self._count
        for d in domains:
            self.insert(d)
        return self._count - before

    def __len__(self) -> int:
        return self._count

    def __contains__(self, domain: str) -> bool:
        return self.contains(domain)

    def clear(self) -> None:
        with self._lock:
            self._root = TrieNode()
            self._count = 0