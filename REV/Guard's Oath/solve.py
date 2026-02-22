#!/usr/bin/env python3

TARGET = [0xF0, 0x0A, 0x41, 0x5F, 0x35, 0xFA, 0x17, 0xC2, 0xF5]


def rotr8(v: int, r: int) -> int:
    return ((v >> r) | ((v << (8 - r)) & 0xFF)) & 0xFF


def recover_oath() -> bytes:
    out = []
    for i, x in enumerate(TARGET):
        v = rotr8(x, (i % 3) + 1)
        v = (v - (i * 0x11)) & 0xFF
        v ^= (0x3A + (i * 7)) & 0xFF
        out.append(v)
    return bytes(out)


if __name__ == "__main__":
    oath = recover_oath()
    print("Recovered oath:", oath.decode("ascii"))
