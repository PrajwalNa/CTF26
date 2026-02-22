#!/usr/bin/env python3

import argparse
import re
import subprocess
from pathlib import Path


def parseHexArray(src: str, name: str) -> list[int]:
    pattern = rf"static const uint8_t {re.escape(name)}\[[^\]]*\]\s*=\s*\{{(.*?)\}};"
    match = re.search(pattern, src, re.S)
    if not match:
        raise ValueError(f"array '{name}' not found")

    hexVals = re.findall(r"0x([0-9A-Fa-f]{2})", match.group(1))
    if not hexVals:
        raise ValueError(f"array '{name}' is empty or unparsable")

    return [int(v, 16) for v in hexVals]


def buildInverseMap(runeMap: list[int]) -> list[int]:
    if len(runeMap) != 256:
        raise ValueError(f"runeMap length must be 256, got {len(runeMap)}")

    inv = [0] * 256
    seen = [False] * 256

    for plain, enc in enumerate(runeMap):
        if seen[enc]:
            raise ValueError("runeMap is not one-to-one (duplicate encoded byte)")
        seen[enc] = True
        inv[enc] = plain

    return inv


def decodeBytes(encoded: list[int], invMap: list[int]) -> str:
    raw = bytes(invMap[b] for b in encoded)
    return raw.decode("ascii")


def loadFromSource(sourcePath: Path) -> tuple[str, str]:
    src = sourcePath.read_text(encoding="utf-8")
    runeMap = parseHexArray(src, "runeMap")
    inscription = parseHexArray(src, "inscription")
    flagRunes = parseHexArray(src, "flagRunes")

    invMap = buildInverseMap(runeMap)
    answer = decodeBytes(inscription, invMap)
    flag = decodeBytes(flagRunes, invMap)
    return answer, flag


def runBinary(exePath: Path, answer: str) -> None:
    proc = subprocess.run(
        [str(exePath)],
        input=(answer + "\n").encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    print("\n[binary stdout]")
    print(proc.stdout.decode("utf-8", errors="replace"))
    if proc.stderr:
        print("[binary stderr]")
        print(proc.stderr.decode("utf-8", errors="replace"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve Rune Translation by inverting runeMap.")
    parser.add_argument(
        "--source",
        default="rune.c",
        help="Path to source file containing runeMap/inscription/flagRunes (default: rune.c)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the local binary with the recovered answer",
    )
    parser.add_argument(
        "--exe",
        default="RuneTranslation.exe",
        help="Binary path used with --run (default: RuneTranslation.exe)",
    )
    args = parser.parse_args()

    sourcePath = Path(args.source)
    answer, flag = loadFromSource(sourcePath)

    print(f"[+] answer: {answer}")
    print(f"[+] flag:   {flag}")

    if args.run:
        runBinary(Path(args.exe), answer)


if __name__ == "__main__":
    main()
