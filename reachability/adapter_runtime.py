"""Pinned, optional native dependencies. No automatic downloads at runtime."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class AdapterError(RuntimeError):
    pass


def lockfile() -> dict:
    return json.loads((ROOT / "adapters.lock.json").read_text())


def checked_run(args, *, timeout=30, **kwargs) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                                check=True, **kwargs)
    except (OSError, subprocess.SubprocessError) as exc:
        raise AdapterError(f"adapter process failed: {exc}") from exc
    if result.stderr.strip():
        raise AdapterError(f"adapter diagnostic: {result.stderr[:1000]}")
    return result.stdout


def verify_source(name: str, root: Path) -> Path:
    source = root / "upstream" / name
    pin = lockfile()["sources"][name]
    revision = checked_run(["git", "-C", str(source), "rev-parse", "HEAD"]).strip()
    if revision != pin["commit"]:
        raise AdapterError(f"{name} revision does not match adapters.lock.json")
    checked_run(["git", "-C", str(source), "diff", "--exit-code", "HEAD", "--"])
    for file, digest in pin.get("files", {}).items():
        if sha256((source / file).read_bytes()).hexdigest() != digest:
            raise AdapterError(f"{name}/{file} content differs from pin")
    return source


def verify_native_build(root: Path) -> None:
    try:
        receipt = json.loads((root / "adapter-build.json").read_text())
        if receipt["lock_sha256"] != sha256((ROOT / "adapters.lock.json").read_bytes()).hexdigest():
            raise AdapterError("native build uses a different dependency lock")
        if receipt["native_source_sha256"] != sha256((ROOT / "native/atomspace_batch.cc").read_bytes()).hexdigest():
            raise AdapterError("native helper changed; rebuild it")
        if "bin/atomspace_batch" not in receipt["files"]:
            raise AdapterError("native build receipt has no helper")
        for file, digest in receipt["files"].items():
            if sha256((root / file).read_bytes()).hexdigest() != digest:
                raise AdapterError(f"native artifact drift: {file}")
    except (OSError, KeyError, ValueError) as exc:
        raise AdapterError("missing/invalid adapter build; run scripts/build_adapters.py") from exc
