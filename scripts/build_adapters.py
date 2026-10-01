"""Fetch exact revisions and build the optional native smoke-test dependencies.

Run from this checkout with Python 3.11. No sudo, global install, or branch updates.
The --debian-sysroot option stages hash-pinned Ubuntu 20.04 amd64 packages locally.
Other hosts can supply their own Guile development installation.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reachability.adapter_runtime import verify_source


def run(args, **kwargs):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--debian-sysroot", action="store_true")
    parser.add_argument("--jobs", type=int, default=4)
    options = parser.parse_args()
    if options.jobs < 1:
        parser.error("--jobs must be positive")
    root = options.root.resolve()
    lock = json.loads((ROOT / "adapters.lock.json").read_text())
    (root / "upstream").mkdir(parents=True, exist_ok=True)
    for name, pin in lock["sources"].items():
        source = root / "upstream" / name
        if not source.exists():
            run(["git", "init", source])
            run(["git", "-C", source, "remote", "add", "origin", pin["url"]])
            run(["git", "-C", source, "fetch", "--depth", "1", "origin", pin["commit"]])
            run(["git", "-C", source, "checkout", "--detach", pin["commit"]])
        verify_source(name, root)

    env = os.environ.copy()
    syslib = root / "sysroot/usr/lib/x86_64-linux-gnu"
    extra = []
    if options.debian_sysroot:
        packages = root / "debs"
        packages.mkdir(exist_ok=True)
        for package in lock["debian_sysroot"]:
            matches = [p for p in packages.glob("*.deb")
                       if sha256(p.read_bytes()).hexdigest() == package["sha256"]]
            if not matches:
                run(["apt-get", "download", f'{package["package"]}:{package["architecture"]}={package["version"]}'], cwd=packages)
                matches = [p for p in packages.glob("*.deb")
                           if sha256(p.read_bytes()).hexdigest() == package["sha256"]]
            if len(matches) != 1:
                raise RuntimeError("downloaded package does not match pinned SHA256")
            run(["dpkg-deb", "-x", matches[0], root / "sysroot"])
        env["PKG_CONFIG_PATH"] = str(syslib / "pkgconfig")
        env["PKG_CONFIG_SYSROOT_DIR"] = str(root / "sysroot")
        extra = [f"-DCMAKE_SHARED_LINKER_FLAGS=-L{syslib}", f"-DCMAKE_EXE_LINKER_FLAGS=-L{syslib}"]

    prefix = root / "install"
    common = ["-DCMAKE_C_COMPILER=gcc-11", "-DCMAKE_CXX_COMPILER=g++-11",
              f"-DCMAKE_INSTALL_PREFIX={prefix}", "-DCMAKE_BUILD_TYPE=Release"]
    cogbuild = root / "build/cogutil-gcc11"
    run(["cmake", "-S", root / "upstream/cogutil", "-B", cogbuild, *common], env=env)
    run(["cmake", "--build", cogbuild, "-j", options.jobs], env=env)
    # Upstream installs /etc/ld.so.conf.d even with a custom prefix. Stage the
    # entire install, then copy only the requested prefix; never write /etc.
    stage = root / "stage"
    run(["cmake", "--install", cogbuild], env={**env, "DESTDIR": str(stage)})
    shutil.copytree(stage / prefix.relative_to("/"), prefix, dirs_exist_ok=True)
    asbuild = root / "build/atomspace"
    run(["cmake", "-S", root / "upstream/atomspace", "-B", asbuild, *common,
         f"-DCMAKE_PREFIX_PATH={prefix}", "-DCMAKE_DISABLE_FIND_PACKAGE_Python3=TRUE", *extra], env=env)
    # Only the C++ library and its dependencies; Scheme/Python bindings are not used.
    run(["cmake", "--build", asbuild, "--target", "atomspace", "-j", options.jobs], env=env)
    libraries = sorted(asbuild.rglob("lib*.so")) + sorted((prefix / "lib/opencog").glob("lib*.so"))
    libdirs = sorted({str(p.parent) for p in libraries})
    if options.debian_sysroot:
        libdirs.append(str(syslib))
    binary = root / "bin/atomspace_batch"
    binary.parent.mkdir(exist_ok=True)
    includes = [root / "upstream/atomspace", asbuild, prefix / "include"]
    run(["g++-11", "-std=c++20", "-O2",
         f'-DATOMSPACE_PIN="{lock["sources"]["atomspace"]["commit"]}"',
         ROOT / "native/atomspace_batch.cc", "-o", binary,
         *("-I" + str(p) for p in includes), *("-L" + p for p in libdirs),
         "-Wl,-rpath," + ":".join(libdirs), "-Wl,--disable-new-dtags",
         "-latomspace", "-latombase", "-lvalue", "-latom_types", "-lcogutil", "-pthread"])
    # A local artifact receipt detects accidental binary/library drift. It is not
    # a signature against a malicious workspace owner or a bit-reproducible build.
    receipt = {"lock_sha256": sha256((ROOT / "adapters.lock.json").read_bytes()).hexdigest(),
               "native_source_sha256": sha256((ROOT / "native/atomspace_batch.cc").read_bytes()).hexdigest(),
               "files": {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
                         for p in [binary, *libraries]},
               "toolchain": {"gcc": subprocess.check_output(["g++-11", "-dumpfullversion"], text=True).strip(),
                             "cmake": subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0],
                             "swipl": subprocess.check_output(["swipl", "--version"], text=True).strip()}}
    (root / "adapter-build.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Built optional adapters. Run: uv run --no-project python -m unittest discover -s integration_tests -v")


if __name__ == "__main__":
    main()
