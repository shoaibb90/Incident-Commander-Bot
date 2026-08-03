"""
Rule-based detection engine.
Scans pasted log text for common attack signatures and returns findings.
This is intentionally simple/regex-based (no ML) so it's transparent,
explainable, and easy to extend with new rules over time.
"""
import re
from collections import Counter

RULES = [
    {
        "name": "Brute Force Login Attempt",
        "category": "authentication",
        "severity": "high",
        "pattern": re.compile(r"failed password|authentication failure|invalid user", re.I),
        "threshold": 5,  # number of matching lines to trigger
    },
    {
        "name": "Port Scan Indicator",
        "category": "network",
        "severity": "medium",
        "pattern": re.compile(r"SYN_SCAN|nmap|port\s?scan|connection refused", re.I),
        "threshold": 3,
    },
    {
        "name": "SQL Injection Attempt",
        "category": "web",
        "severity": "critical",
        "pattern": re.compile(r"(\bUNION\b.*\bSELECT\b)|(\bOR\b\s+1=1)|(--\s*$)|(DROP\s+TABLE)", re.I),
        "threshold": 1,
    },
    {
        "name": "Suspicious Download-and-Execute",
        "category": "endpoint",
        "severity": "critical",
        "pattern": re.compile(r"(curl|wget).{0,40}(\|\s*sh|\|\s*bash)", re.I),
        "threshold": 1,
    },
    {
        "name": "Base64-Encoded Payload",
        "category": "endpoint",
        "severity": "medium",
        "pattern": re.compile(r"base64\s+-d|FromBase64String", re.I),
        "threshold": 1,
    },
    {
        "name": "Privilege Escalation Attempt",
        "category": "endpoint",
        "severity": "high",
        "pattern": re.compile(r"sudo su|chmod\s+777|/etc/passwd|setuid", re.I),
        "threshold": 1,
    },
    {
        "name": "Suspicious User-Agent / Scanner Tool",
        "category": "web",
        "severity": "low",
        "pattern": re.compile(r"sqlmap|nikto|gobuster|dirbuster|hydra", re.I),
        "threshold": 1,
    },
]


def analyze_logs(log_text: str):
    """Returns a list of finding dicts: name, category, severity, match_count, sample_lines"""
    lines = [l for l in log_text.splitlines() if l.strip()]
    findings = []

    for rule in RULES:
        matched_lines = [l for l in lines if rule["pattern"].search(l)]
        if len(matched_lines) >= rule["threshold"]:
            findings.append({
                "name": rule["name"],
                "category": rule["category"],
                "severity": rule["severity"],
                "match_count": len(matched_lines),
                "sample_lines": matched_lines[:3],
            })

    # Extra heuristic: many failed-login lines from the same IP
    ip_pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
    fail_lines = [l for l in lines if re.search(r"failed password|auth fail", l, re.I)]
    ip_counts = Counter(m.group(1) for l in fail_lines for m in [ip_pattern.search(l)] if m)
    hot_ips = [ip for ip, n in ip_counts.items() if n >= 5]
    if hot_ips:
        findings.append({
            "name": "Repeated Failed Logins From Single Source IP",
            "category": "authentication",
            "severity": "high",
            "match_count": sum(ip_counts[ip] for ip in hot_ips),
            "sample_lines": [f"Source IP {ip}: {ip_counts[ip]} failed attempts" for ip in hot_ips[:3]],
        })

    return {
        "total_lines_scanned": len(lines),
        "findings": findings,
    }
