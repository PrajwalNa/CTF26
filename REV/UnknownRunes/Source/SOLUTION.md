# Unknown Runes — Solution

## Challenge Summary

Players connect to a remote TCP server (port 666) and receive `journey.rune`, a compiled binary for a custom ISA. The binary runs a text-based RPG with 4 character paths. Two paths (Mage, Artificer) contain flags locked behind answer prompts, only Mage flag is valid. The other two (Warrior, Bard) are dead ends.

Players must reverse engineer the unknown instruction set, identify the XOR encryption, extract the answers, and play through the correct paths to capture the flags.

---

## Answers

| Path      | Answer                                        | XOR Key                           |
| --------- | --------------------------------------------- | --------------------------------- |
| Mage      | `I seek the p0wer of the dark 0ne: NOSFERATU` | `0x44A0CF` (`[0xCF, 0xA0, 0x44]`) |
| Artificer | `resonance=core.tune:phase_314`               | `0xAFCEFA` (`[0xFA, 0xCE, 0xAF]`) |

## Flags

| Path      | Flag                                    | Steps                                                                                |
| --------- | --------------------------------------- | ------------------------------------------------------------------------------------ |
| Mage      | `{Hack3rs_Ar3_T3chinically_Dark_Mag3s}` | Choose Mage -> Ruins -> defeat spirit -> enter answer -> choose dark path (option 2) |
| Artificer | `{Artificer_Fl4g_1s_Res0n4nting@42}`    | Choose Artificer -> fix golem core -> enter answer  (Fake Flag)                      |


---

## Encryption Details

Three separate XOR keys are used. All operate on 3-byte (24-bit) words, matching the LOAD/STORE width of the ISA.

| Purpose                  | Key (LE word) | Key (bytes)                   |
| ------------------------ | ------------- | ----------------------------- |
| All printed game strings | `0x1FF1AD`    | `[0xAD, 0xF1, 0x1F]` (ADF11F) |
| Mage answer              | `0x44A0CF`    | `[0xCF, 0xA0, 0x44]` (CFA044) |
| Artificer answer         | `0xAFCEFA`    | `[0xFA, 0xCE, 0xAF]` (FACEAF) |
| Mage flag                | `0x46534E`    | `[0x4E, 0x53, 0x46]` (4E5346) |
| Artificer flag           | `0xAFAD0B`    | `[0x0B, 0xAD, 0xAF]` (0BADAF) |

**string encryption**: `fn_print` decrypts most game strings in-place with `0x1FF1AD`, prints via SYSCALL, then re-encrypts. Strings are never in cleartext at rest.

**answer encryption**: The caller stores the flag/answer specific key to memory address `0x10001E` before calling `fn_check_answer`. The function reads the key from that address, decrypts the expected answer, and compares it to user input via STRCMP syscall. The answer keys are only visible in the code flow leading up to each check (no global reference).

---

## Intended Solve Path

1. Connect to the server and play all four paths to map the game structure. Notice that only Mage and Artificer have input prompts.

2. Observe 6-byte repeating structure in the hex dump. Determine instructions are 6-byte LE slots.
   * They'll need to decrypt the opcode a bit differently since the first 2 bits of the byte are reserved and thus 0, the opcode is split between byte 5 & 6, the instruction format is:

        | Byte 1 | Byte 2 | Byte 3 | Byte 4              | Byte 5                      | Byte 6                   |
        | ------ | ------ | ------ | ------------------- | --------------------------- | ------------------------ |
        | IMM    | IMM    | IMM    | REG                 | RSRV + Part of OPCODE       | Part of OPCODE + RSRV    |
        |        |        |        | Reg1-Reg2-Reg3-Resv | (RSRV)00(RSRV) (STRT)000000 | 00(END) (RSRV)0000(RSRV) |

3. Work out the bitfield layout: 8-bit opcode, register fields, 24-bit immediate. Map key opcodes (MOV, XOR, LOAD, STORE, JMP, CALL, SYSCALL).

4. `fn_print` contains a hardcoded `MOV RA, 0x1FF1AD` followed by an XOR loop. This is the easiest key to find.

5. Scan for where valid opcodes end (nothing above `0x26`). XOR-decrypt everything past that boundary with `0x1FF1AD`. All game text comes out clean, but the last two blobs remain garbled — those are the answers under different keys.

6. Disassemble the mage/artificer code paths. Before each `fn_check_answer` call, a `MOV + STOREI` pair writes a different key to `0x10001E`. Mage uses `0x44A0CF`, Artificer uses `0xAFCEFA`.

7. Apply the correct per-path key to the garbled blobs.

8. Play through with the correct answers/Decrypt for the correct key.

---

## Traps and Dead Ends

- Warrior and Bard have no flags whatsoever. Every branch is a death scene. They exist to waste time.
- Wrong answer = instant death. No retry. The mage scroll "consumes your life force" and the game ends.
- Artificer flag is fake, only Mage dark path flag is correct.
- The mage spirit fight has no trick. Keep attacking until it dies or modify code if you're feeling brave.
- Byte-level XOR won't work, LOAD/STORE are 24-bit word operations. Strings are padded to multiples of 3. Players who try byte-by-byte XOR analysis without respecting the 3-byte alignment will get confused.

---

## Design Notes

- The strings key (`0x1FF1AD`) and the mage answer key (`0x44A0CF`) are the same three bytes in different order — `[AD, F1, 1F]` vs `[CF, A0, 44]`. This is intentional misdirection; a solver who finds the first key might assume it works for everything.
- Some flag keys contain hex wordplay: `0x0BADAF` reads as "bad af."
- The ISA has 39 opcodes (`0x00`–`0x26`), 3 registers, and 24-bit data width. The full spec is in `ISAspec.md` (not distributed to players).
- The RPG is generated by `genJourney.py` and compiled by `asmISA.py` (both in the `CustomISA-test files` subfolder, not distributed).
- The VM (`customISA.py`) and server wrapper (`server.py`) run inside Docker. Players only interact via TCP.
