# Unknown Runes ISA Assembler (42-bit instructions)
# Assembles .asm source into binary for the Unknown Runes VM

import sys
import re
from typing import Dict, List, Optional


class UnknownRunesAsm:
    # Assembler for Unknown Runes ISA

    INSTRSZ = 6

    # Register encoding (2-bit raw field values in instruction)
    REGS = {"RA": 0b01, "RB": 0b10, "RC": 0b11}
    NOREG = 0b00

    # Opcode table
    OPCODES = {
        "HALT": 0x00,
        "MOV": 0x01,
        "MOVR": 0x02,
        "ADD": 0x03,
        "SUB": 0x04,
        "ADDI": 0x05,
        "SUBI": 0x06,
        "MUL": 0x07,
        "DIV": 0x08,
        "MOD": 0x09,
        "AND": 0x0A,
        "OR": 0x0B,
        "XOR": 0x0C,
        "NOT": 0x0D,
        "SHL": 0x0E,
        "SHR": 0x0F,
        "LOAD": 0x10,
        "STORE": 0x11,
        "LOADI": 0x12,
        "STOREI": 0x13,
        "JMP": 0x14,
        "JEQ": 0x15,
        "JNE": 0x16,
        "JLT": 0x17,
        "JGT": 0x18,
        "JLE": 0x19,
        "JGE": 0x1A,
        "MZERO": 0x1B,
        "INC": 0x1C,
        "DEC": 0x1D,
        "NEG": 0x1E,
        "SYSCALL": 0x1F,
        "PUSH": 0x20,
        "POP": 0x21,
        "CALL": 0x22,
        "RET": 0x23,
        "PUSHI": 0x24,
        "PUSHA": 0x25,
        "POPA": 0x26,
    }

    # Operand format per opcode: r=register, i=immediate/label, *=variable regs
    FMTS = {
        "HALT": "",
        "MOV": "ri",
        "MOVR": "rr",
        "ADD": "rrr",
        "SUB": "rrr",
        "ADDI": "ri",
        "SUBI": "ri",
        "MUL": "rrr",
        "DIV": "rrr",
        "MOD": "rrr",
        "AND": "rrr",
        "OR": "rrr",
        "XOR": "rrr",
        "NOT": "r",
        "SHL": "ri",
        "SHR": "ri",
        "LOAD": "rr",
        "STORE": "rr",
        "LOADI": "ri",
        "STOREI": "ri",
        "JMP": "i",
        "JEQ": "rri",
        "JNE": "rri",
        "JLT": "rri",
        "JGT": "rri",
        "JLE": "rri",
        "JGE": "rri",
        "MZERO": "r",
        "INC": "r",
        "DEC": "r",
        "NEG": "r",
        "SYSCALL": "*",
        "PUSH": "r",
        "POP": "r",
        "CALL": "r",
        "RET": "",
        "PUSHI": "i",
        "PUSHA": "rrr",
        "POPA": "rrr",
    }

    def __init__(self):
        self.labels: Dict[str, int] = {}
        self.out: bytearray = bytearray()
        self.pos = 0
        self.errs: List[str] = []

    def err(self, ln: int, msg: str) -> None:
        # Record an assembly error
        self.errs.append(f"Line {ln}: {msg}")

    def parseReg(self, tok: str) -> Optional[int]:
        # Parse register name → raw 2-bit encoding, or None
        return self.REGS.get(tok.upper())

    def parseImm(self, tok: str, ln: int) -> Optional[int]:
        # Parse immediate (decimal, hex, binary) or label name
        tok = tok.strip()
        if tok in self.labels:
            return self.labels[tok]
        tUp = tok.upper()
        if tUp in self.labels:
            return self.labels[tUp]
        try:
            if tok.startswith(("0x", "0X")):
                return int(tok, 16)
            if tok.startswith(("0b", "0B")):
                return int(tok, 2)
            return int(tok)
        except ValueError:
            self.err(ln, f"Bad immediate/label: {tok}")
            return None

    def encInstr(
        self, op: int, r1: int = 0, r2: int = 0, r3: int = 0, imm: int = 0
    ) -> bytes:
        # Encode 42-bit instruction into 6 bytes (little-endian)
        imm24 = imm & 0xFFFFFF
        instr = (op << 34) | (r1 << 30) | (r2 << 28) | (r3 << 26) | imm24
        return instr.to_bytes(6, "little")

    def escStr(self, s: str) -> bytes:
        # Process escape sequences in a string literal
        out = bytearray()
        i, n = 0, len(s)
        while i < n:
            if s[i] == "\\" and i + 1 < n:
                c = s[i + 1]
                match c:
                    case "n":
                        out.append(0x0A)
                        i += 2
                    case "t":
                        out.append(0x09)
                        i += 2
                    case "r":
                        out.append(0x0D)
                        i += 2
                    case "0":
                        out.append(0x00)
                        i += 2
                    case "\\":
                        out.append(0x5C)
                        i += 2
                    case '"':
                        out.append(0x22)
                        i += 2
                    case "'":
                        out.append(0x27)
                        i += 2
                    case "x" if i + 3 < n:
                        try:
                            out.append(int(s[i + 2 : i + 4], 16))
                            i += 4
                        except ValueError:
                            out.append(ord(c))
                            i += 2
                    case _:
                        out.append(ord(c))
                        i += 2
            else:
                out.append(ord(s[i]))
                i += 1
        return bytes(out)

    def extractStr(self, line: str) -> Optional[str]:
        # Extract quoted string literal from a line
        m = re.search(r'"((?:[^"\\]|\\.)*)"', line)
        if m:
            return m.group(1)
        m = re.search(r"'((?:[^'\\]|\\.)*)'", line)
        if m:
            return m.group(1)
        return None

    def stripLine(self, raw: str) -> tuple:
        # Strip comments, extract label if present → (label, rest)
        line = raw.split(";")[0].strip()
        lbl = None
        if ":" in line:
            qIdx = line.find('"')
            cIdx = line.find(":")
            if qIdx == -1 or cIdx < qIdx:
                lblPart, line = line.split(":", 1)
                lbl = lblPart.strip()
                line = line.strip()
        return lbl, line

    def tokenize(self, line: str) -> List[str]:
        # Split instruction line into tokens
        parts = re.split(r"[,\s]+", line)
        return [p for p in parts if p]

    def lineSize(self, toks: List[str], raw: str) -> int:
        # Calculate how many bytes a source line contributes
        if not toks:
            return 0
        mnem = toks[0].upper()
        match mnem:
            case ".DB" | ".BYTE":
                return len(toks) - 1
            case ".DW" | ".WORD":
                return (len(toks) - 1) * 3
            case ".DS" | ".STRING":
                s = self.extractStr(raw)
                return (len(self.escStr(s)) + 1) if s else 0
            case ".ALIGN":
                rem = self.pos % self.INSTRSZ
                return (self.INSTRSZ - rem) if rem != 0 else 0
            case _ if mnem in self.OPCODES:
                return self.INSTRSZ
        return 0

    def pass1(self, src: str) -> None:
        # First pass: collect labels and compute byte positions
        self.labels = {}
        self.pos = 0
        for ln, raw in enumerate(src.splitlines(), 1):
            lbl, line = self.stripLine(raw)
            if lbl:
                self.labels[lbl] = self.pos
            toks = self.tokenize(line) if line else []
            self.pos += self.lineSize(toks, raw)

    def pass2(self, src: str) -> bytearray:
        # Second pass: encode instructions and data
        self.out = bytearray()
        self.pos = 0
        for ln, raw in enumerate(src.splitlines(), 1):
            _, line = self.stripLine(raw)
            if not line:
                continue
            toks = self.tokenize(line)
            if not toks:
                continue
            mnem = toks[0].upper()
            args = toks[1:]

            # Directives
            match mnem:
                case ".DB" | ".BYTE":
                    for a in args:
                        v = self.parseImm(a, ln)
                        if v is not None:
                            self.out.append(v & 0xFF)
                            self.pos += 1
                    continue
                case ".DW" | ".WORD":
                    for a in args:
                        v = self.parseImm(a, ln)
                        if v is not None:
                            v24 = v & 0xFFFFFF
                            for i in range(3):
                                self.out.append((v24 >> (i * 8)) & 0xFF)
                            self.pos += 3
                    continue
                case ".DS" | ".STRING":
                    s = self.extractStr(raw)
                    if s is None:
                        self.err(ln, "Missing string literal")
                        continue
                    bs = self.escStr(s)
                    self.out.extend(bs)
                    self.out.append(0)
                    self.pos += len(bs) + 1
                    continue
                case ".ALIGN":
                    while self.pos % self.INSTRSZ != 0:
                        self.out.append(0)
                        self.pos += 1
                    continue

            # Instructions
            if mnem not in self.OPCODES:
                self.err(ln, f"Unknown mnemonic: {mnem}")
                continue

            op = self.OPCODES[mnem]
            fmt = self.FMTS[mnem]
            r1, r2, r3, imm = self.NOREG, self.NOREG, self.NOREG, 0
            rIdx = 0

            if fmt == "*":
                # SYSCALL: 1-3 register operands
                if not args:
                    self.err(ln, "SYSCALL requires at least 1 register")
                for i, a in enumerate(args[:3]):
                    rv = self.parseReg(a)
                    if rv is None:
                        self.err(ln, f"Expected register, got: {a}")
                        break
                    match i:
                        case 0:
                            r1 = rv
                        case 1:
                            r2 = rv
                        case 2:
                            r3 = rv
            else:
                if len(args) != len(fmt):
                    self.err(
                        ln, f"{mnem} expects {len(fmt)} operand(s), got {len(args)}"
                    )
                else:
                    for fi, a in zip(fmt, args):
                        match fi:
                            case "r":
                                rv = self.parseReg(a)
                                if rv is None:
                                    self.err(ln, f"Expected register: {a}")
                                    break
                                match rIdx:
                                    case 0:
                                        r1 = rv
                                    case 1:
                                        r2 = rv
                                    case 2:
                                        r3 = rv
                                rIdx += 1
                            case "i":
                                v = self.parseImm(a, ln)
                                if v is not None:
                                    imm = v

            self.out.extend(self.encInstr(op, r1, r2, r3, imm))
            self.pos += self.INSTRSZ

        return self.out

    def assemble(self, src: str) -> Optional[bytes]:
        # Two-pass assembly: source text → binary
        self.errs = []
        self.pass1(src)
        result = self.pass2(src)
        if self.errs:
            for e in self.errs:
                print(f"ASM ERROR: {e}", file=sys.stderr)
            return None
        return bytes(result)

    def asmFile(self, fPath: str) -> Optional[bytes]:
        # Assemble from source file
        with open(fPath, "r") as f:
            return self.assemble(f.read())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Unknown Runes ISA Assembler v1.0")
        print("Usage: python asmISA.py <source.asm> [-o output.rune]")
        sys.exit(0)

    srcPath = sys.argv[1]
    outPath = None

    # Parse -o flag
    if "-o" in sys.argv:
        oIdx = sys.argv.index("-o")
        if oIdx + 1 < len(sys.argv):
            outPath = sys.argv[oIdx + 1]

    if outPath is None:
        outPath = srcPath.rsplit(".", 1)[0] + ".rune"

    asm = UnknownRunesAsm()
    prog = asm.asmFile(srcPath)
    if prog is None:
        sys.exit(1)

    print(f"Assembled {len(prog)} bytes")

    with open(outPath, "wb") as f:
        f.write(prog)
    print(f"Written to {outPath}")
