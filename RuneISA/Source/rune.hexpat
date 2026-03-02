// ============================================================
// Rune ISA — ImHex Pattern (.hexpat)
// Decodes .rune binaries as 6-byte instruction slots
// Approach A: fixed grid, invalid slots flagged as [DATA]
// ============================================================

#pragma description Rune ISA Binary (.rune)
#pragma endian little
#pragma pattern_limit 200000

import std.mem;
import std.string;

// ─── Opcode lookup ───

fn opname(u8 op) {
    if (op == 0x00) return "HALT";
    if (op == 0x01) return "MOV";
    if (op == 0x02) return "MOVR";
    if (op == 0x03) return "ADD";
    if (op == 0x04) return "SUB";
    if (op == 0x05) return "ADDI";
    if (op == 0x06) return "SUBI";
    if (op == 0x07) return "MUL";
    if (op == 0x08) return "DIV";
    if (op == 0x09) return "MOD";
    if (op == 0x0A) return "AND";
    if (op == 0x0B) return "OR";
    if (op == 0x0C) return "XOR";
    if (op == 0x0D) return "NOT";
    if (op == 0x0E) return "SHL";
    if (op == 0x0F) return "SHR";
    if (op == 0x10) return "LOAD";
    if (op == 0x11) return "STORE";
    if (op == 0x12) return "LOADI";
    if (op == 0x13) return "STOREI";
    if (op == 0x14) return "JMP";
    if (op == 0x15) return "JEQ";
    if (op == 0x16) return "JNE";
    if (op == 0x17) return "JLT";
    if (op == 0x18) return "JGT";
    if (op == 0x19) return "JLE";
    if (op == 0x1A) return "JGE";
    if (op == 0x1B) return "MZERO";
    if (op == 0x1C) return "INC";
    if (op == 0x1D) return "DEC";
    if (op == 0x1E) return "NEG";
    if (op == 0x1F) return "SYSCALL";
    if (op == 0x20) return "PUSH";
    if (op == 0x21) return "POP";
    if (op == 0x22) return "CALL";
    if (op == 0x23) return "RET";
    if (op == 0x24) return "PUSHI";
    if (op == 0x25) return "PUSHA";
    if (op == 0x26) return "POPA";
    return "???";
};

// ─── Register lookup ───

fn regname(u8 r) {
    if (r == 1) return "RA";
    if (r == 2) return "RB";
    if (r == 3) return "RC";
    return "__";
};

// ─── Format function ───
// Reads named bitfield members, decodes the instruction.
// If reserved/unused bits are non-zero or opcode is out of range,
// the slot is flagged as [DATA].

fn fmtRune(ref auto slot) {
    // ── Validity check ──
    if (slot.unused != 0 || slot.rsv1 != 0 || slot.rsv2 != 0 || slot.opcode > 0x26)
        return "[DATA]";

    // Sign-extend 24-bit immediate to 32-bit signed
    u32 imm = slot.imm;
    s32 simm = imm;
    if (imm & 0x800000) simm = s32(imm | 0xFF000000);

    // ── Format output ──
    return std::format("{} {}, {}, {},  {}",
        opname(slot.opcode), regname(slot.reg1), regname(slot.reg2), regname(slot.reg3), simm);
};

// ─── Instruction bitfield (6 bytes = 48 bits, little-endian) ───
// Fields declared MSB -> LSB of the LE 48-bit integer.
// Each field gets its own color in the hex view.
//
//   Opcode  = red        Reserved = grey
//   Reg1    = green      Reg2     = blue
//   Reg3    = yellow     Immediate = purple
//   Unused  = dark grey

bitfield RuneSlot {
    imm    : 24 [[color("CC77FF")]];   // bits 23..0  — immediat
    rsv2   : 2  [[color("808080")]];   // bits 25..24 — reserved
    reg3   : 2  [[color("FFDD66")]];   // bits 27..26 — Reg3
    reg2   : 2  [[color("6699FF")]];   // bits 29..28 — Reg2
    reg1   : 2  [[color("66FF66")]];   // bits 31..30 — Reg1
    rsv1   : 2  [[color("808080")]];   // bits 33..32 — reserved
    opcode : 8  [[color("FF6666")]];   // bits 41..34 — opcode
    unused : 6  [[color("404040")]];   // bits 47..42 — must be 0
} [[format("fmtRune")]];

// Parse entire file as 6-byte slots (ignore trailing bytes < 6)
RuneSlot slots[std::mem::size() / 6] @ 0x00;
