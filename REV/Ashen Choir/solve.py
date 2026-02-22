#!/usr/bin/env python3

VOICE_COUNT = 24
RAW_LEN = 20

IDX_A = [0, 5, 10, 15, 1, 6, 11, 16, 2, 7, 12, 17, 3, 8, 13, 18, 4, 9, 14, 19, 0, 6, 12, 18]
IDX_B = [4, 9, 14, 19, 3, 8, 13, 18, 2, 7, 12, 17, 1, 6, 11, 16, 0, 5, 10, 15, 4, 8, 11, 17]
IDX_C = [2, 7, 12, 17, 0, 5, 10, 15, 4, 9, 14, 19, 1, 6, 11, 16, 3, 8, 13, 18, 2, 9, 10, 19]
ROT_BY = [1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5, 6, 7, 2, 5, 3]

MIX_A = [0xBB, 0x54, 0xAA, 0xC4, 0xB8, 0x9D, 0xC8, 0x68, 0xBA, 0x37, 0xD9, 0xCC, 0x21, 0xB2, 0xCE, 0xCE, 0x9F, 0x09, 0xB4, 0x3C, 0xEB, 0x7E, 0x57, 0xA0]
MIX_B = [0x8A, 0xF3, 0xE6, 0x56, 0xB5, 0xF3, 0x39, 0x3D, 0x79, 0x4F, 0xF3, 0x57, 0x66, 0x0F, 0xD0, 0xAA, 0x10, 0xDB, 0x8D, 0x90, 0xB8, 0x99, 0x43, 0xCB]
FOLD_A = [0xEA, 0x87, 0x66, 0x22, 0x16, 0x24, 0xD0, 0x1B, 0x08, 0x64, 0x64, 0x35, 0x91, 0x64, 0xE7, 0xA0, 0x06, 0xAA, 0xDD, 0x75, 0x17, 0x9D, 0x6D, 0x5C]
FOLD_B = [0xF8, 0x09, 0x47, 0x78, 0xD1, 0x19, 0x40, 0x34, 0xB9, 0x2C, 0xB9, 0x33, 0xE2, 0xCD, 0xD3, 0x4F, 0x5F, 0xB6, 0x5F, 0xBE, 0x57, 0x0A, 0x46, 0xA9]
HI_A0 = [0x5E, 0x19, 0xFD, 0xE9, 0x0C, 0xF9, 0xB4, 0x83, 0x86, 0x22, 0x42, 0x1E, 0x57, 0xA1, 0x28, 0x62, 0xE1, 0x81, 0x1B, 0x4C, 0xDA, 0xB2, 0x15, 0xDC]
HI_B0 = [0x2E, 0xD9, 0x3D, 0xA9, 0xBC, 0x59, 0xF4, 0x73, 0xD6, 0x42, 0xA2, 0x2E, 0xF7, 0x71, 0xA8, 0xB2, 0x51, 0x41, 0xAB, 0xDC, 0x8A, 0x12, 0x35, 0xCC]
HI_A1 = [0x93, 0x4F, 0x1C, 0xEC, 0xB1, 0xC2, 0x23, 0x6A, 0xB4, 0x86, 0x6D, 0x62, 0x45, 0xF7, 0xC8, 0xDB, 0x81, 0x51, 0x71, 0xAA, 0xC9, 0x63, 0xD5, 0x51]
HI_B1 = [0xF3, 0x8F, 0xDC, 0x9C, 0xC1, 0x62, 0x63, 0x6A, 0x84, 0xE6, 0x8D, 0x52, 0x25, 0x27, 0x48, 0xEB, 0x31, 0x91, 0xC1, 0x2A, 0x19, 0xC3, 0xF5, 0xF1]

BUCKET = [
    [0, 4, 8, 12, 16, 20],
    [1, 5, 9, 13, 17, 21],
    [2, 6, 10, 14, 18, 22],
    [3, 7, 11, 15, 19, 23],
]

CORE_A = [0x3C, 0xA3, 0x34, 0x72, 0xD7, 0xFB, 0xE1]
CORE_B = [0xF7, 0xFF, 0x84, 0x5C, 0xE4, 0x32, 0x46]

SIG_MASK = 0xA5C3F17D
REAL_ADD_PART = 0x82171A50
REAL_GOAL_PART = 0xF719B1DE
FAKE_ADD_PART = 0x941A4F92
FAKE_GOAL_PART = 0x11B05077

REAL_ENC = [0xF4, 0xF9, 0x4B, 0xF6, 0xA8, 0x58, 0x29, 0x7D, 0xBE, 0x28, 0xB5, 0x9D, 0xFB, 0x96, 0x77, 0x41, 0xB3, 0x7B, 0x0D]
FAKE_ENC = [0xCE, 0xCE, 0x3F, 0xBE, 0x0F, 0x5F, 0xC0, 0x17, 0x45, 0x75, 0xF8, 0x76, 0x4D]
REAL_SALT_A = [0x33, 0xA1, 0x77, 0x19, 0xE4]
REAL_SALT_B = [0x2A, 0x75, 0xD5, 0x76, 0xD1]
FAKE_SALT_A = [0x91, 0x4E, 0x2F, 0xC4]
FAKE_SALT_B = [0xED, 0x6F, 0x97, 0x89]

REAL_TOKEN = "ASHN-CHOR-ECHO-NITE-WARD"
FAKE_A_TOKEN = "WISP-CHOR-ECHO-NITE-VALE"
FAKE_B_TOKEN = "DUSK-CHOR-ECHO-NITE-WAIL"
FAKE_C_TOKEN = "MIST-CHOR-ECHO-NITE-GLEN"


def rotl32(v, r):
    return ((v << r) & 0xFFFFFFFF) | (v >> (32 - r))


def rotl8(v, r):
    return ((v << r) & 0xFF) | (v >> (8 - r))


def opaque_scramble(v):
    y = (v * 0x45D9F3B) & 0xFFFFFFFF
    y ^= y >> 16
    return (y * 0x27D4EB2D) & 0xFFFFFFFF


def parse_token(token):
    if len(token) != 24:
        return None
    out = []
    for i, ch in enumerate(token):
        if i in (4, 9, 14, 19):
            if ch != "-":
                return None
            continue
        if not ("A" <= ch <= "Z"):
            return None
        out.append(ch)
    if len(out) != RAW_LEN:
        return None
    return out


def split_byte(a, b, i):
    return (a[i] ^ b[i]) & 0xFF


def split_word(part):
    return part ^ SIG_MASK


def voice_lhs(inp, idx):
    m = split_byte(MIX_A, MIX_B, idx)
    f = split_byte(FOLD_A, FOLD_B, idx)
    lhs = (
        rotl8((ord(inp[IDX_A[idx]]) ^ m) & 0xFF, ROT_BY[idx])
        + ((ord(inp[IDX_B[idx]]) + f) & 0xFF)
    ) & 0xFF
    lhs ^= (ord(inp[IDX_C[idx]]) + idx * 7) & 0xFF
    return lhs & 0xFF


def run(token):
    inp = parse_token(token)
    if inp is None:
        return None

    st = {
        "s0": 0xA51C39E7,
        "s1": 0xB4D28A6C,
        "s2": 0xC0DEC0DE,
        "s3": 0x9137F00D,
        "trace": [0] * VOICE_COUNT,
        "passMask": [0] * VOICE_COUNT,
        "classHist": [0] * VOICE_COUNT,
        "voiceOrder": [0] * VOICE_COUNT,
        "classCounts": [0, 0, 0, 0],
    }

    taint = 0
    for ch in inp:
        taint = (taint + ord(ch)) & 0xFF
    taint ^= 0x5A
    taint ^= ((ord(inp[1]) * 3) + ord(inp[18])) & 0xFF
    st["taint"] = taint & 0xFF
    class_acc = ((st["taint"] >> 1) ^ 3) & 3

    cursor = [0, 0, 0, 0]
    used = [False] * VOICE_COUNT

    for step in range(VOICE_COUNT):
        seed = (
            class_acc
            ^ step
            ^ ((st["s0"] >> (8 * (step & 3))) & 0xFF)
            ^ (st["taint"] if (step & 1) else 0xA5)
        ) & 0xFF
        cls = opaque_scramble(seed) & 3
        st["classHist"][step] = cls

        idx = None
        for off in range(4):
            b = (cls + off) & 3
            while cursor[b] < 6 and used[BUCKET[b][cursor[b]]]:
                cursor[b] += 1
            if cursor[b] < 6:
                idx = BUCKET[b][cursor[b]]
                cursor[b] += 1
                break
        if idx is None:
            for i in range(VOICE_COUNT):
                if not used[i]:
                    idx = i
                    break

        used[idx] = True
        st["voiceOrder"][step] = idx

        lhs = voice_lhs(inp, idx)
        t0 = split_byte(HI_A0, HI_B0, idx) & 0xF0
        t1 = split_byte(HI_A1, HI_B1, idx) & 0xF0
        passed = 1 if (((lhs ^ t0) & 0xF0) == 0 or ((lhs ^ t1) & 0xF0) == 0) else 0

        st["trace"][idx] = lhs
        st["passMask"][idx] = passed

        st["s0"] = (
            rotl32((st["s0"] ^ ((lhs + idx * 13) & 0xFF)) + 0x9E3779B9, 5)
            + 0x7F4A7C15
            + idx
        ) & 0xFFFFFFFF
        st["s1"] = (st["s1"] + (((lhs << 1) & 0xFF) ^ ((idx * 29) & 0xFF) ^ 0xA6)) & 0xFFFFFFFF
        st["s1"] ^= rotl32(st["s0"], (idx % 7) + 3)
        st["s2"] = (rotl32((st["s2"] + lhs + st["s1"] + 0x13579BDF) & 0xFFFFFFFF, 7) ^ ((passed & 1) << (idx % 13))) & 0xFFFFFFFF
        st["s3"] ^= rotl32((st["s2"] + 0x2468ACE1 + idx) & 0xFFFFFFFF, (idx % 11) + 1)
        class_acc = (class_acc + ((lhs ^ st["taint"]) & 3) + passed + ((idx >> 2) & 1)) & 3

    st["passCount"] = sum(st["passMask"]) & 0xFF
    for c in st["classHist"]:
        st["classCounts"][c] += 1

    edge = 0
    for i in range(VOICE_COUNT - 1):
        c0 = st["classHist"][i]
        c1 = st["classHist"][i + 1]
        p = st["passMask"][st["voiceOrder"][i]]
        term = (((c0 << 2) ^ c1 ^ p) * (0x11 + i * 7)) & 0xFFFF
        edge = (edge + term) % 65521
    st["edge"] = edge

    core = [0] * 7
    core[0] = (st["trace"][2] + st["trace"][17] + ord(inp[0])) & 0xFF
    core[1] = (st["trace"][5] ^ st["trace"][12] ^ ord(inp[7])) & 0xFF
    core[2] = (st["trace"][8] + st["trace"][9] + st["trace"][10]) & 0xFF
    core[3] = (st["trace"][4] - st["trace"][15] + ord(inp[11])) & 0xFF
    core[4] = (st["trace"][1] ^ st["trace"][6] ^ st["trace"][18]) & 0xFF
    core[5] = (ord(inp[3]) + ord(inp[14]) + st["trace"][22]) & 0xFF
    core[6] = (st["trace"][0] + ord(inp[19]) - st["trace"][23]) & 0xFF
    expected_core = [(CORE_A[i] ^ CORE_B[i]) & 0xFF for i in range(7)]
    st["coreOk"] = core == expected_core
    st["lateOk"] = (((st["trace"][21] ^ st["trace"][7]) + ord(inp[19])) & 0xFF) == 159

    sig_a = 0x811C9DC5
    for i, v in enumerate(st["trace"]):
        sig_a ^= (v + i * 17) & 0xFF
        sig_a = (sig_a * 0x01000193) & 0xFFFFFFFF
    sig_a ^= st["s1"]

    sig_b = 0x9E3779B9
    for i, ch in enumerate(inp):
        sig_b = rotl32(sig_b ^ ((ord(ch) + i * 9) & 0xFF), 5)
        sig_b = (sig_b + 0x7F4A7C15 + i * 0x1F123BB5) & 0xFFFFFFFF
    sig_b ^= st["s2"]

    st["sigA"] = sig_a
    st["sigB"] = sig_b
    st["chord"] = ((sig_a >> 8) ^ (sig_b >> 16) ^ (st["passCount"] << 3) ^ st["taint"]) & 0xFF

    real_add = split_word(REAL_ADD_PART)
    real_goal = split_word(REAL_GOAL_PART)
    fake_add = split_word(FAKE_ADD_PART)
    fake_goal = split_word(FAKE_GOAL_PART)
    st["sigReal"] = (((sig_a ^ rotl32(sig_b, 9)) + real_add) & 0xFFFFFFFF) == real_goal
    st["sigDecoy"] = (((sig_b ^ rotl32(sig_a, 7)) + fake_add) & 0xFFFFFFFF) == fake_goal

    st["stateOk"] = (st["edge"] == 14789 and st["classCounts"] == [6, 7, 3, 8])
    st["earlyOk"] = (st["edge"] == 14031 and st["classCounts"] == [8, 4, 8, 4])
    return st


def decrypt_real(st):
    out = []
    for i, b in enumerate(REAL_ENC):
        salt = REAL_SALT_A[i % 5] ^ REAL_SALT_B[i % 5]
        k = (
            ((st["s0"] >> (8 * (i % 4))) & 0xFF)
            ^ ((st["s1"] >> (8 * ((i + 1) % 4))) & 0xFF)
            ^ ((st["s2"] >> (8 * ((i + 2) % 4))) & 0xFF)
            ^ salt
            ^ ((0x33 + i * 7) & 0xFF)
        ) & 0xFF
        out.append(chr(b ^ k))
    return "".join(out)


def decrypt_fake(st, fold_const):
    out = []
    base = (st["s0"] ^ st["s1"] ^ st["s2"] ^ st["s3"]) & 0xFF
    seed = (base ^ fold_const) & 0xFF
    for i, b in enumerate(FAKE_ENC):
        salt = FAKE_SALT_A[i % 4] ^ FAKE_SALT_B[i % 4]
        k = ((((seed << 4) | (seed & 0x0F)) & 0xFF) ^ salt ^ ((0x5A + i * 11) & 0xFF)) & 0xFF
        out.append(chr(b ^ k))
    return "".join(out)


def classify(token):
    st = run(token)
    if st is None:
        return "DENY", None

    if st["passCount"] == 24 and st["stateOk"] and st["coreOk"] and st["lateOk"] and st["sigReal"]:
        return "REAL", decrypt_real(st)
    if st["passCount"] == 24 and st["sigDecoy"]:
        return "FAKE_B", decrypt_fake(st, 0xAB)
    if st["passCount"] >= 18 and st["earlyOk"] and (not st["lateOk"]):
        return "FAKE_A", decrypt_fake(st, 0x52)
    if st["passCount"] >= 14 and st["chord"] == 0x8A and (((st["sigA"] ^ st["sigB"]) & 0xFF) == 0x37):
        check = (st["sigA"] ^ st["sigB"] ^ st["s3"]) & 0xFFF
        return "FAKE_C", f"Ritual accepted. checksum=0x{check:03X}"
    return "DENY", None


def main():
    tokens = [REAL_TOKEN, FAKE_A_TOKEN, FAKE_B_TOKEN, FAKE_C_TOKEN]
    for t in tokens:
        kind, payload = classify(t)
        print(f"{t} -> {kind}")
        if payload is not None:
            print(f"  {payload}")


if __name__ == "__main__":
    main()
