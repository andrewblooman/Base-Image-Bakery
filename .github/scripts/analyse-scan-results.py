#!/usr/bin/env python3
"""
Analyse Grype vulnerability scan results using the Anthropic Claude API.

Usage:
    python3 analyse-scan-results.py <scan-results-dir>

Environment variables:
    ANTHROPIC_API_KEY  Required. Anthropic API key used to call Claude.

The script reads every grype-results-*.json file from <scan-results-dir>,
extracts a concise vulnerability summary, and sends it to Claude for analysis.
The Markdown-formatted response is printed to stdout, which the GitHub Actions
workflow appends to $GITHUB_STEP_SUMMARY.
"""

import glob
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def load_scan_results(results_dir: str) -> list:
    """Load all Grype JSON scan results from *results_dir*."""
    results = []
    pattern = os.path.join(results_dir, "grype-results-*.json")
    for filepath in sorted(glob.glob(pattern)):
        image_name = (
            os.path.basename(filepath)
            .removeprefix("grype-results-")
            .removesuffix(".json")
        )
        try:
            with open(filepath, encoding="utf-8") as fh:
                data = json.load(fh)
            results.append({"image": image_name, "data": data})
            print(f"Loaded scan results for: {image_name}", file=sys.stderr)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"Warning: could not load {filepath}: {exc}", file=sys.stderr)
    return results


def build_prompt(results: list) -> str:
    """Construct the Claude prompt from the list of scan result dicts."""
    summaries = []
    for item in results:
        image = item["image"]
        matches = item["data"].get("matches", [])

        severity_counts: dict = {}
        critical_and_high: list = []

        for match in matches:
            vuln = match.get("vulnerability", {})
            severity = vuln.get("severity", "Unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            if severity in ("Critical", "High"):
                artifact = match.get("artifact", {})
                critical_and_high.append(
                    {
                        "id": vuln.get("id", ""),
                        "severity": severity,
                        "description": (vuln.get("description") or "")[:300],
                        "fix_versions": vuln.get("fix", {}).get("versions", []),
                        "package": artifact.get("name", ""),
                        "installed_version": artifact.get("version", ""),
                    }
                )

        summaries.append(
            {
                "image": image,
                "total_vulnerabilities": len(matches),
                "by_severity": severity_counts,
                # Cap at 20 to keep the prompt a reasonable size
                "critical_and_high": critical_and_high[:20],
            }
        )

    scan_json = json.dumps(summaries, indent=2)

    return f"""You are a container security expert. Analyse the following Grype \
vulnerability scan results for container base images and produce a concise security report.

Please structure your response with these sections:
1. **Executive Summary** – overall security posture across all images in 2–3 sentences.
2. **Vulnerability Breakdown by Image** – a Markdown table with columns \
Image | Critical | High | Medium | Low | Negligible | Total.
3. **Critical & High Priority Findings** – for each Critical/High CVE list: \
CVE ID, affected package, installed version, fix version(s), and a one-line description.
4. **Remediation Recommendations** – specific, actionable steps ordered by priority.
5. **Risk Assessment** – overall risk rating (Critical / High / Medium / Low) with justification.

Scan results (JSON):
{scan_json}

Format the entire response in Markdown.
"""


def call_claude(prompt: str, api_key: str) -> str:
    """Send *prompt* to the Anthropic Messages API and return the text response."""
    body = json.dumps(
        {
            "model": "claude-opus-4-5",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read())
            return payload["content"][0]["text"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Anthropic API returned HTTP {exc.code}: {exc.read().decode()}"
        ) from exc


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python3 analyse-scan-results.py <scan-results-dir>",
            file=sys.stderr,
        )
        sys.exit(1)

    results_dir = sys.argv[1]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    results = load_scan_results(results_dir)
    if not results:
        print("## 🔍 Vulnerability Scan Analysis")
        print("\n> No scan result files were found — skipping analysis.")
        return

    prompt = build_prompt(results)

    print("Calling Claude API for vulnerability analysis…", file=sys.stderr)
    analysis = call_claude(prompt, api_key)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("## 🔍 Vulnerability Scan Analysis")
    print(f"\n_Generated on {timestamp} by Claude (claude-opus-4-5)_\n")
    print("---")
    print(analysis)
    print("\n---")
    print("\n### 📦 Scan Artefacts")
    print(
        "Full Grype JSON reports and SPDX SBOMs are available as workflow artefacts "
        "and are retained for 90 days."
    )


if __name__ == "__main__":
    main()
