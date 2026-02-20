#!/usr/bin/env python3
# Test suite for Unknown Runes ISA VM

import sys
import os
import io

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Source"))
from customISA import RuneVM

# Register encoding (raw 2-bit field values before decode subtracts 1)
NONE = 0  # 00 = no register
RA = 1  # 01 = RA (index 0)
RB = 2  # 10 = RB (index 1)
RC = 3  # 11 = RC (index 2)

passed = 0
total = 0


def encInstr(op, r1=NONE, r2=NONE, r3=NONE, imm=0):
    # Encode 42-bit instruction into 6 bytes (little-endian)
    imm = imm & 0xFFFFFF
    instr = (op << 34) | (r1 << 30) | (r2 << 28) | (r3 << 26) | imm
    return instr.to_bytes(6, "little")


def runTest(name, instrs, inData="", expectOut=None, presetMem=None):
    global passed, total
    total += 1
    prog = b"".join(instrs)
    inStream = io.StringIO(inData)
    outStream = io.StringIO()
    vm = RuneVM(inStream=inStream, outStream=outStream)
    vm.loadProg(prog)
    if presetMem:
        for addr, val in presetMem.items():
            vm.mem[addr] = val
    try:
        vm.run()
    except SystemExit:
        pass
    output = outStream.getvalue()
    ok = expectOut is None or output == expectOut
    tag = "PASS" if ok else "FAIL"
    extra = f"  expected={expectOut!r}" if not ok else ""
    print(f"  [{tag}] {name}: output={output!r}{extra}")
    if ok:
        passed += 1


def runErrTest(name, instrs, expectErr=None):
    global passed, total
    total += 1
    prog = b"".join(instrs)
    vm = RuneVM(outStream=io.StringIO())
    vm.loadProg(prog)
    try:
        vm.run()
        print(f"  [FAIL] {name}: expected error but none raised")
    except SystemExit:
        print(f"  [FAIL] {name}: expected error but got SystemExit")
    except RuntimeError as e:
        ok = expectErr is None or expectErr in str(e)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}: error={e!r}")
        if ok:
            passed += 1


# === Arithmetic ===
print("=== Arithmetic ===")

runTest(
    "MOV + PRINT_INT",
    [
        encInstr(0x01, RA, imm=42),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "MOV negative",
    [
        encInstr(0x01, RA, imm=(-5) & 0xFFFFFF),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="-5",
)

runTest(
    "MOVR",
    [
        encInstr(0x01, RA, imm=42),
        encInstr(0x02, RB, RA),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RB),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "ADD",
    [
        encInstr(0x01, RA, imm=30),
        encInstr(0x01, RB, imm=12),
        encInstr(0x03, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "SUB",
    [
        encInstr(0x01, RA, imm=100),
        encInstr(0x01, RB, imm=58),
        encInstr(0x04, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "ADDI",
    [
        encInstr(0x01, RA, imm=40),
        encInstr(0x05, RA, imm=2),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "SUBI",
    [
        encInstr(0x01, RA, imm=50),
        encInstr(0x06, RA, imm=8),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "MUL",
    [
        encInstr(0x01, RA, imm=6),
        encInstr(0x01, RB, imm=7),
        encInstr(0x07, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "DIV",
    [
        encInstr(0x01, RA, imm=84),
        encInstr(0x01, RB, imm=2),
        encInstr(0x08, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "DIV truncates toward zero",
    [
        encInstr(0x01, RA, imm=(-7) & 0xFFFFFF),
        encInstr(0x01, RB, imm=2),
        encInstr(0x08, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="-3",
)

runTest(
    "MOD",
    [
        encInstr(0x01, RA, imm=47),
        encInstr(0x01, RB, imm=5),
        encInstr(0x09, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="2",
)

# === Bitwise ===
print("=== Bitwise ===")

runTest(
    "AND",
    [
        encInstr(0x01, RA, imm=0xFF),
        encInstr(0x01, RB, imm=0x0F),
        encInstr(0x0A, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="15",
)

runTest(
    "OR",
    [
        encInstr(0x01, RA, imm=0xF0),
        encInstr(0x01, RB, imm=0x0F),
        encInstr(0x0B, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="255",
)

runTest(
    "XOR",
    [
        encInstr(0x01, RA, imm=0xFF),
        encInstr(0x01, RB, imm=0xF0),
        encInstr(0x0C, RC, RA, RB),
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),
        encInstr(0x00),
    ],
    expectOut="15",
)

runTest(
    "NOT (-Reg1)",
    [
        encInstr(0x01, RA, imm=42),
        encInstr(0x0D, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="-42",
)

runTest(
    "NEG (~Reg1)",
    [
        encInstr(0x01, RA, imm=0),
        encInstr(0x1E, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="-1",
)

runTest(
    "SHL",
    [
        encInstr(0x01, RA, imm=1),
        encInstr(0x0E, RA, imm=4),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="16",
)

runTest(
    "SHR",
    [
        encInstr(0x01, RA, imm=64),
        encInstr(0x0F, RA, imm=3),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="8",
)

# === Misc Single-Reg ===
print("=== Misc Single-Reg ===")

runTest(
    "MZERO",
    [
        encInstr(0x01, RA, imm=999),
        encInstr(0x1B, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="0",
)

runTest(
    "INC",
    [
        encInstr(0x01, RA, imm=41),
        encInstr(0x1C, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "DEC",
    [
        encInstr(0x01, RA, imm=43),
        encInstr(0x1D, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

# === Memory ===
print("=== Memory ===")

runTest(
    "STORE + LOAD",
    [
        encInstr(0x01, RA, imm=42),
        encInstr(0x01, RB, imm=0x100),
        encInstr(0x11, RB, RA),
        encInstr(0x1B, RA),
        encInstr(0x10, RA, RB),
        encInstr(0x01, RC, imm=1),
        encInstr(0x1F, RC, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "STOREI + LOADI",
    [
        encInstr(0x01, RA, imm=42),
        encInstr(0x13, RA, imm=0x200),
        encInstr(0x1B, RA),
        encInstr(0x12, RA, imm=0x200),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

# === Jumps ===
print("=== Jumps ===")

runTest(
    "JMP",
    [
        encInstr(0x01, RA, imm=99),
        encInstr(0x14, imm=3 * 6),
        encInstr(0x01, RA, imm=0),  # skipped
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="99",
)

runTest(
    "JEQ taken",
    [
        encInstr(0x01, RA, imm=5),
        encInstr(0x01, RB, imm=5),
        encInstr(0x15, RA, RB, imm=4 * 6),
        encInstr(0x01, RA, imm=0),  # skipped
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="5",
)

runTest(
    "JEQ not taken",
    [
        encInstr(0x01, RA, imm=5),
        encInstr(0x01, RB, imm=6),
        encInstr(0x15, RA, RB, imm=4 * 6),
        encInstr(0x01, RA, imm=99),  # reached
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="99",
)

runTest(
    "JNE taken",
    [
        encInstr(0x01, RA, imm=3),
        encInstr(0x01, RB, imm=7),
        encInstr(0x16, RA, RB, imm=4 * 6),
        encInstr(0x01, RA, imm=0),  # skipped
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="3",
)

runTest(
    "JLT taken",
    [
        encInstr(0x01, RA, imm=3),
        encInstr(0x01, RB, imm=10),
        encInstr(0x17, RA, RB, imm=4 * 6),
        encInstr(0x01, RA, imm=0),  # skipped
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="3",
)

runTest(
    "JGT taken",
    [
        encInstr(0x01, RA, imm=10),
        encInstr(0x01, RB, imm=3),
        encInstr(0x18, RA, RB, imm=4 * 6),
        encInstr(0x01, RA, imm=0),  # skipped
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="10",
)

runTest(
    "JLE taken (equal)",
    [
        encInstr(0x01, RA, imm=5),
        encInstr(0x01, RB, imm=5),
        encInstr(0x19, RA, RB, imm=4 * 6),
        encInstr(0x01, RA, imm=0),  # skipped
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="5",
)

runTest(
    "JGE taken (greater)",
    [
        encInstr(0x01, RA, imm=10),
        encInstr(0x01, RB, imm=3),
        encInstr(0x1A, RA, RB, imm=4 * 6),
        encInstr(0x01, RA, imm=0),  # skipped
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="10",
)

# === Syscalls ===
print("=== Syscalls ===")

runTest(
    "PRINT_HEX",
    [
        encInstr(0x01, RA, imm=255),
        encInstr(0x01, RB, imm=7),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="0xFF",
)

runTest(
    "PRINT_STR (null-terminated)",
    [
        encInstr(0x01, RA, imm=2),
        encInstr(0x01, RB, imm=0x100),
        encInstr(0x01, RC, imm=0),
        encInstr(0x1F, RA, RB, RC),
        encInstr(0x00),
    ],
    presetMem={0x100: ord("H"), 0x101: ord("i"), 0x102: 0},
    expectOut="Hi",
)

runTest(
    "PRINT_STR (with length)",
    [
        encInstr(0x01, RA, imm=2),
        encInstr(0x01, RB, imm=0x100),
        encInstr(0x01, RC, imm=3),
        encInstr(0x1F, RA, RB, RC),
        encInstr(0x00),
    ],
    presetMem={0x100: ord("A"), 0x101: ord("B"), 0x102: ord("C"), 0x103: ord("D")},
    expectOut="ABC",
)

runTest(
    "READ_INT",
    [
        encInstr(0x01, RA, imm=3),
        encInstr(0x1F, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    inData="42\n",
    expectOut="42",
)

runTest(
    "STRLEN",
    [
        encInstr(0x01, RA, imm=5),
        encInstr(0x01, RB, imm=0x100),
        encInstr(0x1F, RA, RB),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    presetMem={0x100: ord("H"), 0x101: ord("e"), 0x102: ord("y"), 0x103: 0},
    expectOut="3",
)

runTest(
    "STRCMP equal",
    [
        encInstr(0x01, RA, imm=6),
        encInstr(0x01, RB, imm=0x100),
        encInstr(0x01, RC, imm=0x110),
        encInstr(0x1F, RA, RB, RC),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    presetMem={
        0x100: ord("A"),
        0x101: ord("B"),
        0x102: 0,
        0x110: ord("A"),
        0x111: ord("B"),
        0x112: 0,
    },
    expectOut="0",
)

runTest(
    "STRCMP less",
    [
        encInstr(0x01, RA, imm=6),
        encInstr(0x01, RB, imm=0x100),
        encInstr(0x01, RC, imm=0x110),
        encInstr(0x1F, RA, RB, RC),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    presetMem={0x100: ord("A"), 0x101: 0, 0x110: ord("B"), 0x111: 0},
    expectOut="-1",
)

# === Register flexibility ===
print("=== Register Flexibility ===")

runTest(
    "Any reg in any slot (RC as dst, RB+RA as src)",
    [
        encInstr(0x01, RB, imm=20),
        encInstr(0x01, RA, imm=22),
        encInstr(0x03, RC, RB, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RC),
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "Same reg as dst and src",
    [
        encInstr(0x01, RA, imm=21),
        encInstr(0x03, RA, RA, RA),
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),
        encInstr(0x00),
    ],
    expectOut="42",
)

# === Error cases ===
print("=== Error Cases ===")

runErrTest(
    "DIV by zero",
    [
        encInstr(0x01, RA, imm=10),
        encInstr(0x01, RB, imm=0),
        encInstr(0x08, RC, RA, RB),
        encInstr(0x00),
    ],
    expectErr="Division by zero",
)

runErrTest(
    "MOD by zero",
    [
        encInstr(0x01, RA, imm=10),
        encInstr(0x01, RB, imm=0),
        encInstr(0x09, RC, RA, RB),
        encInstr(0x00),
    ],
    expectErr="Modulo by zero",
)

runErrTest(
    "No register (00 in required field)",
    [
        encInstr(0x01, NONE, imm=42),
        encInstr(0x00),
    ],
    expectErr="no register",
)

# Build a raw instruction with rsv (33..32) != 0
total += 1
raw_rsv = (0x01 << 34) | (1 << 32) | (RA << 30) | 42  # rsv=1
prog_rsv = raw_rsv.to_bytes(6, "little")
vm_rsv = RuneVM(outStream=io.StringIO())
vm_rsv.loadProg(prog_rsv)
try:
    vm_rsv.run()
    print("  [FAIL] Reserved bits (33..32): expected error")
except SystemExit:
    print("  [FAIL] Reserved bits (33..32): expected error")
except RuntimeError as e:
    ok = "Reserved" in str(e)
    print(f"  [{'PASS' if ok else 'FAIL'}] Reserved bits (33..32): error={e!r}")
    if ok:
        passed += 1

# Build a raw instruction with rsv2 != 0
total += 1
raw = (0x01 << 34) | (RA << 30) | (1 << 24) | 42  # rsv2=1
prog = raw.to_bytes(6, "little")
vm = RuneVM(outStream=io.StringIO())
vm.loadProg(prog)
try:
    vm.run()
    print("  [FAIL] Reserved bits (25..24): expected error")
except SystemExit:
    print("  [FAIL] Reserved bits (25..24): expected error")
except RuntimeError as e:
    ok = "Reserved" in str(e)
    print(f"  [{'PASS' if ok else 'FAIL'}] Reserved bits (25..24): error={e!r}")
    if ok:
        passed += 1

# === Loop test (INC + JLT) ===
print("=== Integration ===")

# Count from 0 to 4, print each
# RA = counter, RB = limit, RC = scratch for syscall
runTest(
    "Loop (INC + JLT)",
    [
        encInstr(0x1B, RA),  # 0: MZERO RA (counter=0)
        encInstr(0x01, RB, imm=5),  # 1: MOV RB, 5 (limit)
        encInstr(0x01, RC, imm=1),  # 2: MOV RC, 1 (PRINT_INT)
        encInstr(0x1F, RC, RA),  # 3: SYSCALL PRINT_INT(RA)
        encInstr(0x1C, RA),  # 4: INC RA
        encInstr(0x17, RA, RB, imm=3 * 6),  # 5: JLT RA, RB → loop to 3
        encInstr(0x00),  # 6: HALT
    ],
    expectOut="01234",
)

# === Stack Operations ===
print("=== Stack Operations ===")

runTest(
    "PUSH + POP",
    [
        encInstr(0x01, RA, imm=42),
        encInstr(0x20, RA),  # PUSH RA
        encInstr(0x1B, RA),  # MZERO RA (clear it)
        encInstr(0x21, RA),  # POP RA
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),  # PRINT_INT(RA)
        encInstr(0x00),
    ],
    expectOut="42",
)

runTest(
    "PUSH order (LIFO)",
    [
        encInstr(0x01, RA, imm=11),
        encInstr(0x01, RB, imm=22),
        encInstr(0x20, RA),  # PUSH 11
        encInstr(0x20, RB),  # PUSH 22
        encInstr(0x21, RC),  # POP → 22 (last pushed)
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),  # PRINT_INT(22)
        encInstr(0x21, RC),  # POP → 11
        encInstr(0x01, RA, imm=1),
        encInstr(0x1F, RA, RC),  # PRINT_INT(11)
        encInstr(0x00),
    ],
    expectOut="2211",
)

runTest(
    "PUSHI",
    [
        encInstr(0x24, imm=99),  # PUSHI 99
        encInstr(0x21, RA),  # POP RA
        encInstr(0x01, RB, imm=1),
        encInstr(0x1F, RB, RA),  # PRINT_INT(RA)
        encInstr(0x00),
    ],
    expectOut="99",
)

runTest(
    "PUSHA + POPA",
    [
        encInstr(0x01, RA, imm=10),
        encInstr(0x01, RB, imm=20),
        encInstr(0x01, RC, imm=30),
        encInstr(0x25, RA, RB, RC),  # PUSHA (save all)
        encInstr(0x1B, RA),  # clear all
        encInstr(0x1B, RB),
        encInstr(0x1B, RC),
        encInstr(0x26, RA, RB, RC),  # POPA (restore all)
        encInstr(0x01, RC, imm=1),
        encInstr(0x1F, RC, RA),  # PRINT_INT(RA) → 10
        encInstr(0x01, RC, imm=1),
        encInstr(0x1F, RC, RB),  # PRINT_INT(RB) → 20
        encInstr(0x00),
    ],
    expectOut="1020",
)

runTest(
    "CALL + RET",
    [
        encInstr(0x14, imm=3 * 6),  # 0: JMP to main (skip func)
        # func at offset 6:
        encInstr(0x01, RA, imm=42),  # 1: MOV RA, 42
        encInstr(0x23),  # 2: RET
        # main at offset 18:
        encInstr(0x01, RB, imm=1 * 6),  # 3: MOV RB, addr of func (6)
        encInstr(0x22, RB),  # 4: CALL RB
        encInstr(0x01, RB, imm=1),  # 5: MOV RB, 1
        encInstr(0x1F, RB, RA),  # 6: PRINT_INT(RA) → 42
        encInstr(0x00),  # 7: HALT
    ],
    expectOut="42",
)

runTest(
    "Nested CALL + RET",
    [
        encInstr(0x14, imm=6 * 6),  # 0: JMP to main (offset 36)
        # inner func at offset 6:
        encInstr(0x01, RA, imm=77),  # 1: MOV RA, 77
        encInstr(0x23),  # 2: RET
        # outer func at offset 18:
        encInstr(0x01, RC, imm=1 * 6),  # 3: MOV RC, addr of inner
        encInstr(0x22, RC),  # 4: CALL inner → returns with RA=77
        encInstr(0x23),  # 5: RET
        # main at offset 36:
        encInstr(0x01, RB, imm=3 * 6),  # 6: MOV RB, addr of outer (18)
        encInstr(0x22, RB),  # 7: CALL outer → returns with RA=77
        encInstr(0x01, RB, imm=1),  # 8: MOV RB, 1
        encInstr(0x1F, RB, RA),  # 9: PRINT_INT(RA) → 77
        encInstr(0x00),  # 10: HALT
    ],
    expectOut="77",
)

print(f"\n{'=' * 40}")
print(f"Results: {passed}/{total} tests passed")
if passed == total:
    print("All tests passed!")
else:
    print(f"{total - passed} test(s) FAILED")
