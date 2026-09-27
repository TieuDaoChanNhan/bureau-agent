"""Build/check/package the static site, then optionally upload to the existing Space.

python demo/publish.py --check   # offline checks and ZIP, no login needed
python demo/publish.py           # same checks, then upload using a local HF login
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from build import build, SITE, DEMO

FILES = (
    "README.md", "index.html", "style.css", "app.js", "fixtures.js", "offline.js",
    "session.js", "customer-ui.js", "tour.js", "vendor/driver.css",
    "vendor/driver.js.iife.js", "vendor/DRIVER_LICENSE",
    "vendor/fonts.css",
    "vendor/GEIST_OFL.txt", "vendor/GEIST_MONO_OFL.txt",
)


def prepare() -> dict[str, str]:
    build()
    hashes = {}
    for name in FILES:
        path = SITE / name
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?:sk-|jnk_|hf_)[A-Za-z0-9_-]{16,}", text):
            raise ValueError(f"Credential-like value in {name}; upload refused.")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    html = (SITE / "index.html").read_text(encoding="utf-8")
    if "connect-src 'none'" not in html:
        raise ValueError("The public demo must disallow external API connections.")
    for asset in re.findall(r'(?:src|href)="\./([^"]+)"', html):
        if asset not in FILES:
            raise ValueError(f"HTML references an unpublished asset: {asset}")
    if "sdk: static" not in (SITE / "README.md").read_text(encoding="utf-8"):
        raise ValueError("This deployment must stay on the Static SDK.")
    artifacts = DEMO / "artifacts"
    artifacts.mkdir(exist_ok=True)
    with zipfile.ZipFile(artifacts / "bureau-static.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(SITE / name, name)
    (artifacts / "manifest.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    print(f"Checked {len(FILES)} public assets. ZIP: demo/artifacts/bureau-static.zip")
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Build/check/package only; never contact Hugging Face")
    parser.add_argument("--repo-id", default="bachbeo2007/bureau")
    args = parser.parse_args()
    hashes = prepare()
    if args.check:
        return 0
    try:
        from huggingface_hub import HfApi, get_token
    except ImportError:
        print("Install the deployment CLI with: python -m pip install huggingface_hub", file=sys.stderr)
        return 2
    if not get_token():
        print("Upload pending: run hf auth login privately, then run this command again. Do not add any API keys to the Space.", file=sys.stderr)
        return 2
    api = HfApi()
    info = api.space_info(args.repo_id)
    if info.sdk != "static" or info.private:
        raise ValueError("Upload requires an existing PUBLIC STATIC Space; no hardware or visibility settings will be changed.")
    commit = api.upload_folder(repo_id=args.repo_id, repo_type="space", folder_path=str(SITE),
                              allow_patterns=list(FILES), commit_message="Publish isolated static customer demo")
    result = {"repo_id": args.repo_id, "commit": commit.oid, "files": hashes,
              "url": f"https://huggingface.co/spaces/{args.repo_id}"}
    (DEMO / "artifacts" / "deployment.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Uploaded revision {commit.oid}: {result['url']}")
    print("Run public browser verification before marking the task complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
