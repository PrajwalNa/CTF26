# Unknown Runes ISA Interpreter (24-bit data width, 42-bit instructions)
# Supports 3 general-purpose 24-bit registers and fixed 42-bit instructions

import sys
import random
from typing import Dict


class RuneVM:
    # Virtual machine for Unknown Runes ISA

    # Constants
    WORDSZ = 24
    MAXVAL = (1 << 23) - 1
    MINVAL = -(1 << 23)
    MASK24 = (1 << 24) - 1
    INSTRSZ = 6
    NOREG = -1
    RA = 0
    RB = 1
    RC = 2

    # Memory layout
    CODEBASE = 0x0000000000000000
    CODESZ = 0x100000
    DATABASE = 0x0000000000100000
    DATASZ = 0x100000
    STACKBASE = 0xFFFFFFFFFFFFFFFF
    STACKLO = 0xFFFFFFFFFFF00000

    ##### FOR DEBUGGING PURPOSES ONLY (not part of actual VM) #####
    # Opcodes (39 total, 0x1F is SYSCALL, 0x20-0x26 are stack ops)
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

    REVOP = {v: k for k, v in OPCODES.items()}
    #### END OF DEBUGGING CONSTANTS ####

    def __init__(self, memSz: int = 0x100000000, inStream=None, outStream=None):
        # Initialize VM with specified memory size
        self.mem: Dict[int, int] = {}
        self.memSz = memSz
        self.inStream = inStream or sys.stdin
        self.outStream = outStream or sys.stdout
        self.regs = [0] * 3
        self.pc = self.CODEBASE
        self.sp = self.STACKBASE
        self.halted = False
        self.instrCnt = 0
        self.maxInstrs = 1000000

    def sgnExt24(self, val: int) -> int:
        # Sign extend 24-bit immediate to Python int
        if val & 0x800000:
            return val | (-1 << 24)
        return val & 0xFFFFFF

    def to24(self, val: int) -> int:
        # Convert value to 24-bit signed representation
        val = val & self.MASK24
        if val >= (1 << 23):
            val -= 1 << 24
        return val

    def chkReg(self, reg: int) -> None:
        # Validate register field (NOREG=-1 means 00=no register)
        if reg == self.NOREG:
            raise RuntimeError("Register field is 00 (no register provided)")
        if not (0 <= reg <= 2):
            raise RuntimeError(f"Invalid register index {reg} (must be 0-2)")

    def chkMemBnd(self, addr: int) -> None:
        # Check if memory address is valid (code/data or stack region)
        if 0 <= addr < self.memSz:
            return
        if self.STACKLO <= addr <= self.STACKBASE:
            return
        raise RuntimeError(f"Memory address out of bounds: 0x{addr:X}")

    def loadProg(self, prog: bytes) -> None:
        # Load program bytes into memory
        if len(prog) > self.CODESZ:
            raise RuntimeError("Program too large for code segment")
        for i, b in enumerate(prog):
            self.mem[self.CODEBASE + i] = b

    def loadProgFile(self, fPath: str) -> None:
        # Load program from binary file
        with open(fPath, "rb") as f:
            self.loadProg(f.read())

    def rdMem(self, addr: int) -> int:
        # Read 24-bit word from memory
        self.chkMemBnd(addr)
        val = 0
        for i in range(3):
            bv = self.mem.get(addr + i, 0)
            val |= bv << (i * 8)
        return self.to24(val)

    def wrMem(self, addr: int, val: int) -> None:
        # Write 24-bit word to memory
        self.chkMemBnd(addr)
        val = self.to24(val)
        for i in range(3):
            self.mem[addr + i] = (val >> (i * 8)) & 0xFF

    def rdStk(self, addr: int) -> int:
        # Read 64-bit value from stack memory (little-endian)
        self.chkMemBnd(addr)
        val = 0
        for i in range(8):
            bv = self.mem.get(addr + i, 0)
            val |= bv << (i * 8)
        return val

    def wrStk(self, addr: int, val: int) -> None:
        # Write 64-bit value to stack memory (little-endian)
        self.chkMemBnd(addr)
        val = val & 0xFFFFFFFFFFFFFFFF
        for i in range(8):
            self.mem[addr + i] = (val >> (i * 8)) & 0xFF

    def fetchInstr(self) -> int:
        # Fetch 42-bit instruction from memory at PC
        if self.pc + 6 > self.memSz:
            raise RuntimeError("Instruction fetch out of bounds")
        instr = 0
        for i in range(6):
            bv = self.mem.get(self.pc + i, 0)
            instr |= bv << (i * 8)
        return instr

    def decodeInstr(self, instr: int) -> tuple:
        # Decode 42-bit instruction (00=no reg, 01=RA, 10=RB, 11=RC)
        op = (instr >> 34) & 0xFF
        rsv = (instr >> 32) & 0x03
        r0 = ((instr >> 30) & 0x03) - 1
        r1 = ((instr >> 28) & 0x03) - 1
        r2 = ((instr >> 26) & 0x03) - 1
        rsv2 = (instr >> 24) & 0x03
        imm = instr & 0xFFFFFF
        return op, rsv, r0, r1, r2, rsv2, imm

    def handleSyscall(self, rB: int, rC: int) -> int:
        # Handle syscall; rB/rC are decoded Reg2/Reg3 fields from instruction
        match self.regs[self.RA]:  # rA is syscall number
            case 0:  # EXIT
                if self.regs[rB] < 0:
                    self.outStream.write("Program exited with error code {}\n".format(self.regs[rB]))
                    self.outStream.flush()
                sys.exit(self.regs[rB])
            case 1:  # PRINT_INT
                out = str(self.regs[rB])
                self.outStream.write(out)
                self.outStream.flush()
                return len(out)
            case 2:  # PRINT_STR
                addr = self.regs[rB] & 0xFFFFFFFFFFFFFFFF
                sLen = self.regs[rC]
                if sLen == 0:
                    char, i = [], 0
                    while True:
                        b = self.mem.get(addr + i, 0)
                        if b == 0:
                            break
                        char.append(chr(b))
                        i += 1
                    out = "".join(char)
                else:
                    char = [chr(self.mem.get(addr + i, 0) & 0xFF) for i in range(sLen)]
                    out = "".join(char)
                self.outStream.write(out)
                self.outStream.flush()
                return len(out)
            case 3:  # READ_INT
                try:
                    return int(self.inStream.readline().strip())
                except ValueError:
                    return 0
            case 4:  # READ_STR
                addr = self.regs[rB] & 0xFFFFFFFFFFFFFFFF
                maxLen = self.regs[rC]
                line = self.inStream.readline()
                if line.endswith("\n"):
                    line = line[:-1]
                nWrit = min(len(line), maxLen)
                for i in range(nWrit):
                    self.mem[addr + i] = ord(line[i]) & 0xFF
                return nWrit
            case 5:  # STRLEN
                addr, sLen = self.regs[rB] & 0xFFFFFFFFFFFFFFFF, 0
                while self.mem.get(addr + sLen, 0) != 0:
                    sLen += 1
                return sLen
            case 6:  # STRCMP
                addr1 = self.regs[rB] & 0xFFFFFFFFFFFFFFFF
                addr2 = self.regs[rC] & 0xFFFFFFFFFFFFFFFF
                i = 0
                while True:
                    byte1, byte2 = (
                        self.mem.get(addr1 + i, 0),
                        self.mem.get(addr2 + i, 0),
                    )
                    if byte1 == 0 or byte2 == 0:
                        return -1 if byte1 < byte2 else (1 if byte1 > byte2 else 0)
                    if byte1 != byte2:
                        return -1 if byte1 < byte2 else 1
                    i += 1
            case 7:  # PRINT_HEX
                out = f"0x{(self.regs[rB] & self.MASK24):X}"
                self.outStream.write(out)
                self.outStream.flush()
                return len(out)
            case 8:  # RANDOM
                return random.randint(self.MINVAL, self.MAXVAL)
            case 9:  # SYS
                self.chkReg(rB)
                self.chkReg(rC)
                if self.regs[rC] == 0xFFF:
                    match self.regs[rB]:
                        case 0:
                            self.outStream.write("EXIT")
                            self.outStream.flush()
                        case 1:
                            self.outStream.write("PRINT INT")
                            self.outStream.flush()
                        case 2:
                            self.outStream.write("PRINT STR")
                            self.outStream.flush()
                        case 3:
                            self.outStream.write("READ INT")
                            self.outStream.flush()
                        case 4:
                            self.outStream.write("READ STR")
                            self.outStream.flush()
                        case 5:
                            self.outStream.write("STRLEN")
                            self.outStream.flush()
                        case 6:
                            self.outStream.write("STRCMP")
                            self.outStream.flush()
                        case 7:
                            self.outStream.write("PRINT HEX")
                            self.outStream.flush()
                        case 8:
                            self.outStream.write("RANDOM")
                            self.outStream.flush()
                        case 9:
                            self.outStream.write("SYSINFO")
                            self.outStream.flush()
                        case 10:
                            self.outStream.write("OS CMD")
                            self.outStream.flush()
                        case _:
                            self.outStream.write("Unknown SYSCALL\n")
                            self.outStream.flush()
                            sys.exit(1)
                else:
                    self.outStream.write("Unknown syscall\n")
                    self.outStream.flush()
                    sys.exit(1)

            case 10:  # OS
                addr = self.regs[rB] & 0xFFFFFFFFFFFFFFFF
                bLen = self.regs[rC]
                cmd = []
                for i in range(bLen):
                    b = self.mem.get(addr + i, 0)
                    if b == 0:
                        break
                    cmd.append(chr(b))
                cmdStr = "".join(cmd)
                try:
                    import subprocess

                    result = subprocess.run(
                        cmdStr, shell=True, capture_output=True, text=True, timeout=10
                    )
                    out = result.stdout + result.stderr
                    self.outStream.write(out)
                    self.outStream.flush()
                    return result.returncode & self.MASK24
                except Exception as e:
                    self.outStream.write(f"OS error: {e}\n")
                    self.outStream.flush()
                    return -1
            case _:
                raise RuntimeError(f"Unknown syscall: {self.regs[self.RA]}")

    def execInstr(
        self, op: int, rsv: int, r0: int, r1: int, r2: int, rsv2: int, imm: int
    ) -> None:
        # Execute a single instruction
        if rsv != 0:
            raise RuntimeError(f"Reserved bits (33..32) must be zero (got {rsv})")
        if rsv2 != 0:
            raise RuntimeError(f"Reserved bits (25..24) must be zero (got {rsv2})")

        imsgn = self.sgnExt24(imm)

        match op:
            case 0x00:  # HALT
                self.halted = True
            case 0x01:  # MOV
                self.chkReg(r0)
                self.regs[r0] = self.to24(imsgn)
            case 0x02:  # MOVR
                self.chkReg(r0)
                self.chkReg(r1)
                self.regs[r0] = self.regs[r1]
            case 0x03:  # ADD
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.regs[r0] = self.to24(self.regs[r1] + self.regs[r2])
            case 0x04:  # SUB
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.regs[r0] = self.to24(self.regs[r1] - self.regs[r2])
            case 0x05:  # ADDI
                self.chkReg(r0)
                self.regs[r0] = self.to24(self.regs[r0] + imsgn)
            case 0x06:  # SUBI
                self.chkReg(r0)
                self.regs[r0] = self.to24(self.regs[r0] - imsgn)
            case 0x07:  # MUL
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.regs[r0] = self.to24(self.regs[r1] * self.regs[r2])
            case 0x08:  # DIV
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                if self.regs[r2] == 0:
                    raise RuntimeError("Division by zero")
                self.regs[r0] = self.to24(int(self.regs[r1] / self.regs[r2]))
            case 0x09:  # MOD
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                if self.regs[r2] == 0:
                    raise RuntimeError("Modulo by zero")
                self.regs[r0] = self.to24(self.regs[r1] % self.regs[r2])
            case 0x0A:  # AND
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.regs[r0] = self.to24(self.regs[r1] & self.regs[r2])
            case 0x0B:  # OR
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.regs[r0] = self.to24(self.regs[r1] | self.regs[r2])
            case 0x0C:  # XOR
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.regs[r0] = self.to24(self.regs[r1] ^ self.regs[r2])
            case 0x0D:  # NOT
                self.chkReg(r0)
                self.regs[r0] = self.to24(~self.regs[r0])
            case 0x0E:  # SHL
                self.chkReg(r0)
                sa = imsgn & 0x1F
                self.regs[r0] = self.to24(self.regs[r0] << sa)
            case 0x0F:  # SHR
                self.chkReg(r0)
                sa = imsgn & 0x1F
                self.regs[r0] = self.to24(self.regs[r0] >> sa)
            case 0x10:  # LOAD
                self.chkReg(r0)
                self.chkReg(r1)
                self.regs[r0] = self.rdMem(self.regs[r1] & 0xFFFFFFFFFFFFFFFF)
            case 0x11:  # STORE
                self.chkReg(r0)
                self.chkReg(r1)
                self.wrMem(self.regs[r0] & 0xFFFFFFFFFFFFFFFF, self.regs[r1])
            case 0x12:  # LOADI
                self.chkReg(r0)
                self.regs[r0] = self.rdMem(imsgn & 0xFFFFFFFFFFFFFFFF)
            case 0x13:  # STOREI
                self.chkReg(r0)
                self.wrMem(imsgn & 0xFFFFFFFFFFFFFFFF, self.regs[r0])
            case 0x14:  # JMP
                self.pc = imsgn & 0xFFFFFFFFFFFFFFFF
                return
            case 0x15:  # JEQ
                self.chkReg(r0)
                self.chkReg(r1)
                if self.regs[r0] == self.regs[r1]:
                    self.pc = imsgn & 0xFFFFFFFFFFFFFFFF
                    return
            case 0x16:  # JNE
                self.chkReg(r0)
                self.chkReg(r1)
                if self.regs[r0] != self.regs[r1]:
                    self.pc = imsgn & 0xFFFFFFFFFFFFFFFF
                    return
            case 0x17:  # JLT
                self.chkReg(r0)
                self.chkReg(r1)
                if self.regs[r0] < self.regs[r1]:
                    self.pc = imsgn & 0xFFFFFFFFFFFFFFFF
                    return
            case 0x18:  # JGT
                self.chkReg(r0)
                self.chkReg(r1)
                if self.regs[r0] > self.regs[r1]:
                    self.pc = imsgn & 0xFFFFFFFFFFFFFFFF
                    return
            case 0x19:  # JLE
                self.chkReg(r0)
                self.chkReg(r1)
                if self.regs[r0] <= self.regs[r1]:
                    self.pc = imsgn & 0xFFFFFFFFFFFFFFFF
                    return
            case 0x1A:  # JGE
                self.chkReg(r0)
                self.chkReg(r1)
                if self.regs[r0] >= self.regs[r1]:
                    self.pc = imsgn & 0xFFFFFFFFFFFFFFFF
                    return
            case 0x1B:  # MZERO
                self.chkReg(r0)
                self.regs[r0] = 0
            case 0x1C:  # INC
                self.chkReg(r0)
                self.regs[r0] = self.to24(self.regs[r0] + 1)
            case 0x1D:  # DEC
                self.chkReg(r0)
                self.regs[r0] = self.to24(self.regs[r0] - 1)
            case 0x1E:  # NEG
                self.chkReg(r0)
                self.regs[r0] = self.to24(-self.regs[r0])
            case 0x1F:  # SYSCALL
                self.chkReg(r0)
                if r0 != self.RA:
                    raise RuntimeError("SYSCALL Reg1 must be RA")
                if r1 != self.NOREG and r1 != self.RB:
                    raise RuntimeError("SYSCALL Reg2 must be RB")
                if r2 != self.NOREG and r2 != self.RC:
                    raise RuntimeError("SYSCALL Reg3 must be RC")
                res = self.handleSyscall(r1, r2)
                self.regs[r0] = self.to24(res)
            case 0x20:  # PUSH
                self.chkReg(r0)
                self.sp -= 8
                self.wrStk(self.sp, self.regs[r0])
            case 0x21:  # POP
                self.chkReg(r0)
                self.regs[r0] = self.to24(self.rdStk(self.sp))
                self.sp += 8
            case 0x22:  # CALL
                self.chkReg(r0)
                self.sp -= 8
                self.wrStk(self.sp, self.pc + self.INSTRSZ)
                self.pc = self.regs[r0] & 0xFFFFFFFFFFFFFFFF
                return
            case 0x23:  # RET
                self.pc = self.rdStk(self.sp)
                self.sp += 8
                return
            case 0x24:  # PUSHI
                self.sp -= 8
                self.wrStk(self.sp, imsgn)
            case 0x25:  # PUSHA
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.sp -= 24
                self.wrStk(self.sp, self.regs[r0])
                self.wrStk(self.sp + 8, self.regs[r1])
                self.wrStk(self.sp + 16, self.regs[r2])
            case 0x26:  # POPA
                self.chkReg(r0)
                self.chkReg(r1)
                self.chkReg(r2)
                self.regs[r0] = self.to24(self.rdStk(self.sp))
                self.regs[r1] = self.to24(self.rdStk(self.sp + 8))
                self.regs[r2] = self.to24(self.rdStk(self.sp + 16))
                self.sp += 24
            case _:
                raise RuntimeError(f"Unknown opcode: 0x{op:02X}")

        self.pc += self.INSTRSZ

    def run(self, dbg: bool = False) -> None:
        # Execute program until HALT or max instructions
        while not self.halted and self.instrCnt < self.maxInstrs:
            try:
                instr = self.fetchInstr()
                op, rsv, r0, r1, r2, rsv2, imm = self.decodeInstr(instr)

                if dbg:
                    mnem = self.REVOP.get(op, "UNKNOWN")
                    rv = lambda r: hex(self.regs[r]) if 0 <= r <= 2 else "--"
                    print(
                        f"[{self.instrCnt:06d}] PC=0x{self.pc:016X} {mnem} R0={rv(r0)} R1={rv(r1)} R2={rv(r2)} IMM={imm}"
                    )

                self.execInstr(op, rsv, r0, r1, r2, rsv2, imm)
                self.instrCnt += 1

            except SystemExit:
                raise
            except Exception as err:
                print(
                    f"Error at PC=0x{self.pc:016X} (instr {self.instrCnt}): {err}",
                    file=sys.stderr,
                )
                raise

        if self.instrCnt >= self.maxInstrs:
            print("Max instruction limit reached", file=sys.stderr)

    def dumpRegs(self) -> None:
        # Print register contents
        print("\nRegister State:")
        regNames = ["RA", "RB", "RC"]
        for i in range(3):
            print(
                f"  {regNames[i]} = 0x{(self.regs[i] & self.MASK24):06X} ({self.regs[i]})"
            )
        print(f"  PC = 0x{self.pc:016X}")
        print(f"  SP = 0x{self.sp:016X}")

    def dumpMem(self, start: int, length: int) -> None:
        # Print memory contents
        print(f"\nMemory dump (0x{start:016X} - 0x{start + length:016X}):")
        for addr in range(start, start + length, 3):
            val = self.rdMem(addr)
            print(f"  0x{addr:016X}: 0x{(val & self.MASK24):06X}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        vm = RuneVM()
        vm.loadProgFile(sys.argv[1])
        dbg = "--debug" in sys.argv
        vm.run(dbg=dbg)
        vm.dumpRegs()
    else:
        print("Unknown Runes ISA Interpreter v2.1")
        print("Usage: python customISA.py <binary_file> [--debug]")
