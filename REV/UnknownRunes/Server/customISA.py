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

    # Memory layout
    CODEBASE = 0x0000000000000000
    CODESZ = 0x100000
    DATABASE = 0x0000000000100000
    DATASZ = 0x100000
    STACKBASE = 0xFFFFFFFFFFFFFFFF
    STACKLO = 0xFFFFFFFFFFF00000

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
            raise RuntimeError(f"Invalid register index {reg}")

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

    def handleSyscall(self, rA: int, rB: int, rC: int) -> int:
        # Handle syscall, rB/rC are register indices from Reg2/Reg3 fields
        match rA:
            case 0:  # EXIT
                self.chkReg(rB)
                sys.exit(self.regs[rB])
            case 1:  # PRINT_INT
                self.chkReg(rB)
                out = str(self.regs[rB])
                self.outStream.write(out)
                self.outStream.flush()
                return len(out)
            case 2:  # PRINT_STR
                self.chkReg(rB)
                self.chkReg(rC)
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
                self.chkReg(rB)
                self.chkReg(rC)
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
                self.chkReg(rB)
                addr, sLen = self.regs[rB] & 0xFFFFFFFFFFFFFFFF, 0
                while self.mem.get(addr + sLen, 0) != 0:
                    sLen += 1
                return sLen
            case 6:  # STRCMP
                self.chkReg(rB)
                self.chkReg(rC)
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
                self.chkReg(rB)
                out = f"0x{(self.regs[rB] & self.MASK24):X}"
                self.outStream.write(out)
                self.outStream.flush()
                return len(out)
            case 8:  # RANDOM
                return random.randint(self.MINVAL, self.MAXVAL)
            case 9:  # SYS
                pass
            case 10:
                pass
            case _:
                raise RuntimeError(f"Unknown syscall: {rA}")

    def execInstr(
        self, op: int, rsv: int, r0: int, r1: int, r2: int, rsv2: int, imm: int
    ) -> None:
        # Execute a single instruction
        if rsv != 0:
            raise RuntimeError(f"Reserved bits must be zero")
        if rsv2 != 0:
            raise RuntimeError(f"Reserved bits must be zero")

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
                self.regs[r0] = self.to24(-self.regs[r0])
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
                self.regs[r0] = self.to24(~self.regs[r0])
            case 0x1F:  # SYSCALL
                self.chkReg(r0)
                rA = self.regs[r0]
                res = self.handleSyscall(rA, r1, r2)
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
                raise RuntimeError(f"Unknown")

        self.pc += self.INSTRSZ

    def run(self, dbg: bool = False) -> None:
        # Execute program until HALT or max instructions
        while not self.halted and self.instrCnt < self.maxInstrs:
            try:
                instr = self.fetchInstr()
                op, rsv, r0, r1, r2, rsv2, imm = self.decodeInstr(instr)
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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        vm = RuneVM()
        vm.loadProgFile(sys.argv[1])
        vm.run()
        vm.dumpRegs()
    else:
        print("Unknown Runes ISA Interpreter v2.1")
        print("Usage: python customISA.py <binary_file>")
