#!/usr/bin/env python3
"""
Patches stat markers in README.md with live data from GitHub API.
Markers: <!-- STATS:key -->value<!-- /STATS:key -->
Commits only if content changed.
"""

import re
import subprocess
import sys
from datetime import datetime, timezone
import urllib.request
import json


def gh_api(path):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_commit_count(owner, repo):
    # Use contributor stats — sum all commits
    try:
        data = gh_api(f"/repos/{owner}/{repo}/contributors?per_page=100&anon=true")
        return str(sum(c.get("contributions", 0) for c in data))
    except Exception:
        return None


def get_latest_tag(owner, repo):
    try:
        data = gh_api(f"/repos/{owner}/{repo}/releases/latest")
        return data.get("tag_name")
    except Exception:
        try:
            data = gh_api(f"/repos/{owner}/{repo}/tags?per_page=1")
            return data[0]["name"] if data else None
        except Exception:
            return None


def get_last_workflow_run(owner, repo, workflow_file):
    try:
        data = gh_api(
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"
            f"?status=success&per_page=1"
        )
        runs = data.get("workflow_runs", [])
        if runs:
            dt = datetime.fromisoformat(
                runs[0]["updated_at"].replace("Z", "+00:00")
            )
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return None


def patch_marker(content, key, value):
    if value is None:
        return content
    pattern = rf"(<!-- STATS:{re.escape(key)} -->)(.*?)(<!-- /STATS:{re.escape(key)} -->)"
    replacement = rf"\g<1>{value}\g<3>"
    return re.sub(pattern, replacement, content, flags=re.DOTALL)


def main():
    readme_path = "README.md"
    owner = "kavyabarnadhya"

    with open(readme_path, "r", encoding="utf-8") as f:
        original = f.read()

    content = original

    # Dhamaka Blocks commit count
    commits = get_commit_count(owner, "dhamaka-blocks")
    if commits:
        content = patch_marker(content, "dhamaka-commits", f"{commits} commits")
        print(f"dhamaka-commits: {commits}")

    # Dhamaka Blocks latest version
    version = get_latest_tag(owner, "dhamaka-blocks")
    if version:
        content = patch_marker(content, "dhamaka-version", version)
        print(f"dhamaka-version: {version}")

    # UPSC Digest last run
    last_run = get_last_workflow_run(owner, "upsc-news-digest", "daily_digest.yml")
    if last_run:
        content = patch_marker(content, "upsc-last-run", last_run)
        print(f"upsc-last-run: {last_run}")

    if content == original:
        print("No changes — README already up to date.")
        sys.exit(0)

    with open(readme_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    print("README.md updated.")


if __name__ == "__main__":
    main()
