#!/usr/bin/env python3
import re
import subprocess
import struct
import time
import os

CRC = os.environ.get("NA2_INJECTION_CRC", "").upper()
if not re.fullmatch(r"[0-9A-F]{8}", CRC):
    raise RuntimeError("NA2_INJECTION_CRC must be exactly eight hexadecimal digits")
PNACH_FILE = f"build/{CRC}.pnach"
ELF = "data/FILES/SLOP_NA2.28"
INJECTION_BASE = int(os.environ.get("NA2_INJECTION_BASE", "0"), 0)
INJECTION_END = int(os.environ.get("NA2_INJECTION_END", "0"), 0)
CODE_BASE = int(os.environ.get("NA2_INJECTION_CODE_BASE", "0"), 0)
CODE_END = int(os.environ.get("NA2_INJECTION_CODE_END", "0"), 0)
BUILD_ID = int(os.environ.get("NA2_INJECTION_BUILD_ID", "0"), 0)
if not 0 < INJECTION_BASE < INJECTION_END <= 0x02000000:
    raise RuntimeError("Invalid NA2 development injection reservation")
if not INJECTION_BASE < CODE_BASE < CODE_END <= INJECTION_END:
    raise RuntimeError("Invalid NA2 development injection code bank")
if not 0 < BUILD_ID <= 0xFFFFFFFF:
    raise RuntimeError("NA2_INJECTION_BUILD_ID must be a nonzero 32-bit value")
PS2DEV = os.path.abspath("msys/1.0/local/ps2dev/ee/bin")
PS2SDK = os.path.abspath("msys/1.0/local/ps2dev/ps2sdk/bin")
OBJ_DIR = "obj"
BUILD_DIR = "build"

HEADER_FILE = "src/Main.h"

os.environ["PATH"] = f"{PS2DEV}{os.pathsep}{PS2SDK}{os.pathsep}" + os.environ["PATH"]

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, env=os.environ).returncode

def obj_bss_size(obj):
    out = run(f"ee-objdump -h {obj}")
    for line in out.splitlines():
        m = re.match(r'^\s*\d+\s+\.bss\s+([0-9a-f]+)', line)
        if m:
            return int(m.group(1), 16)
    return 0

def strip_comment(s):
    idx = s.find(';')
    return s[:idx] if idx != -1 else s

def make_resolve_tokens(labels):
    def resolve_tokens(token_str):
        token_str = strip_comment(token_str)
        tokens = [t.strip() for t in token_str.split(',') if t.strip()]
        resolved = []
        for token in tokens:
            if token.startswith(("0x", "0X")):
                resolved.append(int(token, 0))
            elif token in labels:
                resolved.append(labels[token])
            else:
                raise RuntimeError(f"Linker label '{token}' was not found for .org")
        return resolved
    return resolve_tokens

HEADER_EXTERN_RE = re.compile(
    r'^extern\s+.+?\b([A-Za-z_]\w*)\s*\([^;]*\)\s*;\s*//\s*(0x[0-9A-Fa-f]+)'
)

HEADER_EXTERN_PTR_ARRAY_RE = re.compile(
    r'^extern\s+\w+\s*\(\*([A-Za-z_]\w*)\s*\([^;]*\)\)\s*\[\d+\]\s*;\s*//\s*(0x[0-9A-Fa-f]+)'
)


def parse_header_symbols(header_path):
    """Read the generated header and return {function_name: integer_address}.

    Addresses are extracted from the ``// 0xADDRESS`` comment beside each
    extern declaration, avoiding a manually maintained .definelabel for every
    existing game function.
    """
    symbols = {}
    if not os.path.exists(header_path):
        print(f"  WARNING: header '{header_path}' was not found; "
              f"no symbols will be loaded from it")
        return symbols

    with open(header_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith("extern"):
                continue

            m = HEADER_EXTERN_PTR_ARRAY_RE.match(stripped)
            if not m:
                m = HEADER_EXTERN_RE.match(stripped)
            if not m:
                continue

            name, addr_str = m.group(1), m.group(2)
            addr = int(addr_str, 16)

            if name in symbols and symbols[name] != addr:
                print(f"  WARNING: '{name}' appears twice in the header with "
                      f"different addresses ({hex(symbols[name])} and {hex(addr)}); "
                      f"keeping the first")
                continue

            symbols[name] = addr

    return symbols


def parse_asm(filename, initial_labels=None):
    labels = dict(initial_labels) if initial_labels else {}
    importobjs = []
    word_orgs = []
    asm_blocks = []
    current_org = None
    current_org_type = None
    current_instr_count = 0

    resolve_tokens = make_resolve_tokens(labels)

    def flush_asm():
        nonlocal current_org_type, current_instr_count
        if current_org_type == "asm" and current_instr_count > 0 and current_org is not None:
            addrs = current_org if isinstance(current_org, list) else [current_org]
            for a in addrs:
                if a is not None:
                    asm_blocks.append((a, current_instr_count))
        current_org_type = None
        current_instr_count = 0

    with open(filename, "r") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()

        m = re.match(r'^\.definelabel\s+(\w+),\s*(0x[0-9a-fA-F]+|\d+)', stripped)
        if m:
            labels[m.group(1)] = int(m.group(2), 0)
            continue

        m = re.match(r'^(\w+)\s+equ\s+(0x[0-9a-fA-F]+|\d+)', stripped)
        if m:
            labels[m.group(1)] = int(m.group(2), 0)
            continue

        m = re.match(r'^\.org\s+(.+)$', stripped)
        if m:
            flush_asm()
            resolved = resolve_tokens(m.group(1))
            current_org = resolved[0] if len(resolved) == 1 else resolved
            continue

        m = re.match(r'^\s*\.importobj\s+"\.\/(.+?)\.o"', stripped)
        if m:
            current_org_type = "importobj"
            addr = current_org[0] if isinstance(current_org, list) else current_org
            importobjs.append((addr, m.group(1)))
            continue

        m = re.match(r'^\s*\.word\s+(\S+)', stripped)
        if m and current_org is not None:
            current_org_type = "word"
            token = m.group(1)
            addrs = current_org if isinstance(current_org, list) else [current_org]
            for a in addrs:
                if a is None:
                    continue
                if token.startswith(("0x", "0X")):
                    word_orgs.append((a, token, "literal"))
                else:
                    word_orgs.append((a, token, "symbol"))
            if isinstance(current_org, list):
                current_org = [a + 4 if a is not None else None for a in current_org]
            else:
                current_org += 4
            continue

        if current_org is not None and stripped and \
           not stripped.startswith(";") and \
           not stripped.startswith(".") and \
           stripped != ".Close":
            current_org_type = "asm"
            current_instr_count += 1
            continue

        if stripped == ".Close":
            flush_asm()

    return labels, importobjs, word_orgs, asm_blocks

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=os.environ)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"Command failed ({result.returncode}): {cmd}{suffix}")
    return result.stdout

def obj_size(obj):
    out = run(f"ee-objdump -h {obj}")
    for line in out.splitlines():
        m = re.match(r'^\s*\d+\s+\.text\s+([0-9a-f]+)', line)
        if m:
            return int(m.group(1), 16)
    return 0

def obj_rodata_size(obj):
    out = run(f"ee-objdump -h {obj}")
    for line in out.splitlines():
        m = re.match(r'^\s*\d+\s+\.rodata\s+([0-9a-f]+)', line)
        if m:
            return int(m.group(1), 16)
    return 0

def objdump_data(obj):
    out = run(f"ee-objdump -s {obj}")
    collecting = False
    result = ""
    for line in out.splitlines():
        if "Contents of section .data" in line:
            collecting = True
            continue
        if collecting:
            if re.match(r'^ [0-9a-f]+', line):
                hex_part = line.strip().split("  ")[0].split(" ", 1)[1].replace(" ", "")
                result += hex_part
            elif "Contents of section" in line:
                break
    return result

def objdump_rodata(obj):
    out = run(f"ee-objdump -s {obj}")
    collecting = False
    result = ""
    for line in out.splitlines():
        if "Contents of section .rodata" in line:
            collecting = True
            continue
        if collecting:
            if re.match(r'^ [0-9a-f]+', line):
                hex_part = line.strip().split("  ")[0].split(" ", 1)[1].replace(" ", "")
                result += hex_part
            elif "Contents of section" in line:
                break
    return result

def objdump_text(obj):
    out = run(f"ee-objdump -s {obj}")
    collecting = False
    result = ""
    for line in out.splitlines():
        if "Contents of section .text" in line:
            collecting = True
            continue
        if collecting:
            if re.match(r'^ [0-9a-f]+', line):
                hex_part = line.strip().split("  ")[0].split(" ", 1)[1].replace(" ", "")
                result += hex_part
            elif "Contents of section" in line:
                break
    return result

def read_textblock_patches(first_addr, addr, size):
    fname = f"{BUILD_DIR}/textblocks.bin"
    if not os.path.exists(fname):
        print(f"  WARNING: {fname} was not found")
        return []

    offset = addr - first_addr
    with open(fname, "rb") as f:
        f.seek(offset)
        data = f.read(size)

    patches = []
    for i in range(0, len(data), 4):
        word = data[i:i+4]
        if len(word) < 4:
            break
        hexword = word[::-1].hex()
        patches.append(
            f"patch=1,EE,{addr + i + 0x20000000:08X},extended,{hexword.upper()}"
        )

    return patches

def generate_textblocks_linker(labels, importobjs, obj_addrs, header_symbols=None):
    out = [".ps2"]

    already_defined = set()

    with open("linker.asm", "r") as f:
        original = f.read()
    for line in original.splitlines():
        l = line.strip()
        if l.startswith(".definelabel") or re.match(r'^\w+\s+equ\s+', l):
            out.append(line)
            m = re.match(r'^\.definelabel\s+(\w+)', l)
            if m:
                already_defined.add(m.group(1).lower())
            else:
                m = re.match(r'^(\w+)\s+equ\s+', l)
                if m:
                    already_defined.add(m.group(1).lower())

    if header_symbols:
        for name, addr in header_symbols.items():
            if name.lower() in already_defined:
                continue
            out.append(f".definelabel {name}, {hex(addr)}")
            already_defined.add(name.lower())

    first_addr = min(obj_addrs.values())
    out.append(f'.create "build/textblocks.bin", {hex(first_addr)}')

    for _, name in importobjs:
        addr = obj_addrs[name]
        out.append(f".org {hex(addr)}")
        out.append(f'    .importobj "./obj/{name}.o"')

    out.append(".close")

    with open("build/linker_textblocks.asm", "w") as f:
        f.write("\n".join(out))

def generate_asmblocks_linker(original, asm_blocks, labels, function_symbols):
    out = [".ps2"]

    for line in original.splitlines():
        l = line.strip()
        if l.startswith(".definelabel") or re.match(r'^\w+\s+equ\s+', l):
            out.append(line)

    for sym_name, addr in function_symbols.items():
        out.append(f".definelabel {sym_name}, {hex(addr)}")

    asm_addr_set = set(a for a, _ in asm_blocks)

    resolve_tokens = make_resolve_tokens(labels)

    copying = False
    body_lines = []
    pending_addrs = []

    def flush_block():
        nonlocal copying, body_lines, pending_addrs
        if copying:
            for addr in pending_addrs:
                if addr is None:
                    continue
                out.append(f'.create "build/asmblock_{addr:X}.bin", {addr}')
                out.append(f".org {hex(addr)}")
                out.extend(body_lines)
                out.append(".close")
        copying = False
        body_lines = []
        pending_addrs = []

    for line in original.splitlines():
        stripped = line.strip()
        m = re.match(r'^\.org\s+(.+)$', stripped)
        if m:
            flush_block()
            addrs = resolve_tokens(m.group(1))
            relevant = [a for a in addrs if a in asm_addr_set]
            if relevant:
                copying = True
                pending_addrs = relevant
            continue

        if copying and stripped and not stripped.startswith(";"):
            if stripped == ".Close":
                continue
            body_lines.append(f"    {stripped}")

    flush_block()

    with open("build/linker_asmblocks.asm", "w") as f:
        f.write("\n".join(out))

def read_asmblock_patches(addr, count):
    fname = f"build/asmblock_{addr:X}.bin"
    if not os.path.exists(fname):
        print(f"  WARNING: {fname} was not found")
        return []
    with open(fname, "rb") as f:
        data = f.read(count * 4)
    patches = []
    for i in range(0, len(data), 4):
        word = data[i:i+4]
        if len(word) < 4:
            break
        hexword = word[::-1].hex()
        patches.append(f"patch=1,EE,{addr + i + 0x20000000:08X},extended,{hexword.upper()}")
    return patches

def collect_all_symbols(obj_addrs):
    """Return {symbol_name: final_address} for functions in every object."""
    symbols = {}
    for name, base in obj_addrs.items():
        out = run(f"ee-nm obj/{name}.o")
        for line in out.splitlines():
            m = re.match(r'^([0-9a-f]+)\s+T\s+(\S+)$', line)
            if m:
                offset = int(m.group(1), 16)
                sym_name = m.group(2)
                symbols[sym_name] = base + offset
    return symbols

def elf_patches(elf, start, end):
    out = run(f"ee-objdump -d {elf} --start-address={hex(start)} --stop-address={hex(end)}")
    patches = []
    for line in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})', line)
        if m:
            addr = int(m.group(1), 16) + 0x20000000
            patches.append(f"patch=1,EE,{addr:08X},extended,{m.group(2).upper()}")
    return patches

def resolve_symbol_in_objs(symbol, obj_addrs):
    for name, base in obj_addrs.items():
        out = run(f"ee-nm obj/{name}.o")
        for line in out.splitlines():
            m = re.match(r'^([0-9a-f]+)\s+T\s+' + re.escape(symbol) + r'$', line)
            if m:
                offset = int(m.group(1), 16)
                return base + offset
    return None

def word_patch(addr, value):
    return f"patch=1,EE,{addr + 0x20000000:08X},extended,{value:08X}"

def generate_linker(filename, labels, importobjs, word_orgs, asm_blocks,
                     obj_sizes, obj_data_sizes, obj_rodata_sizes, obj_bss_sizes,
                     header_symbols=None):
    base = CODE_BASE

    addr = base
    obj_addrs = {}
    obj_data_addrs = {}
    obj_rodata_addrs = {}
    obj_bss_addrs = {}
    for _, name in importobjs:
        obj_addrs[name] = addr
        text_size = obj_sizes.get(name, 0)
        data_size = obj_data_sizes.get(name, 0)
        rodata_size = obj_rodata_sizes.get(name, 0)
        bss_size = obj_bss_sizes.get(name, 0)

        data_addr = (addr + text_size + 7) & ~7
        obj_data_addrs[name] = data_addr

        bss_addr = (data_addr + data_size + 3) & ~3
        obj_bss_addrs[name] = bss_addr

        rodata_addr = (bss_addr + bss_size + 7) & ~7
        obj_rodata_addrs[name] = rodata_addr

        addr = (rodata_addr + rodata_size + 15) & ~15

    if addr > CODE_END:
        raise RuntimeError(
            f"compiled C image exceeds selected code bank: {addr:#x} > "
            f"{CODE_END:#x}"
        )

    with open(filename, "r") as f:
        original = f.read()

    header_lines = []
    already_defined = set()
    for line in original.splitlines():
        l = line.strip()
        if l.startswith(".ps2") or l.startswith(".Open") or \
           l.startswith(".definelabel") or l.startswith(";") or \
           re.match(r'^\w+\s+equ\s+', l):
            if re.match(r'^BASE_ADDRESS\s+equ\s+', l):
                header_lines.append(f"BASE_ADDRESS equ {CODE_BASE:#x}")
            else:
                header_lines.append(line)
            m = re.match(r'^\.definelabel\s+(\w+)', l)
            if m:
                already_defined.add(m.group(1).lower())
            else:
                m = re.match(r'^(\w+)\s+equ\s+', l)
                if m:
                    already_defined.add(m.group(1).lower())

    if header_symbols:
        for name, saddr in header_symbols.items():
            if name.lower() in already_defined:
                continue
            header_lines.append(f".definelabel {name}, {hex(saddr)}")
            already_defined.add(name.lower())

    out = header_lines + [""]

    for _, name in importobjs:
        out.append(f".org {hex(obj_addrs[name])}")
        out.append(f'    .importobj "./obj/{name}.o"')

    out.append("")

    for org_addr, token, type_ in word_orgs:
        out.append(f".org {hex(org_addr)}")
        out.append(f"    .word {token}")

    out.append("")

    asm_addr_set = set(a for a, _ in asm_blocks)

    resolve_tokens_gen = make_resolve_tokens(labels)

    copying = False
    body_lines = []
    pending_addrs = []

    def flush_gen():
        nonlocal copying, body_lines, pending_addrs
        if copying:
            for addr in pending_addrs:
                if addr is None:
                    continue
                out.append(f".org {hex(addr)}")
                out.extend(body_lines)
        copying = False
        body_lines = []
        pending_addrs = []

    for line in original.splitlines():
        stripped = line.strip()
        m = re.match(r'^\.org\s+(.+)$', stripped)
        if m:
            flush_gen()
            addrs = resolve_tokens_gen(m.group(1))
            relevant = [a for a in addrs if a in asm_addr_set]
            if relevant:
                copying = True
                pending_addrs = relevant
            continue

        if copying and stripped and not stripped.startswith(";"):
            if stripped == ".Close":
                continue
            body_lines.append(f"    {stripped}")

    flush_gen()

    out.append("")
    out.append(".Close")

    with open("build/linker_generated.asm", "w") as f:
        f.write("\n".join(out))

    print("  Generated build/linker_generated.asm")
    for name in obj_addrs:
        print(
            f"    {name} -> text={hex(obj_addrs[name])} "
            f"bss={hex(obj_bss_addrs[name])} "
            f"rodata={hex(obj_rodata_addrs[name])}"
        )
    for addr, count in asm_blocks:
        print(f"    asm block -> {hex(addr)} ({count} instructions)")

    return obj_addrs, obj_rodata_addrs, obj_data_addrs

def obj_data_size(obj):
    out = run(f"ee-objdump -h {obj}")
    for line in out.splitlines():
        m = re.match(r'^\s*\d+\s+\.data\s+([0-9a-f]+)', line)
        if m:
            return int(m.group(1), 16)
    return 0

def main():
    os.makedirs("obj", exist_ok=True)
    os.makedirs("build", exist_ok=True)
    t0 = time.time()

    header_symbols = parse_header_symbols(HEADER_FILE)
    print(f"Loaded {len(header_symbols)} symbols from {HEADER_FILE}")

    labels, importobjs, word_orgs, asm_blocks = parse_asm("linker.asm", initial_labels=header_symbols)

    if not (labels.get("BASE_ADDRESS") or labels.get("c_code_addr")):
        raise RuntimeError("BASE_ADDRESS was not found in linker.asm")
    labels["BASE_ADDRESS"] = CODE_BASE
    if not importobjs:
        raise RuntimeError("linker.asm does not import any C objects")

    print("Compiling C...")
    objs = []
    for _, name in importobjs:
        src = f"src/{name}.c"
        os.makedirs(OBJ_DIR, exist_ok=True)

        obj = f"{OBJ_DIR}/{name}.o"
        if not os.path.exists(src):
            raise FileNotFoundError(f"Imported C source was not found: {src}")
        print(f"  Compiling {src}...")
        command = (
            "ee-gcc -w -D_EE -G0 -O2 -std=c99 "
            f"-DNA2_INJECTION_BUILD_ID=0x{BUILD_ID:08X}u "
            f"-c {src} -o {obj}"
        )
        if run_cmd(command) != 0:
            raise RuntimeError(f"C compilation failed: {src}")
        objs.append(name)
    t1 = time.time()
    print(f"  -> {int((t1-t0)*1000)}ms")

    obj_sizes = {name: obj_size(f"obj/{name}.o") for name in objs}
    obj_data_sizes = {name: obj_data_size(f"obj/{name}.o") for name in objs}
    obj_rodata_sizes = {name: obj_rodata_size(f"obj/{name}.o") for name in objs}
    obj_bss_sizes = {name: obj_bss_size(f"obj/{name}.o") for name in objs}

    obj_addrs, obj_rodata_addrs, obj_data_addrs = generate_linker(
        "linker.asm", labels, importobjs, word_orgs, asm_blocks,
        obj_sizes, obj_data_sizes, obj_rodata_sizes, obj_bss_sizes,
        header_symbols=header_symbols
    )

    print("Linking main image...")
    if run_cmd("armips.exe build/linker_generated.asm") != 0:
        raise RuntimeError("Armips failed to link the main image")

    function_symbols = collect_all_symbols(obj_addrs)

    generate_textblocks_linker(labels, importobjs, obj_addrs, header_symbols=header_symbols)
    print("Linking text blocks...")
    if run_cmd("armips.exe build/linker_textblocks.asm") != 0:
        raise RuntimeError("Armips failed to link the injected text blocks")

    with open("linker.asm", "r") as f:
        original_content = f.read()
    generate_asmblocks_linker(original_content, asm_blocks, labels, function_symbols)
    print("Linking assembly blocks...")
    if run_cmd("armips.exe build/linker_asmblocks.asm") != 0:
        raise RuntimeError("Armips failed to link the hook assembly blocks")

    t2 = time.time()
    print(f"  -> {int((t2-t1)*1000)}ms")

    print("Generating PNACH...")
    lines_out = []
    lines_out.append("// Auto-generated pnach")
    lines_out.append("gametitle=Narutimate Accel v2.28 injection lab")
    lines_out.append(f"// Current CRC: {CRC}")
    lines_out.append(
        f"// Reserved range: 0x{INJECTION_BASE:08X}-0x{INJECTION_END:08X}"
    )
    lines_out.append(f"// Code bank: 0x{CODE_BASE:08X}-0x{CODE_END:08X}")
    lines_out.append(f"// Build ID: 0x{BUILD_ID:08X}")
    lines_out.append("")

    lines_out.append("; injected code")
    first_addr = min(obj_addrs.values())
    for name in objs:
        addr = obj_addrs[name]
        lines_out += read_textblock_patches(first_addr, addr, obj_sizes[name])

    lines_out.append("")

    lines_out.append("; rodata")
    for name in objs:
        rodata = objdump_rodata(f"obj/{name}.o")
        rodata_addr = obj_rodata_addrs[name]
        if rodata:
            for i in range(0, len(rodata), 8):
                word = rodata[i:i+8]
                if len(word) < 8:
                    word = word.ljust(8, '0')
                le = word[6:8] + word[4:6] + word[2:4] + word[0:2]
                patch_addr = rodata_addr + (i // 8) * 4 + 0x20000000
                lines_out.append(f"patch=1,EE,{patch_addr:08X},extended,{le.upper()}")
    lines_out.append("")

    lines_out.append("; data")
    for name in objs:
        data = objdump_data(f"obj/{name}.o")
        data_addr = obj_data_addrs[name]
        if data:
            for i in range(0, len(data), 8):
                word = data[i:i+8]
                if len(word) < 8:
                    word = word.ljust(8, '0')
                le = word[6:8] + word[4:6] + word[2:4] + word[0:2]
                patch_addr = data_addr + (i // 8) * 4 + 0x20000000
                lines_out.append(f"patch=1,EE,{patch_addr:08X},extended,{le.upper()}")
    lines_out.append("")

    lines_out.append("; asm blocks")
    for addr, count in asm_blocks:
        lines_out += read_asmblock_patches(addr, count)
    lines_out.append("")

    lines_out.append("; hooks (.word)")
    for org_addr, token, type_ in word_orgs:
        if type_ == "literal":
            lines_out.append(word_patch(org_addr, int(token, 0)))
        elif type_ == "symbol":
            resolved = resolve_symbol_in_objs(token, obj_addrs)
            source = "obj"
            if resolved is None and token in header_symbols:
                resolved = header_symbols[token]
                source = "Main.h"
            if resolved is None:
                raise RuntimeError(
                    f"Hook symbol '{token}' was not found in the objects or "
                    f"{HEADER_FILE}"
                )
            else:
                lines_out.append(f"; {token} -> {hex(resolved)} ({source})")
                lines_out.append(word_patch(org_addr, resolved))
    lines_out.append("")

    with open(PNACH_FILE, "w") as f:
        f.write("\n".join(lines_out))

    t3 = time.time()
    print(f"  -> {int((t3-t2)*1000)}ms")
    print(f"PNACH generated at {PNACH_FILE}")
    print(f"Total: {int((t3-t0)*1000)}ms")

if __name__ == "__main__":
    main()
