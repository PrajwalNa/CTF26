#!/usr/bin/env python3

import argparse
import string
import subprocess


CHARSET = string.ascii_lowercase + string.digits


def solve() -> list[str]:
    answers = []

    for ember_ch in CHARSET:
        ember = ord(ember_ch)
        for frost_ch in CHARSET:
            frost = ord(frost_ch)
            if ember + frost != 150:
                continue

            for bile_ch in CHARSET:
                bile = ord(bile_ch)
                if (bile ^ 0x33) != 95:
                    continue

                for root_ch in CHARSET:
                    root = ord(root_ch)
                    if frost + root != 149:
                        continue
                    if bile - root != 11:
                        continue

                    for mist_ch in CHARSET:
                        mist = ord(mist_ch)
                        if root - mist != -13:
                            continue
                        if ((ember * 7 + mist) % 26) != 16:
                            continue
                        if (mist ^ ember) != 12:
                            continue

                        for ash_ch in CHARSET:
                            ash = ord(ash_ch)
                            if (ash & 0xF) != 3:
                                continue
                            if bile + ash != 207:
                                continue
                            if ((frost * 3 + ash) % 26) != 21:
                                continue

                            answers.append(
                                ember_ch + frost_ch + bile_ch + root_ch + mist_ch + ash_ch
                            )

    return answers


def run_binary(exe_path: str, answer: str) -> None:
    proc = subprocess.run(
        [exe_path],
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
    parser = argparse.ArgumentParser(description="Solve Cauldron of Balance constraints.")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run binary with solved answer",
    )
    parser.add_argument(
        "--exe",
        default="Cauldron.exe",
        help="Path to challenge binary (used with --run).",
    )
    args = parser.parse_args()

    answers = solve()
    print(f"[+] solutions found: {len(answers)}")
    for ans in answers:
        print(f"[+] answer: {ans}")

    if args.run:
        if len(answers) != 1:
            print("[!] Not running binary because solution count is not exactly 1.")
            return
        run_binary(args.exe, answers[0])


if __name__ == "__main__":
    main()
