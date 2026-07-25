from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


def consolidated_patches(plan_path: Path) -> list[tuple[int, bytes, bytes]]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    patches: dict[int, tuple[bytes, bytes]] = {}
    for action in plan["actions"]:
        if action["action"] != "patch_memory":
            continue
        address = int(action["address"], 0)
        expected = bytes.fromhex(action["expected_hex"])
        replacement = bytes.fromhex(action["replacement_hex"])
        if address in patches:
            initial, current = patches[address]
            if current != expected:
                raise ValueError(
                    f"non-contiguous patch chain at 0x{address:08X}: "
                    f"{current.hex()} != {expected.hex()}"
                )
            patches[address] = (initial, replacement)
        else:
            patches[address] = (expected, replacement)
    return [
        (address, expected, replacement)
        for address, (expected, replacement) in sorted(patches.items())
        if expected != replacement
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source = args.source.resolve()
    plan = args.plan.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source) as source_archive:
        infos = source_archive.infolist()
        names = [info.filename for info in infos]
    if "eeMemory.bin" not in names:
        raise ValueError("savestate does not contain eeMemory.bin")

    temp_parent = output.parent / "transform-temp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_parent) as temporary:
        extracted = Path(temporary)
        with zipfile.ZipFile(source) as source_archive:
            for info in infos:
                name = info.filename
                try:
                    entry = source_archive.read(info)
                except (NotImplementedError, RuntimeError):
                    result = subprocess.run(
                        ["tar", "-xOf", str(source), name],
                        check=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    entry = result.stdout
                    if result.returncode != 0 and len(entry) != info.file_size:
                        detail = result.stderr.decode(errors="replace").strip()
                        raise RuntimeError(
                            f"could not extract {name}: {detail}"
                        )
                if len(entry) != info.file_size:
                    raise ValueError(
                        f"unexpected size for {name}: "
                        f"{len(entry)} != {info.file_size}"
                    )
                destination = extracted / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(entry)
        memory_path = extracted / "eeMemory.bin"
        memory = bytearray(memory_path.read_bytes())
        if len(memory) != 32 * 1024 * 1024:
            raise ValueError(f"unexpected EE memory size: {len(memory)}")

        applied = 0
        for address, expected, replacement in consolidated_patches(plan):
            live = bytes(memory[address : address + len(expected)])
            if live != expected:
                raise ValueError(
                    f"guard failed at 0x{address:08X}: "
                    f"{live.hex()} != {expected.hex()}"
                )
            if len(expected) != len(replacement):
                raise ValueError(f"size change at 0x{address:08X}")
            memory[address : address + len(expected)] = replacement
            applied += 1
        memory_path.write_bytes(memory)

        with zipfile.ZipFile(
            output,
            "x",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=1,
            allowZip64=True,
        ) as archive:
            for name in names:
                archive.write(extracted / name, arcname=name)

    with zipfile.ZipFile(output) as archive:
        output_names = archive.namelist()
        if output_names != names:
            raise ValueError("savestate entry order or inventory changed")
        patched_memory = archive.read("eeMemory.bin")
    for address, _, replacement in consolidated_patches(plan):
        if patched_memory[address : address + len(replacement)] != replacement:
            raise ValueError(f"output verification failed at 0x{address:08X}")

    print(f"patches={applied}")
    print(f"output={output}")
    print(f"size={output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
