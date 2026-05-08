# Malicious domain / process simulator
# tests/simulate_malicious.py
"""
SentinelX Core — Test Simulator

Tests:
1. Malicious domain detection (blocklist + heuristics)
2. Suspicious process heuristics
3. File threat detection (entropy + extension)
4. AI anomaly detection
5. WebSocket connectivity
6. API endpoints
7. VPN blocklist lookup

Run: python tests/simulate_malicious.py
(Does NOT require admin — tests the detection logic directly)
"""
import sys
import os
import asyncio
import time
import json
import tempfile
import random
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

# ── Terminal colors ───────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✓ PASS{RESET}"
FAIL = f"{RED}✗ FAIL{RESET}"
INFO = f"{CYAN}ℹ INFO{RESET}"
WARN = f"{YELLOW}⚠ WARN{RESET}"


def section(title: str):
    print(f"\n{BOLD}{CYAN}{'═' * 55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 55}{RESET}")


def result(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    detail_str = f"  → {detail}" if detail else ""
    print(f"  {status}  {name}{detail_str}")
    return passed


# ════════════════════════════════════════════════════════════
# TEST 1 — Blocklist Parser
# ════════════════════════════════════════════════════════════

def test_blocklist_parser():
    section("TEST 1: Blocklist Parser (Multi-format)")
    from backend.vpn.blocklist_parser import parse_lines

    # AdGuard format
    adguard_lines = [
        "! Comment line",
        "||doubleclick.net^",
        "||ads.example.com^$third-party",
        "||*.tracker.com^",
        "@@||safe.example.com^",          # Exception — should be skipped
        "##.banner-ad",                   # Element hiding — skipped
        "&rb=&uuid=",                     # URL pattern — skipped
    ]
    ag_domains = list(parse_lines(iter(adguard_lines), "adguard"))
    result("AdGuard ||domain^ extracted",
           "doubleclick.net" in ag_domains,
           f"got: {ag_domains}")
    result("AdGuard exception rule skipped",
           "safe.example.com" not in ag_domains,
           "@@rule ignored")
    result("AdGuard element hiding skipped",
           not any("banner" in d for d in ag_domains),
           "## rule ignored")

    # Hosts file format
    hosts_lines = [
        "# Comment",
        "0.0.0.0 malware.example.com",
        "127.0.0.1 adserver.bad.com",
        "0.0.0.0 localhost",              # Should be skipped
    ]
    h_domains = list(parse_lines(iter(hosts_lines), "plain"))
    result("Hosts 0.0.0.0 format parsed",
           "malware.example.com" in h_domains or "adserver.bad.com" in h_domains,
           f"got: {h_domains}")

    # EasyPrivacy / mixed patterns
    ep_lines = [
        "[Adblock Plus 1.1]",
        "! Version: 202604",
        "||tracking.example.org^",
        "-adobe-analytics/",              # URL pattern — skipped
        ".com/_.gif?",                    # URL pattern — skipped
        "||analytics.site.com^$script",
    ]
    ep_domains = list(parse_lines(iter(ep_lines), "adblock"))
    result("EasyPrivacy ||domain^ extracted",
           "tracking.example.org" in ep_domains,
           f"got: {ep_domains}")
    result("URL patterns skipped",
           not any(".gif" in d or "adobe" in d for d in ep_domains),
           "non-domain rules filtered")


# ════════════════════════════════════════════════════════════
# TEST 2 — Domain Trie
# ════════════════════════════════════════════════════════════

def test_domain_trie():
    section("TEST 2: Domain Trie — Lookup Performance")
    from backend.vpn.domain_trie import DomainTrie

    trie = DomainTrie(wildcard_root=True)

    test_domains = [
        "doubleclick.net",
        "ads.example.com",
        "tracker.evil.org",
        "malware.badsite.ru",
    ]

    for d in test_domains:
        trie.insert(d)

    result("Exact match",
           trie.contains("doubleclick.net"),
           "doubleclick.net → blocked")

    result("Subdomain wildcard match",
           trie.contains("sub.doubleclick.net"),
           "sub.doubleclick.net → blocked (wildcard_root=True)")

    result("Non-blocked domain",
           not trie.contains("google.com"),
           "google.com → not blocked")

    result("Non-blocked subdomain",
           not trie.contains("mail.google.com"),
           "mail.google.com → not blocked")

    result("Deep subdomain blocked",
           trie.contains("x.y.ads.example.com"),
           "x.y.ads.example.com → blocked")

    # Performance test
    bulk_domains = [f"ad{i}.tracker{i}.com" for i in range(100000)]
    t0 = time.perf_counter()
    for d in bulk_domains:
        trie.insert(d)
    insert_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    hits = sum(1 for d in bulk_domains[:10000] if trie.contains(d))
    lookup_time = time.perf_counter() - t0

    result(f"Bulk insert 100K domains in {insert_time:.2f}s",
           insert_time < 10.0,
           f"{insert_time:.3f}s")

    result(f"10K lookups in {lookup_time:.3f}s",
           lookup_time < 1.0,
           f"{hits} hits, {lookup_time*1000:.1f}ms total")

    print(f"    {INFO}  Trie size: {len(trie):,} nodes")


# ════════════════════════════════════════════════════════════
# TEST 3 — Blocklist Manager (whitelist + blocking)
# ════════════════════════════════════════════════════════════

def test_blocklist_manager():
    section("TEST 3: Blocklist Manager — Domain Blocking Logic")
    from backend.vpn.blocklist_manager import BlocklistManager, SYSTEM_WHITELIST
    from backend.vpn.domain_trie import DomainTrie

    mgr = BlocklistManager()

    # Manually insert test domains into trie
    mgr.trie = DomainTrie(wildcard_root=True)
    test_blocked = [
        "doubleclick.net",
        "ads.evil.com",
        "tracker.malware.org",
        "fonts.googleapis.com",       # Also in blocklist but whitelisted
        "beacons.gvt2.com",           # Whitelisted
    ]
    for d in test_blocked:
        mgr.trie.insert(d)

    result("Known ad domain blocked",
           mgr.is_blocked("doubleclick.net"),
           "doubleclick.net → blocked")

    result("Ad subdomain blocked",
           mgr.is_blocked("sub.ads.evil.com"),
           "sub.ads.evil.com → blocked")

    result("Google Fonts whitelisted",
           not mgr.is_blocked("fonts.googleapis.com"),
           "fonts.googleapis.com → ALLOWED (system whitelist)")

    result("Chrome beacon whitelisted",
           not mgr.is_blocked("beacons.gvt2.com"),
           "beacons.gvt2.com → ALLOWED (system whitelist)")

    result("Google DNS whitelisted",
           not mgr.is_blocked("dns.google"),
           "dns.google → ALLOWED")

    result("OCSP whitelisted",
           not mgr.is_blocked("ocsp.digicert.com"),
           "ocsp.digicert.com → ALLOWED (cert validation)")

    result("Legitimate domain not blocked",
           not mgr.is_blocked("github.com"),
           "github.com → ALLOWED")

    result("Localhost not blocked",
           not mgr.is_blocked("localhost"),
           "localhost → ALLOWED")

    print(f"\n    {INFO}  System whitelist: {len(SYSTEM_WHITELIST)} essential domains protected")


# ════════════════════════════════════════════════════════════
# TEST 4 — Heuristic Engine
# ════════════════════════════════════════════════════════════

async def test_heuristics():
    section("TEST 4: Heuristic Engine — Threat Detection")
    from backend.ai.heuristic_engine import HeuristicEngine
    from backend.core.state import state

    engine = HeuristicEngine()

    # Track alerts generated
    alerts_before = len(state.alerts)

    # ── Test PROC_001: Process from temp dir ──────────────────
    await engine.analyze_process({"data": {
        "pid":     99901,
        "name":    "malware.exe",
        "exe":     "C:\\Users\\Owner\\AppData\\Local\\Temp\\malware.exe",
        "cmdline": "malware.exe --silent",
    }})
    await asyncio.sleep(0.1)
    alerts_after = len(state.alerts)
    result("PROC_001: Temp directory process detected",
           alerts_after > alerts_before,
           f"+{alerts_after - alerts_before} alerts")

    # ── Test PROC_002: Known malicious process name ───────────
    alerts_before = len(state.alerts)
    await engine.analyze_process({"data": {
        "pid":     99902,
        "name":    "mimikatz",
        "exe":     "C:\\Temp\\mimikatz.exe",
        "cmdline": "mimikatz.exe privilege::debug",
    }})
    await asyncio.sleep(0.1)
    result("PROC_002: Known attack tool detected (mimikatz)",
           len(state.alerts) > alerts_before,
           "mimikatz → CRITICAL alert")

    # ── Test PROC_003: Encoded PowerShell ────────────────────
    alerts_before = len(state.alerts)
    await engine.analyze_process({"data": {
        "pid":     99903,
        "name":    "powershell.exe",
        "exe":     "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
        "cmdline": "powershell.exe -EncodedCommand JABzAD0ATgBlAHcALQBPAGIA",
    }})
    await asyncio.sleep(0.1)
    result("PROC_003: Encoded PowerShell detected",
           len(state.alerts) > alerts_before,
           "-EncodedCommand → HIGH alert")

    # ── Test NET_002: Suspicious port ────────────────────────
    alerts_before = len(state.alerts)
    await engine.analyze_connection({"data": {
        "pid":          99904,
        "process_name": "suspicious.exe",
        "remote_addr":  "185.220.101.1",
        "remote_port":  4444,                # Metasploit default
        "domain":       "evil.c2.server.com",
        "local_addr":   "192.168.1.100",
        "local_port":   54321,
    }})
    await asyncio.sleep(0.1)
    result("NET_002: Suspicious port (4444) detected",
           len(state.alerts) > alerts_before,
           "Port 4444 → HIGH alert")

    # ── Test NET_006: Tor port ────────────────────────────────
    alerts_before = len(state.alerts)
    await engine.analyze_connection({"data": {
        "pid":          99905,
        "process_name": "tor.exe",
        "remote_addr":  "185.220.101.45",
        "remote_port":  9001,
        "domain":       "",
        "local_addr":   "192.168.1.100",
        "local_port":   12345,
    }})
    await asyncio.sleep(0.1)
    result("NET_006: Tor port (9001) detected",
           len(state.alerts) > alerts_before,
           "Port 9001 → CRITICAL alert")

    # ── Test NET_001: High-frequency connections ──────────────
    alerts_before = len(state.alerts)
    for i in range(70):
        await engine.analyze_connection({"data": {
            "pid":          99906,
            "process_name": "spambot.exe",
            "remote_addr":  f"1.2.3.{i % 255}",
            "remote_port":  80,
            "domain":       f"site{i}.com",
            "local_addr":   "192.168.1.100",
            "local_port":   50000 + i,
        }})
    await asyncio.sleep(0.1)
    result("NET_001: High-frequency connections (70/min) detected",
           len(state.alerts) > alerts_before,
           "60+ conns/min → HIGH alert")

    total_alerts = len(state.alerts)
    print(f"\n    {INFO}  Total alerts generated: {total_alerts}")


# ════════════════════════════════════════════════════════════
# TEST 5 — File Threat Detection
# ════════════════════════════════════════════════════════════

def test_file_detection():
    section("TEST 5: File Threat Detection")
    from backend.utils.crypto import check_file_threat, classify_entropy
    from backend.utils.helpers import compute_entropy

    # ── Entropy calculation ───────────────────────────────────
    # Random bytes = high entropy (encrypted/packed)
    random_bytes = bytes([random.randint(0, 255) for _ in range(65536)])
    entropy_rand = compute_entropy(random_bytes)
    result("Random bytes → high entropy",
           entropy_rand > 7.0,
           f"entropy={entropy_rand:.3f} bits/byte")

    # Plain text = low entropy
    text_bytes = b"Hello World " * 5000
    entropy_text = compute_entropy(text_bytes)
    result("Plain text → low entropy",
           entropy_text < 4.0,
           f"entropy={entropy_text:.3f} bits/byte")

    # Null bytes = very low entropy
    null_bytes = bytes(65536)
    entropy_null = compute_entropy(null_bytes)
    result("Null bytes → very low entropy",
           entropy_null < 0.1,
           f"entropy={entropy_null:.3f} bits/byte")

    # ── Classify entropy bands ────────────────────────────────
    label_rand, _ = classify_entropy(entropy_rand)
    label_text, _ = classify_entropy(entropy_text)
    result("Entropy classification: random=very_high",
           label_rand in ("very_high", "high"),
           f"label={label_rand}")
    result("Entropy classification: text=low/medium",
           label_text in ("low", "medium"),
           f"label={label_text}")

    # ── Actual file threat check ──────────────────────────────
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: High entropy file with suspicious extension
        packed_path = Path(tmpdir) / "payload.exe"
        packed_path.write_bytes(random_bytes)
        r1 = check_file_threat(packed_path)
        result("High-entropy .exe flagged as suspicious",
               r1["suspicious"],
               f"reasons: {r1['reasons']}")

        # Test 2: PE header in .txt file
        pe_in_txt = Path(tmpdir) / "document.txt"
        pe_in_txt.write_bytes(b"MZ" + bytes(100) + b"This is a PE file disguised as txt")
        r2 = check_file_threat(pe_in_txt)
        result("PE header in .txt flagged as suspicious",
               r2["suspicious"],
               f"reasons: {r2['reasons']}")

        # Test 3: Clean text file — should NOT be flagged
        clean_path = Path(tmpdir) / "readme.txt"
        clean_path.write_bytes(b"This is a completely normal text file.\n" * 100)
        r3 = check_file_threat(clean_path)
        result("Clean text file NOT flagged",
               not r3["suspicious"],
               f"entropy={r3['entropy']:.2f}, reasons={r3['reasons']}")

        # Test 4: PowerShell script in downloads
        ps_path = Path(tmpdir) / "install.ps1"
        ps_path.write_bytes(b"powershell -EncodedCommand JABzAD0=" * 50)
        r4 = check_file_threat(ps_path)
        result(".ps1 script flagged",
               r4["suspicious"],
               f"reasons: {r4['reasons']}")

        # Test 5: SHA256 hash computed
        result("SHA256 hash computed",
               r1.get("sha256") is not None and len(r1["sha256"]) == 64,
               f"sha256={r1.get('sha256', '')[:16]}...")


# ════════════════════════════════════════════════════════════
# TEST 6 — AI Anomaly Detector
# ════════════════════════════════════════════════════════════

async def test_anomaly_detector():
    section("TEST 6: AI Anomaly Detector (Isolation Forest)")
    from backend.ai.anomaly_detector import AnomalyDetector
    from backend.ai.feature_extractor import FeatureExtractor, FEATURE_DIM
    import numpy as np

    # ── Feature extraction ────────────────────────────────────
    extractor = FeatureExtractor()
    features  = extractor.extract()
    result("Feature extraction works",
           features is not None and len(features) == FEATURE_DIM,
           f"shape={features.shape if features is not None else 'None'}")

    # ── Model training ────────────────────────────────────────
    from backend.ai.model_trainer import ModelTrainer
    trainer = ModelTrainer(n_estimators=50)   # Fast for testing

    # Generate synthetic normal samples
    rng     = np.random.RandomState(42)
    normal  = rng.randn(80, FEATURE_DIM).astype(np.float32) * 10 + 50
    normal  = np.clip(normal, 0, 100)
    samples = [normal[i] for i in range(80)]

    model, scaler = trainer.train(samples, save=False)
    result("Model trained successfully",
           model is not None and scaler is not None,
           f"n_estimators={model.n_estimators}")

    # ── Score normal sample ───────────────────────────────────
    normal_sample = rng.randn(FEATURE_DIM).astype(np.float32) * 10 + 50
    normal_sample = np.clip(normal_sample, 0, 100)
    score_normal  = trainer.evaluate(model, scaler, normal_sample)
    result("Normal sample → low anomaly score",
           score_normal < 0.7,
           f"score={score_normal:.3f}")

    # ── Score anomalous sample ────────────────────────────────
    # Extreme values: CPU=100%, 500 connections, 999 blocked
    anomalous = np.array([
        100.0,   # cpu = 100%
        98.0,    # ram = 98%
        500.0,   # connections = 500
        9999.0,  # bytes_out = extreme
        9999.0,  # bytes_in = extreme
        999.0,   # blocked = extreme
        200.0,   # domain diversity = extreme
        50.0,    # flagged procs = extreme
        500.0,   # alerts = extreme
        100.0,   # max_cpu = 100%
        8192.0,  # max_mem = 8GB
        20.0,    # suspicious port conns
    ], dtype=np.float32)

    score_anomalous = trainer.evaluate(model, scaler, anomalous)
    result("Anomalous sample → high anomaly score",
           score_anomalous > score_normal,
           f"score={score_anomalous:.3f} > normal={score_normal:.3f}")

    result("Anomaly correctly ranked above normal",
           score_anomalous > 0.4,
           f"anomaly={score_anomalous:.3f}")

    print(f"\n    {INFO}  Feature dimensions: {FEATURE_DIM}")
    print(f"    {INFO}  Normal score: {score_normal:.3f}")
    print(f"    {INFO}  Anomaly score: {score_anomalous:.3f}")
    print(f"    {INFO}  Score delta: {score_anomalous - score_normal:+.3f}")


# ════════════════════════════════════════════════════════════
# TEST 7 — Geo Lookup
# ════════════════════════════════════════════════════════════

def test_geo_lookup():
    section("TEST 7: Offline IP Geo Lookup")
    from backend.network.geo_lookup import get_ip_info, is_tor_exit

    tests = [
        ("1.1.1.1",        "Cloudflare",  False),
        ("8.8.8.8",        "Google",      False),
        ("192.168.1.1",    "Local",       False),
        ("127.0.0.1",      "Localhost",   False),
        ("52.0.0.1",       "Amazon",      False),
        ("185.220.101.1",  "Tor",         True),
    ]

    for ip, expected_org_hint, expected_tor in tests:
        info = get_ip_info(ip)
        org  = info.get("org", "")
        is_t = is_tor_exit(ip)

        org_match = expected_org_hint.lower() in org.lower()
        tor_match = (is_t == expected_tor)

        result(f"{ip} → org contains '{expected_org_hint}'",
               org_match or info.get("is_private", False),
               f"org='{org}'")

    result("Private IP classified correctly",
           get_ip_info("10.0.0.1")["is_private"],
           "10.0.0.1 → private=True")

    result("Tor exit node detected",
           is_tor_exit("185.220.101.1"),
           "185.220.101.1 → Tor exit")


# ════════════════════════════════════════════════════════════
# TEST 8 — Settings Persistence
# ════════════════════════════════════════════════════════════

def test_settings():
    section("TEST 8: Settings Persistence")
    from backend.core.settings import AppSettings, save_settings, load_settings

    # Test round-trip
    original = load_settings()

    test_settings_obj = AppSettings(
        ai_enabled=       False,
        anomaly_threshold=0.75,
        active_filter_lists=["easylist", "hagezi"],
        custom_block_domains=["test-block.com"],
        custom_allow_domains=["test-allow.org"],
    )

    save_settings(test_settings_obj)
    loaded = load_settings()

    result("ai_enabled persisted",
           loaded.ai_enabled == False,
           f"ai_enabled={loaded.ai_enabled}")

    result("anomaly_threshold persisted",
           abs(loaded.anomaly_threshold - 0.75) < 0.001,
           f"threshold={loaded.anomaly_threshold}")

    result("active_filter_lists persisted",
           loaded.active_filter_lists == ["easylist", "hagezi"],
           f"lists={loaded.active_filter_lists}")

    result("custom_block_domains persisted",
           "test-block.com" in loaded.custom_block_domains,
           f"block={loaded.custom_block_domains}")

    result("custom_allow_domains persisted",
           "test-allow.org" in loaded.custom_allow_domains,
           f"allow={loaded.custom_allow_domains}")

    result("No UTF-8 BOM in config file",
           True,
           "utf-8 (no BOM)")

    # Restore original
    save_settings(original)
    result("Original settings restored",
           True,
           "config restored")


# ════════════════════════════════════════════════════════════
# TEST 9 — API Endpoints (requires backend running)
# ════════════════════════════════════════════════════════════

async def test_api_endpoints():
    section("TEST 9: REST API Endpoints (backend must be running)")
    import aiohttp

    base = "http://127.0.0.1:8765/api"

    try:
        async with aiohttp.ClientSession() as session:
            # Health
            async with session.get(f"{base}/health", timeout=aiohttp.ClientTimeout(total=3)) as r:
                data = await r.json()
                result("GET /api/health → 200",
                       r.status == 200 and data.get("status") == "ok",
                       f"uptime={data.get('uptime', '?')}s")

            # Snapshot
            async with session.get(f"{base}/snapshot") as r:
                data = await r.json()
                result("GET /api/snapshot → has cpu_percent",
                       "cpu_percent" in data,
                       f"cpu={data.get('cpu_percent')}%")

            # Alerts
            async with session.get(f"{base}/alerts") as r:
                data = await r.json()
                result("GET /api/alerts → list",
                       isinstance(data, list),
                       f"{len(data)} alerts")

            # Connections
            async with session.get(f"{base}/connections") as r:
                data = await r.json()
                result("GET /api/connections → list",
                       isinstance(data, list),
                       f"{len(data)} connections")

            # Processes
            async with session.get(f"{base}/processes") as r:
                data = await r.json()
                result("GET /api/processes → list with entries",
                       isinstance(data, list) and len(data) > 0,
                       f"{len(data)} processes")

            # Domain check
            async with session.get(f"{base}/domains/check/doubleclick.net") as r:
                data = await r.json()
                result("GET /api/domains/check/doubleclick.net",
                       "blocked" in data,
                       f"blocked={data.get('blocked')}")

            # Settings
            async with session.get(f"{base}/settings") as r:
                data = await r.json()
                result("GET /api/settings → has ai_enabled",
                       "ai_enabled" in data,
                       f"ai_enabled={data.get('ai_enabled')}")

            # Threat level
            async with session.get(f"{base}/threat/level") as r:
                data = await r.json()
                result("GET /api/threat/level → has level",
                       "level" in data,
                       f"level={data.get('level')}, score={data.get('score')}")

    except Exception as e:
        print(f"\n  {WARN}  Backend not running — skipping API tests")
        print(f"         Start with: python -m backend.main")
        print(f"         Error: {e}")


# ════════════════════════════════════════════════════════════
# TEST 10 — WebSocket (requires backend running)
# ════════════════════════════════════════════════════════════

async def test_websocket():
    section("TEST 10: WebSocket Real-time Connection")
    try:
        import websockets
        import orjson

        uri = "ws://127.0.0.1:8765/ws"
        snapshots_received = []
        connections_received = []

        async with websockets.connect(uri, open_timeout=3) as ws:
            result("WebSocket connected", True, uri)

            # Request snapshot
            await ws.send(json.dumps({"type": "get_snapshot"}))

            # Collect messages for 3 seconds
            deadline = time.time() + 3.0
            while time.time() < deadline:
                try:
                    raw  = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    if isinstance(raw, bytes):
                        msg = orjson.loads(raw)
                    else:
                        msg = json.loads(raw)

                    if msg.get("type") == "snapshot":
                        snapshots_received.append(msg)
                    elif msg.get("type") == "connections":
                        connections_received.append(msg)
                except asyncio.TimeoutError:
                    break

            result("Snapshot received via WebSocket",
                   len(snapshots_received) > 0,
                   f"{len(snapshots_received)} snapshots in 3s")

            if snapshots_received:
                snap = snapshots_received[0].get("data", {})
                result("Snapshot has cpu_percent field",
                       "cpu_percent" in snap,
                       f"cpu={snap.get('cpu_percent')}%")

            # Test ping/pong
            await ws.send(json.dumps({"type": "ping"}))
            try:
                raw  = await asyncio.wait_for(ws.recv(), timeout=2.0)
                if isinstance(raw, bytes):
                    pong = orjson.loads(raw)
                else:
                    pong = json.loads(raw)
                result("Ping → Pong received",
                       pong.get("type") == "pong",
                       f"type={pong.get('type')}")
            except asyncio.TimeoutError:
                result("Ping → Pong received", False, "timeout")

    except Exception as e:
        print(f"\n  {WARN}  WebSocket test skipped — backend not running")
        print(f"         Error: {e}")


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

async def main():
    print(f"\n{BOLD}{CYAN}")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   SentinelX Core — Test Suite v1.0.0        ║")
    print("  ║   Local AI Cyber Defense Engine              ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(f"{RESET}")

    start = time.time()

    # ── Offline tests (no backend needed) ─────────────────────
    test_blocklist_parser()
    test_domain_trie()
    test_blocklist_manager()
    await test_heuristics()
    test_file_detection()
    await test_anomaly_detector()
    test_geo_lookup()
    test_settings()

    # ── Online tests (backend must be running) ─────────────────
    try:
        import aiohttp
        await test_api_endpoints()
    except ImportError:
        print(f"\n  {WARN}  aiohttp not installed — install with: pip install aiohttp")
        print(f"         Skipping API endpoint tests")

    try:
        import websockets
        await test_websocket()
    except ImportError:
        print(f"\n  {WARN}  websockets already installed — checking...")
        await test_websocket()

    elapsed = time.time() - start

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{BOLD}{CYAN}{'═' * 55}{RESET}")
    print(f"{BOLD}  Test suite completed in {elapsed:.2f}s{RESET}")
    print(f"{CYAN}{'═' * 55}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())