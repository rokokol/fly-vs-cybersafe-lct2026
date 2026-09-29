#!/usr/bin/env python3
"""Run the whole demo and write a trace for the animation

Steps, all real:
1. Read the stored PIN reference from the flash dump.
2. Let the fly smell out that PIN through the timing oracle (run-and-tumble).
3. Decrypt the hidden storage offline with the fixed firmware key.
4. Write out/trace.json: the odour field, every fly sniff, and the decrypt result

The PIN and the cipher are independent: the PIN opens the USB gate, the fixed key
opens the data. The fly does step 2; step 3 needs no PIN
"""
import argparse
import json
from pathlib import Path

import firmware
import oracle
from fly import Fly, candidate_to_xy

HERE = Path(__file__).resolve().parent
DEFAULT_DUMP = HERE / "data" / "backup_full.bin"
DEFAULT_OUT = HERE / "out" / "trace.json"
GRID = 100


def odour_field(ora):
    """A GRID x GRID map of the leaked prefix length, the smell the fly follows"""
    field = []
    for y in range(GRID):
        row = []
        for x in range(GRID):
            candidate = (x // 10, x % 10, y // 10, y % 10)
            row.append(ora.sniff(candidate)[1])
        field.append(row)
    return field


def _lfn_text(entry):
    """The 13 UTF-16 characters carried by one long-file-name entry"""
    raw = entry[1:11] + entry[14:26] + entry[28:32]
    return raw.decode("utf-16-le", errors="ignore")


def root_files(plain):
    """List the regular files in the FAT12 root directory of the plaintext

    Long file names are reassembled; subdirectories and volume labels are left out
    """
    bytes_per_sector = int.from_bytes(plain[0x0B:0x0D], "little")
    reserved = int.from_bytes(plain[0x0E:0x10], "little")
    num_fats = plain[0x10]
    root_entries = int.from_bytes(plain[0x11:0x13], "little")
    sectors_per_fat = int.from_bytes(plain[0x16:0x18], "little")
    root_start = (reserved + num_fats * sectors_per_fat) * bytes_per_sector

    files = []
    pending = []  # long-name fragments seen just before a short entry
    for i in range(root_entries):
        entry = plain[root_start + i * 32:root_start + i * 32 + 32]
        if len(entry) < 32 or entry[0] == 0x00:
            break
        attr = entry[11]
        if entry[0] == 0xE5:
            pending = []
            continue
        if attr & 0x0F == 0x0F:
            pending.append((entry[0] & 0x1F, _lfn_text(entry)))
            continue
        if attr & 0x08:  # volume label
            pending = []
            continue
        if attr & 0x10:  # subdirectory
            pending = []
            continue
        if pending:
            pending.sort()
            name = "".join(text for _, text in pending).split("\x00", 1)[0]
        else:
            base = entry[0:8].decode("latin1").rstrip()
            ext = entry[8:11].decode("latin1").rstrip()
            name = f"{base}.{ext}" if ext else base
        files.append(name)
        pending = []
    return files


def decrypt_summary(dump):
    plain = firmware.decrypt(dump)
    files = root_files(plain)
    zips = [name for name in files if name.lower().endswith(".zip")]
    return {
        "sector0": plain[:16].hex(" "),
        "oem": plain[3:11].decode("latin1"),
        "boot_sig": plain[510:512].hex(" "),
        "storage_bytes": len(plain),
        "is_zip": b"PK\x03\x04" in plain,
        "root_files": files,
        "artifact": (zips or files or [None])[0],
    }


def run_fly(reference, seed, noise_ms):
    """Run one hunt and return its trace, checking the safe actually opened"""
    ora = oracle.Oracle(reference, noise_ms=noise_ms)
    trace = Fly(ora, seed=seed).hunt()
    found = "".join(str(d) for d in trace[-1]["candidate"])
    if found != "".join(str(d) for d in reference):
        raise SystemExit(f"fly ended on {found}, expected {''.join(map(str, reference))}")
    return trace


def pick_seed(reference, noise_ms, seeds=range(120), cap=1200):
    """Pick a seed with a typical hunt length for this noise, so the run is
    representative of the cost rather than a lucky short one, and still watchable
    """
    lengths = []
    for seed in seeds:
        trace = Fly(oracle.Oracle(reference, noise_ms=noise_ms), seed=seed).hunt()
        if trace[-1]["accepted"] and len(trace) <= cap:
            lengths.append((len(trace), seed))
    if not lengths:
        return 0
    lengths.sort()
    return lengths[len(lengths) // 2][1]  # the median-length run


def build_trace(dump, seed, noise_ms=0):
    pin = firmware.extract_pin(dump)
    reference = tuple(int(d) for d in pin)
    trace = run_fly(reference, seed, noise_ms)
    return {
        "pin": pin,
        "grid": GRID,
        "step_ms": oracle.STEP_MS,
        "seed": seed,
        "noise_ms": noise_ms,
        "target_xy": list(candidate_to_xy(reference)),
        "sniffs": len(trace),
        "field": odour_field(oracle.Oracle(reference)),
        "trace": trace,
        "decrypt": decrypt_summary(dump),
    }


def build_dataset(dump, levels):
    """Build the web dataset: the shared field plus one hunt per noise level"""
    pin = firmware.extract_pin(dump)
    reference = tuple(int(d) for d in pin)
    runs = []
    for noise_ms in levels:
        seed = pick_seed(reference, noise_ms)
        trace = run_fly(reference, seed, noise_ms)
        runs.append({
            "noise_ms": noise_ms,
            "seed": seed,
            "sniffs": len(trace),
            "trace": trace,
        })
    return {
        "pin": pin,
        "grid": GRID,
        "step_ms": oracle.STEP_MS,
        "target_xy": list(candidate_to_xy(reference)),
        "field": odour_field(oracle.Oracle(reference)),
        "decrypt": decrypt_summary(dump),
        "runs": runs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--noise", type=float, default=0.0,
                        help="measurement jitter (ms, standard deviation)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = build_trace(args.dump, args.seed, args.noise)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data))

    dec = data["decrypt"]
    print(f"PIN reference in flash : {data['pin']}")
    print(f"measurement noise      : {data['noise_ms']} ms")
    print(f"fly sniffs to open     : {data['sniffs']} (blind space is 10000)")
    print(f"storage decrypted      : {dec['storage_bytes']} bytes")
    print(f"boot sector            : {dec['sector0']}")
    print(f"OEM / signature        : {dec['oem']} / {dec['boot_sig']}")
    print(f"root files             : {', '.join(dec['root_files']) or '(none)'}")
    print(f"artifact inside        : {dec['artifact']} (zip={dec['is_zip']})")
    print(f"trace written          : {args.out} ({len(data['trace'])} frames)")


if __name__ == "__main__":
    main()
