#!/usr/bin/env python3
"""
Lich protocol test client.

Examples:
  python test_client.py handshake
  python test_client.py login --user test --password SBLCHT42
  python test_client.py flow --user test --password SBLCHT42 --max-payload 512
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shlex
import socket
import struct
import sys
from typing import Optional

try:
    import blake3  # pip install blake3
except ImportError:
    blake3 = None


HEADER_SIZE = 46
VERSION = 0x06
MAGIC = bytes([0x4C, 0x1C, 0x48, 0x84, 0x92, 0x00])
ZERO_MAGIC = b"\x00" * 6
ELE_KEY = bytes([0xF0, 0x15, 0xAC, 0x71, 0xEE])

PROTO_AR = b"AR"
PROTO_SB = b"SB"
PROTO_BC = b"BC"
PROTO_NW = b"NW"
PROTO_UW = b"UW"
PROTO_ER = b"ER"

MSG_ARISE_REQ = 0x01
MSG_ARISE_RESP = 0x02
MSG_SB_REQ = 0x10
MSG_SB_RESP = 0x11
MSG_SB_ELEVATE = 0x12
MSG_BC_RTS = 0x20
MSG_BC_CTS = 0x21
MSG_BC_DATA = 0x22
MSG_BC_ACK = 0x23
MSG_NW_SETCFG = 0x30
MSG_NW_GETCFG = 0x31
MSG_NW_APPROVE = 0x34
MSG_UW_EXEC = 0x40
MSG_UW_RESULT = 0x41
MSG_UW_INVALID = 0x42
MSG_ER_REQ = 0x50
MSG_ER_RESP = 0x51
MSG_ER_IDK = 0x52

ERR_MAP = {
    0x0000: "ERR_OK",
    0x0001: "ERR_MAGIC_VER",
    0x0002: "ERR_HASH_FAIL",
    0x0003: "ERR_UNAUTHORIZED",
    0x0004: "ERR_CMD_DENIED",
    0x0005: "ERR_TOKEN_EXP",
    0x0006: "ERR_MALFORMED",
    0x0007: "ERR_CONFIG_NOTFOUND",
    0x0008: "ERR_CHUNK_HASH",
    0x0009: "ERR_TRANSFER_DENY",
}


def hashPayload(protoId: bytes, payload: bytes) -> bytes:
    if protoId == PROTO_AR:
        md5Bytes = hashlib.md5(payload).digest()
        return md5Bytes + (b"\x00" * 16)

    if blake3 is None:
        raise RuntimeError("blake3 module is required for non-AR messages. Install with: pip install blake3")

    return blake3.blake3(payload).digest()


def buildFrame(protoId: bytes, msgType: int, payload: bytes) -> bytes:
    if len(protoId) != 2:
        raise ValueError("protoId must be 2 bytes")

    magicBytes = ZERO_MAGIC if protoId == PROTO_AR else MAGIC
    payloadHash = hashPayload(protoId, payload)

    header = (
        protoId
        + bytes([msgType])
        + struct.pack("<I", len(payload))
        + magicBytes
        + bytes([VERSION])
        + payloadHash
    )

    if len(header) != HEADER_SIZE:
        raise RuntimeError(f"header size mismatch: {len(header)}")

    return header + payload


def recvExact(sockObj: socket.socket, size: int) -> bytes:
    out = bytearray()
    while len(out) < size:
        chunk = sockObj.recv(size - len(out))
        if not chunk:
            raise ConnectionError(f"socket closed early: wanted {size}, got {len(out)}")
        out.extend(chunk)
    return bytes(out)


def parseFrame(rawFrame: bytes) -> dict:
    if len(rawFrame) < HEADER_SIZE:
        raise ValueError("short frame")

    header = rawFrame[:HEADER_SIZE]
    payload = rawFrame[HEADER_SIZE:]

    payloadLen = struct.unpack("<I", header[3:7])[0]
    if payloadLen != len(payload):
        raise ValueError(f"payload length mismatch header={payloadLen} actual={len(payload)}")

    return {
        "protoId": header[0:2],
        "msgType": header[2],
        "payloadLen": payloadLen,
        "magic": header[7:13],
        "version": header[13],
        "hashBytes": header[14:46],
        "payload": payload,
    }


def verifyFrameHash(frame: dict) -> bool:
    try:
        expectedHash = hashPayload(frame["protoId"], frame["payload"])
    except RuntimeError:
        return False

    if frame["protoId"] == PROTO_AR:
        return frame["hashBytes"][:16] == expectedHash[:16]

    return frame["hashBytes"] == expectedHash


def requestFrame(host: str, port: int, timeout: float, protoId: bytes, msgType: int, payload: bytes) -> dict:
    reqFrame = buildFrame(protoId, msgType, payload)
    sendFrame = parseFrame(reqFrame)
    print("=== SEND ===")
    printFrame(sendFrame, "send")

    with socket.create_connection((host, port), timeout=timeout) as sockObj:
        sockObj.settimeout(timeout)
        sockObj.sendall(reqFrame)

        respHeader = recvExact(sockObj, HEADER_SIZE)
        respPayloadLen = struct.unpack("<I", respHeader[3:7])[0]
        respPayload = recvExact(sockObj, respPayloadLen) if respPayloadLen else b""

    recvFrame = parseFrame(respHeader + respPayload)
    print("=== RECV ===")
    printFrame(recvFrame, "recv")
    return recvFrame


def decodeError(frame: dict) -> Optional[str]:
    payload = frame["payload"]
    msgType = frame["msgType"]

    if len(payload) != 2:
        return None

    if msgType not in (MSG_ER_IDK, MSG_UW_INVALID, MSG_BC_CTS, MSG_BC_ACK):
        return None

    code = struct.unpack("<H", payload)[0]
    return f"0x{code:04x} ({ERR_MAP.get(code, 'UNKNOWN')})"


def printFrame(frame: dict, label: str = "resp") -> None:
    protoText = frame["protoId"].decode("ascii", errors="replace")
    hashOk = verifyFrameHash(frame)

    print(f"[{label}] proto={protoText} msg=0x{frame['msgType']:02x} payloadLen={frame['payloadLen']}")
    print(f"[{label}] magic={frame['magic'].hex()} ver=0x{frame['version']:02x} hashOk={hashOk}")

    errText = decodeError(frame)
    if errText:
        print(f"[{label}] error={errText}")
        return

    payload = frame["payload"]

    if frame["protoId"] == PROTO_AR and frame["msgType"] == MSG_ARISE_RESP and len(payload) >= 3:
        magicPart = struct.unpack("<H", payload[:2])[0]
        respVer = payload[2]
        chosenHash = payload[3:].decode("utf-8", errors="replace")
        print(f"[{label}] arise.magicPart=0x{magicPart:04x} arise.ver=0x{respVer:02x} chosenHash={chosenHash}")
        return

    if frame["protoId"] == PROTO_SB and frame["msgType"] == MSG_SB_RESP and len(payload) >= 18:
        accept = payload[0]
        token = payload[1:17]
        authLevel = payload[17]
        print(f"[{label}] soulbind.accept={accept} auth={authLevel} token={token.hex()}")
        if len(payload) > 18:
            flagText = decodeElevFlag(payload[18:])
            if flagText:
                print(f"[{label}] soulbind.flag={flagText}")
            else:
                print(f"[{label}] soulbind.flag.raw={payload[18:].hex()}")
        return

    if frame["protoId"] == PROTO_BC and frame["msgType"] == MSG_BC_CTS and len(payload) >= 1:
        print(f"[{label}] bc.cts.accept={payload[0]}")
        return

    if frame["protoId"] == PROTO_BC and frame["msgType"] == MSG_BC_ACK and len(payload) == 0:
        print(f"[{label}] bc.ack=ok")
        return

    if frame["protoId"] == PROTO_NW and frame["msgType"] == MSG_NW_GETCFG:
        valueText = payload.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
        print(f"[{label}] getCfg.value={valueText}")
        return

    if frame["protoId"] == PROTO_NW and frame["msgType"] == MSG_NW_APPROVE:
        parts = payload.split(b"\x00")
        if len(parts) >= 2:
            keyText = parts[0].decode("utf-8", errors="replace")
            decisionText = parts[1].decode("utf-8", errors="replace")
            print(f"[{label}] nw.key={keyText} decision={decisionText}")
            return

    if frame["protoId"] == PROTO_UW and frame["msgType"] == MSG_UW_RESULT:
        print(f"[{label}] uw.result.raw={payload.hex()}")
        return

    if frame["protoId"] == PROTO_ER and frame["msgType"] == MSG_ER_RESP:
        print(f"[{label}] eternal.raw={payload.hex()}")
        return

    print(f"[{label}] payload.hex={payload.hex()}")


def parseToken(tokenHex: str) -> bytes:
    try:
        token = bytes.fromhex(tokenHex)
    except ValueError as exc:
        raise ValueError("token must be hex") from exc

    if len(token) != 16:
        raise ValueError("token must be 16 bytes (32 hex chars)")

    return token


def parseChunkBytes(chunkText: Optional[str], chunkHex: Optional[str]) -> bytes:
    if (chunkText is None and chunkHex is None) or (chunkText is not None and chunkHex is not None):
        raise ValueError("choose exactly one of --text or --hex")

    if chunkText is not None:
        return chunkText.encode("utf-8")

    try:
        return bytes.fromhex(chunkHex or "")
    except ValueError as exc:
        raise ValueError("chunk hex is invalid") from exc


def decodeElevFlag(flagBytes: bytes) -> Optional[str]:
    if not flagBytes:
        return None

    # Case 1: server returns plaintext bytes.
    try:
        plain = flagBytes.decode("utf-8")
    except UnicodeDecodeError:
        plain = ""
    if re.fullmatch(r"\{[A-Za-z0-9_]+\}", plain):
        return plain

    # Case 2: server returns XOR-obfuscated bytes.
    dec = bytes(flagBytes[i] ^ ELE_KEY[i % len(ELE_KEY)] for i in range(len(flagBytes)))
    try:
        decText = dec.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if re.fullmatch(r"\{[A-Za-z0-9_]+\}", decText):
        return decText

    return None


def doHandshake(host: str, port: int, timeout: float, supportedHashes: str) -> dict:
    payload = bytes([0x84, 0x92, VERSION]) + supportedHashes.encode("utf-8")
    frame = requestFrame(host, port, timeout, PROTO_AR, MSG_ARISE_REQ, payload)
    return frame


def doLogin(host: str, port: int, timeout: float, user: str, password: str) -> Optional[bytes]:
    if len(user.encode("utf-8")) > 8:
        raise ValueError("username must be <=8 bytes")
    if len(password.encode("utf-8")) > 8:
        raise ValueError("password must be <=8 bytes")

    payload = user.encode("utf-8") + b"\x00" + password.encode("utf-8") + b"\x00"
    frame = requestFrame(host, port, timeout, PROTO_SB, MSG_SB_REQ, payload)

    if frame["protoId"] == PROTO_SB and frame["msgType"] == MSG_SB_RESP and len(frame["payload"]) >= 18:
        if frame["payload"][0] == 1:
            token = frame["payload"][1:17]
            print(f"[login] token={token.hex()}")
            return token

    return None


def doSetCfg(host: str, port: int, timeout: float, token: bytes, key: str, value: str) -> dict:
    payload = key.encode("utf-8") + b"\x00" + value.encode("utf-8") + b"\x00" + token
    frame = requestFrame(host, port, timeout, PROTO_NW, MSG_NW_SETCFG, payload)
    return frame


def doGetCfg(host: str, port: int, timeout: float, token: bytes, key: str) -> dict:
    payload = key.encode("utf-8") + b"\x00" + token
    frame = requestFrame(host, port, timeout, PROTO_NW, MSG_NW_GETCFG, payload)
    return frame


def doElevate(host: str, port: int, timeout: float, token: bytes, requestText: str) -> dict:
    payload = token + requestText.encode("utf-8") + b"\x00"
    frame = requestFrame(host, port, timeout, PROTO_SB, MSG_SB_ELEVATE, payload)
    return frame


def doBcRts(host: str, port: int, timeout: float, token: bytes, dataSize: int) -> dict:
    if dataSize < 0 or dataSize > 0xFFFFFFFF:
        raise ValueError("size must be in range [0, 4294967295]")

    payload = struct.pack("<I", dataSize) + token
    frame = requestFrame(host, port, timeout, PROTO_BC, MSG_BC_RTS, payload)
    return frame


def doBcData(host: str, port: int, timeout: float, token: bytes, chunkBytes: bytes) -> dict:
    if len(chunkBytes) > 1024:
        raise ValueError("chunk size must be <=1024 bytes")

    chunkHash = hashlib.md5(chunkBytes).digest()
    payload = chunkBytes + chunkHash + token
    frame = requestFrame(host, port, timeout, PROTO_BC, MSG_BC_DATA, payload)
    return frame


def doBcSend(host: str, port: int, timeout: float, token: bytes, chunkBytes: bytes) -> int:
    rtsFrame = doBcRts(host, port, timeout, token, len(chunkBytes))
    if not (rtsFrame["protoId"] == PROTO_BC and rtsFrame["msgType"] == MSG_BC_CTS and len(rtsFrame["payload"]) >= 1):
        print("[bcsend] RTS failed")
        return 1
    if rtsFrame["payload"][0] != 1:
        print("[bcsend] RTS denied")
        return 1

    dataFrame = doBcData(host, port, timeout, token, chunkBytes)
    if dataFrame["protoId"] == PROTO_BC and dataFrame["msgType"] == MSG_BC_ACK and len(dataFrame["payload"]) == 0:
        return 0

    print("[bcsend] DATA failed")
    return 1


def doExec(host: str, port: int, timeout: float, token: bytes, command: str) -> dict:
    payload = command.encode("utf-8") + b"\x00" + token
    frame = requestFrame(host, port, timeout, PROTO_UW, MSG_UW_EXEC, payload)
    return frame


def doLogout(host: str, port: int, timeout: float, token: bytes) -> dict:
    frame = requestFrame(host, port, timeout, PROTO_ER, MSG_ER_REQ, token)
    return frame


def printSessionHelp() -> None:
    print("session commands:")
    print("  help")
    print("  status")
    print("  handshake [supportedHashes]")
    print("  login [user] [password]")
    print("  token")
    print("  setToken <hexToken>")
    print("  bcrts <size>")
    print("  bcdata <text>")
    print("  bcdatahex <hexBytes>")
    print("  bcsend <text>")
    print("  bcsendhex <hexBytes>")
    print("  get <key>")
    print("  set <key> <value>")
    print("  elevate [requestText]")
    print("  exec <command>")
    print("  logout")
    print("  quit/exit")


def runSession(host: str, port: int, timeout: float, user: str, password: str) -> int:
    sess = {
        "user": user,
        "password": password,
        "token": None,
    }

    print("interactive session mode")
    printSessionHelp()

    while True:
        try:
            line = input("lich> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue

        try:
            parts = shlex.split(line)
        except ValueError as exc:
            print(f"parse error: {exc}")
            continue

        cmd = parts[0].lower()

        try:
            if cmd in ("quit", "exit"):
                return 0

            if cmd == "help":
                printSessionHelp()
                continue

            if cmd == "status":
                tok = sess["token"].hex() if sess["token"] else "none"
                print(f"user={sess['user'] or '<unset>'} token={tok}")
                continue

            if cmd == "token":
                print(sess["token"].hex() if sess["token"] else "none")
                continue

            if cmd == "settoken":
                if len(parts) != 2:
                    print("usage: setToken <hexToken>")
                    continue
                sess["token"] = parseToken(parts[1])
                print("token updated")
                continue

            if cmd == "handshake":
                supported = parts[1] if len(parts) > 1 else "Blake3,MD5"
                doHandshake(host, port, timeout, supported)
                continue

            if cmd == "login":
                if len(parts) >= 2:
                    sess["user"] = parts[1]
                if len(parts) >= 3:
                    sess["password"] = parts[2]

                if not sess["user"] or not sess["password"]:
                    print("usage: login <user> <password>")
                    continue

                tok = doLogin(host, port, timeout, sess["user"], sess["password"])
                if tok:
                    sess["token"] = tok
                continue

            if cmd == "get":
                if len(parts) != 2:
                    print("usage: get <key>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                doGetCfg(host, port, timeout, sess["token"], parts[1])
                continue

            if cmd == "bcrts":
                if len(parts) != 2:
                    print("usage: bcrts <size>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                doBcRts(host, port, timeout, sess["token"], int(parts[1]))
                continue

            if cmd == "bcdata":
                if len(parts) < 2:
                    print("usage: bcdata <text>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                chunkBytes = " ".join(parts[1:]).encode("utf-8")
                doBcData(host, port, timeout, sess["token"], chunkBytes)
                continue

            if cmd == "bcdatahex":
                if len(parts) != 2:
                    print("usage: bcdatahex <hexBytes>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                chunkBytes = bytes.fromhex(parts[1])
                doBcData(host, port, timeout, sess["token"], chunkBytes)
                continue

            if cmd == "bcsend":
                if len(parts) < 2:
                    print("usage: bcsend <text>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                chunkBytes = " ".join(parts[1:]).encode("utf-8")
                doBcSend(host, port, timeout, sess["token"], chunkBytes)
                continue

            if cmd == "bcsendhex":
                if len(parts) != 2:
                    print("usage: bcsendhex <hexBytes>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                chunkBytes = bytes.fromhex(parts[1])
                doBcSend(host, port, timeout, sess["token"], chunkBytes)
                continue

            if cmd == "set":
                if len(parts) < 3:
                    print("usage: set <key> <value>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                key = parts[1]
                value = " ".join(parts[2:])
                doSetCfg(host, port, timeout, sess["token"], key, value)
                continue

            if cmd == "elevate":
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                requestText = parts[1] if len(parts) > 1 else "elevateRequest"
                frame = doElevate(host, port, timeout, sess["token"], requestText)
                if frame["protoId"] == PROTO_SB and frame["msgType"] == MSG_SB_RESP and len(frame["payload"]) >= 18 and frame["payload"][0] == 1:
                    sess["token"] = frame["payload"][1:17]
                    print(f"elevated token={sess['token'].hex()}")
                continue

            if cmd == "exec":
                if len(parts) < 2:
                    print("usage: exec <command>")
                    continue
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                command = " ".join(parts[1:])
                doExec(host, port, timeout, sess["token"], command)
                continue

            if cmd == "logout":
                if not sess["token"]:
                    print("token not set; login first")
                    continue
                doLogout(host, port, timeout, sess["token"])
                sess["token"] = None
                print("token cleared")
                continue

            print("unknown command; use: help")

        except (ValueError, RuntimeError, ConnectionError, OSError) as exc:
            print(f"error: {exc}")


def runFlow(host: str, port: int, timeout: float, user: str, password: str, maxPayload: int, command: str) -> int:
    print("[flow] handshake")
    hsFrame = doHandshake(host, port, timeout, "Blake3,MD5")
    if not (hsFrame["protoId"] == PROTO_AR and hsFrame["msgType"] == MSG_ARISE_RESP):
        print("[flow] handshake failed")
        return 1

    print("[flow] login")
    token = doLogin(host, port, timeout, user, password)
    if not token:
        print("[flow] login failed")
        return 1

    print("[flow] set EleEnabled=True")
    doSetCfg(host, port, timeout, token, "EleEnabled", "True")

    print("[flow] elevate")
    elevFrame = doElevate(host, port, timeout, token, "elevateRequest")
    if elevFrame["protoId"] == PROTO_SB and elevFrame["msgType"] == MSG_SB_RESP and len(elevFrame["payload"]) >= 18 and elevFrame["payload"][0] == 1:
        token = elevFrame["payload"][1:17]
        print(f"[flow] elevated token={token.hex()}")
    else:
        print("[flow] elevate failed")
        return 1

    print(f"[flow] set maxPayload={maxPayload}")
    doSetCfg(host, port, timeout, token, "maxPayload", str(maxPayload))

    print("[flow] set EnCmdExec=True")
    doSetCfg(host, port, timeout, token, "EnCmdExec", "True")

    print("[flow] exec command")
    doExec(host, port, timeout, token, command)

    print("[flow] logout")
    doLogout(host, port, timeout, token)

    return 0


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lich protocol test client")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9001, help="Server port (default: 9001)")
    parser.add_argument("--timeout", type=float, default=5.0, help="Socket timeout seconds")

    subParsers = parser.add_subparsers(dest="cmd", required=True)

    sp = subParsers.add_parser("handshake", help="Send Arise handshake")
    sp.add_argument("--supported", default="Blake3,MD5", help="supported_hashes value")

    sp = subParsers.add_parser("login", help="Send SoulBind login")
    sp.add_argument("--user", required=True)
    sp.add_argument("--password", required=True)

    sp = subParsers.add_parser("get", help="NecroticWeave GetConfig")
    sp.add_argument("--token", required=True, help="hex token from login")
    sp.add_argument("--key", required=True)

    sp = subParsers.add_parser("set", help="NecroticWeave SetConfig")
    sp.add_argument("--token", required=True, help="hex token from login")
    sp.add_argument("--key", required=True)
    sp.add_argument("--value", required=True)

    sp = subParsers.add_parser("elevate", help="SoulBind elevate")
    sp.add_argument("--token", required=True, help="hex token from login")
    sp.add_argument("--request", default="elevateRequest")

    sp = subParsers.add_parser("bcrts", help="BoneCourier RTS")
    sp.add_argument("--token", required=True, help="hex token from login")
    sp.add_argument("--size", type=int, required=True, help="total transfer size")

    sp = subParsers.add_parser("bcdata", help="BoneCourier DATA")
    sp.add_argument("--token", required=True, help="hex token from login")
    grp = sp.add_mutually_exclusive_group(required=True)
    grp.add_argument("--text", help="chunk text to send")
    grp.add_argument("--hex", help="chunk bytes in hex")

    sp = subParsers.add_parser("bcsend", help="BoneCourier RTS + DATA helper")
    sp.add_argument("--token", required=True, help="hex token from login")
    grp = sp.add_mutually_exclusive_group(required=True)
    grp.add_argument("--text", help="chunk text to send")
    grp.add_argument("--hex", help="chunk bytes in hex")

    sp = subParsers.add_parser("exec", help="UndeadWhisper exec")
    sp.add_argument("--token", required=True, help="hex token")
    sp.add_argument("--command", required=True)

    sp = subParsers.add_parser("logout", help="EternalRest")
    sp.add_argument("--token", required=True, help="hex token")

    sp = subParsers.add_parser("flow", help="End-to-end test flow")
    sp.add_argument("--user", required=True)
    sp.add_argument("--password", required=True)
    sp.add_argument("--max-payload", type=int, default=512)
    sp.add_argument("--command", default="id")

    sp = subParsers.add_parser("session", help="Interactive session mode")
    sp.add_argument("--user", default="")
    sp.add_argument("--password", default="")

    return parser


def main() -> int:
    args = buildParser().parse_args()

    host = args.host
    port = args.port
    timeout = args.timeout

    try:
        if args.cmd == "handshake":
            doHandshake(host, port, timeout, args.supported)
            return 0

        if args.cmd == "login":
            token = doLogin(host, port, timeout, args.user, args.password)
            return 0 if token else 1

        if args.cmd == "get":
            doGetCfg(host, port, timeout, parseToken(args.token), args.key)
            return 0

        if args.cmd == "set":
            doSetCfg(host, port, timeout, parseToken(args.token), args.key, args.value)
            return 0

        if args.cmd == "elevate":
            doElevate(host, port, timeout, parseToken(args.token), args.request)
            return 0

        if args.cmd == "bcrts":
            doBcRts(host, port, timeout, parseToken(args.token), args.size)
            return 0

        if args.cmd == "bcdata":
            chunkBytes = parseChunkBytes(args.text, args.hex)
            doBcData(host, port, timeout, parseToken(args.token), chunkBytes)
            return 0

        if args.cmd == "bcsend":
            chunkBytes = parseChunkBytes(args.text, args.hex)
            return doBcSend(host, port, timeout, parseToken(args.token), chunkBytes)

        if args.cmd == "exec":
            doExec(host, port, timeout, parseToken(args.token), args.command)
            return 0

        if args.cmd == "logout":
            doLogout(host, port, timeout, parseToken(args.token))
            return 0

        if args.cmd == "flow":
            return runFlow(host, port, timeout, args.user, args.password, args.max_payload, args.command)

        if args.cmd == "session":
            return runSession(host, port, timeout, args.user, args.password)

        print("unknown command")
        return 2

    except (ValueError, RuntimeError, ConnectionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
