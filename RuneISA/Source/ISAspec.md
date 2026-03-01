# Rune ISA Spec (42-bit)

This is the instruction set used in the 'Unknown Runes' & 'A Dark Legacy' challenges.

## Registers
- `RA` - general purpose (24-bit signed)
- `RB` - general purpose (24-bit signed)
- `RC` - general purpose (24-bit signed)
- `PC` - program counter (64-bit)
- `SP` - stack pointer (64-bit)


## Instruction Encoding (42 bits)
```
Bits 41..34 : Opcode    (8 bits)
Bits 33..32 : Reserved  (2 bits, must be 0)
Bits 31..30 : Reg1      (2 bits)
Bits 29..28 : Reg2      (2 bits)
Bits 27..26 : Reg3      (2 bits)
Bits 25..24 : Reserved  (2 bits, must be 0)
Bits 23..0  : Immediate (24-bit signed)
```
| Byte 0 | Byte 1 | Byte 2 | Byte 3              | Byte 4                      | Byte 5                   |
| ------ | ------ | ------ | ------------------- | --------------------------- | ------------------------ |
| IMM    | IMM    | IMM    | REG                 | RSRV + Part of OPCODE       | Part of OPCODE + RSRV    |
|        |        |        | Reg1-Reg2-Reg3-Resv | (RSRV)00(RSRV) (STRT)000000 | 00(END) (RSRV)0000(RSRV) |
NOTE: Above is how the instruction would appear in hex editor.

### Register Encoding
| Bits | Meaning              |
| ---- | -------------------- |
| `00` | No register (unused) |
| `01` | RA                   |
| `10` | RB                   |
| `11` | RC                   |

A `00` in a register field means that field is not used by the instruction.
If an instruction requires a register in a given field and the field is `00`,
the VM raises a runtime error.

Any register (RA, RB, RC) can be placed in any of the three field positions (Reg1, Reg2, Reg3).
The opcode determines which fields are meaningful.


## Opcode Reference
| Op   | Mnemonic | Reg1      | Reg2      | Reg3      | Imm  | Meaning                                                         |
| ---- | -------- | --------- | --------- | --------- | ---- | --------------------------------------------------------------- |
| 0x00 | HALT     | -         | -         | -         | -    | Stop execution                                                  |
| 0x01 | MOV      | dst       | -         | -         | val  | `Reg1 = Imm` (sign extended)                                    |
| 0x02 | MOVR     | dst       | src       | -         | -    | `Reg1 = Reg2`                                                   |
| 0x03 | ADD      | dst       | src2      | src1      | -    | `Reg1 = Reg2 + Reg3`                                            |
| 0x04 | SUB      | dst       | src2      | src1      | -    | `Reg1 = Reg2 - Reg3`                                            |
| 0x05 | ADDI     | acc       | -         | -         | val  | `Reg1 += sign_ext(Imm)`                                         |
| 0x06 | SUBI     | acc       | -         | -         | val  | `Reg1 -= sign_ext(Imm)`                                         |
| 0x07 | MUL      | dst       | src2      | src1      | -    | `Reg1 = Reg2 * Reg3`                                            |
| 0x08 | DIV      | dst       | src2      | src1      | -    | `Reg1 = Reg2 / Reg3` (integer, truncated toward zero)           |
| 0x09 | MOD      | dst       | src2      | src1      | -    | `Reg1 = Reg2 % Reg3`                                            |
| 0x0A | AND      | dst       | src2      | src1      | -    | `Reg1 = Reg2 & Reg3` (bitwise AND)                              |
| 0x0B | OR       | dst       | src2      | src1      | -    | `Reg1 = Reg2 \| Reg3` (bitwise OR)                              |
| 0x0C | XOR      | dst       | src2      | src1      | -    | `Reg1 = Reg2 ^ Reg3`                                            |
| 0x0D | NOT      | acc       | -         | -         | -    | `Reg1 = ~Reg1` (bitwise NOT)                                    |
| 0x0E | SHL      | acc       | -         | -         | amt  | `Reg1 = Reg1 << (Imm & 0x1F)`                                   |
| 0x0F | SHR      | acc       | -         | -         | amt  | `Reg1 = Reg1 >> (Imm & 0x1F)`                                   |
| 0x10 | LOAD     | dst       | addr      | -         | -    | `Reg1 = MEM[Reg2]`                                              |
| 0x11 | STORE    | addr      | val       | -         | -    | `MEM[Reg1] = Reg2`                                              |
| 0x12 | LOADI    | dst       | -         | -         | addr | `Reg1 = MEM[Imm]` (sign extended)                               |
| 0x13 | STOREI   | val       | -         | -         | addr | `MEM[Imm] = Reg1` (sign extended)                               |
| 0x14 | JMP      | -         | -         | -         | tgt  | `PC = Imm` (unconditional)                                      |
| 0x15 | JEQ      | cmp1      | cmp2      | -         | tgt  | if `Reg1 == Reg2` then `PC = Imm`                               |
| 0x16 | JNE      | cmp1      | cmp2      | -         | tgt  | if `Reg1 != Reg2` then `PC = Imm`                               |
| 0x17 | JLT      | cmp1      | cmp2      | -         | tgt  | if `Reg1 < Reg2` then `PC = Imm` (signed)                       |
| 0x18 | JGT      | cmp1      | cmp2      | -         | tgt  | if `Reg1 > Reg2` then `PC = Imm` (signed)                       |
| 0x19 | JLE      | cmp1      | cmp2      | -         | tgt  | if `Reg1 <= Reg2` then `PC = Imm` (signed)                      |
| 0x1A | JGE      | cmp1      | cmp2      | -         | tgt  | if `Reg1 >= Reg2` then `PC = Imm` (signed)                      |
| 0x1B | MZERO    | dst       | -         | -         | -    | `Reg1 = 0`                                                      |
| 0x1C | INC      | acc       | -         | -         | -    | `Reg1 += 1`                                                     |
| 0x1D | DEC      | acc       | -         | -         | -    | `Reg1 -= 1`                                                     |
| 0x1E | NEG      | acc       | -         | -         | -    | `Reg1 = -Reg1` (2's complement)                                 |
| 0x1F | SYSCALL  | sysN (RA) | arg1 (RB) | arg2 (RC) | -    | Invoke syscall (see below)                                      |
| 0x20 | PUSH     | val       | -         | -         | -    | `SP -= 8; MEM[SP] = sign_ext(Reg1)`                             |
| 0x21 | POP      | dst       | -         | -         | -    | `Reg1 = MEM[SP]; SP += 8`                                       |
| 0x22 | CALL     | tgt       | -         | -         | -    | `SP -= 8; MEM[SP] = PC + 6; PC = Reg1`                          |
| 0x23 | RET      | -         | -         | -         | -    | `PC = MEM[SP]; SP += 8`                                         |
| 0x24 | PUSHI    | -         | -         | -         | addr | `SP -= 8; MEM[SP] = sign_ext(Imm)`                              |
| 0x25 | PUSHA    | val       | val       | val       | -    | `SP -= 24; MEM[SP] = Reg1; MEM[SP+8] = Reg2; MEM[SP+16] = Reg3` |
| 0x26 | POPA     | dst1      | dst2      | dst3      | -    | `Reg1 = MEM[SP]; Reg2 = MEM[SP+8]; Reg3 = MEM[SP+16]; SP += 24` |
Fields marked `-` are don't care and should be encoded as `00` / `0`.

#### Notes
- Conditional jumps: if the condition is false, execution falls through (`PC` advances normally).
- SHL/SHR: shift amount is masked to 5 bits (max 31), taken from the immediate field.
- All arithmetic wraps in 24-bit signed space.


## Syscalls
`SYSCALL` uses the instruction's register fields as follows:
- RegA: holds the syscall number, then overwritten with the return value (output)
- `SYSCALL RA, RB, RC`

The registers (RA, RB, RC) can only be placed in the field marked for it.

| ID  | Name      | RegB (arg1) | RegC (arg2) | Return (in RegA)          |
| --- | --------- | ----------- | ----------- | ------------------------- |
| 0   | EXIT      | exit code   | -           | (does not return)         |
| 1   | PRINT_INT | value       | -           | bytes written             |
| 2   | PRINT_STR | addr        | length      | bytes written             |
| 3   | READ_INT  | -           | -           | parsed integer            |
| 4   | READ_STR  | buffer addr | max len     | bytes read                |
| 5   | STRLEN    | string addr | -           | string length             |
| 6   | STRCMP    | addr1       | addr2       | `-1`, `0`, or `1`         |
| 7   | PRINT_HEX | value       | -           | bytes written             |
| 8   | RANDOM    | -           | -           | random 24-bit value       |
| 9   | SYS       | NUM         | `0xFFF`     | syscall-specific behavior |
| 10  | OS        | buf addr    | buf len     | os command execute        |

#### PRINT_STR detail
- If length (RegC) is 0, the string is read until a null byte (`0x00`).

#### READ_STR detail (specifc to 'A Dark Legacy')
- Usually provides buffer overflow protection by only reading up to the provided max length (RegC).
- However, for the purposes of the challenge, the protection is disabled.


## Value Ranges
- Registers: signed 24-bit (`-2^23` to `2^23 - 1`)
- Immediate field: signed 24-bit (`-8,388,608` to `8,388,607`)
- Memory address: unsigned 64-bit
- Instruction alignment: 6-byte boundaries (42 logical bits stored in 6-byte little-endian slots, top 6 bits unused)


## Memory Layout
```
0xFFFFFFFFFFFFFFFF - 0xFFFFFFFFFFF00000 : Stack (grows downward)
0x00000000001FFFFF - 0x0000000000100000 : Data (1 MB)
0x00000000000FFFFF - 0x0000000000000000 : Code (1 MB)
```


## Execution Flow
1. Start with `PC = 0x0000000000000000`.
2. Fetch 6 bytes at `PC` (little-endian → 48-bit value, top 6 bits ignored → 42 logical bits).
3. Decode opcode, register fields, and immediate.
4. Execute.
5. If the instruction did not modify `PC` (no taken jump): `PC += 6`.
6. If the instruction was a taken jump: `PC` is set to the jump target directly.
7. Repeat until `HALT` or a runtime error occurs.


## Runtime Constraints / Errors
- Division by zero -> runtime error
- Register field is `00` where a register is required -> runtime error
- Invalid memory access -> runtime error
- Arithmetic overflow wraps in 24-bit signed space
- Unknown opcode (not in `0x00..0x26`) -> runtime error