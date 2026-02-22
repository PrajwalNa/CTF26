#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define voiceCount 24u
#define rawTokenLen 20u
#define dashedTokenLen 24u
#define denyMsg "The forest answers only with silence."

typedef enum outcomeTag {
    outcomeDeny = 0,
    outcomeReal = 1,
    outcomeFakeA = 2,
    outcomeFakeB = 3,
    outcomeFakeC = 4
    } outcome_t;

typedef struct choirStateTag {
    uint32_t s0;
    uint32_t s1;
    uint32_t s2;
    uint32_t s3;
    uint32_t sigA;
    uint32_t sigB;
    uint16_t edge;
    uint8_t taint;
    uint8_t classAcc;
    uint8_t passCount;
    uint8_t chord;
    uint8_t trace[voiceCount];
    uint8_t passMask[voiceCount];
    uint8_t classHist[voiceCount];
    uint8_t voiceOrder[voiceCount];
    uint8_t classCounts[4];
    } choirState_t;

typedef int (*voiceFn_t)(choirState_t* st, const uint8_t in[rawTokenLen]);

    // Each voice reads three token indices and one rotation amount.
static const uint8_t idxA[voiceCount] = {
    0u, 5u, 10u, 15u, 1u, 6u, 11u, 16u, 2u, 7u, 12u, 17u,
    3u, 8u, 13u, 18u, 4u, 9u, 14u, 19u, 0u, 6u, 12u, 18u
    };

static const uint8_t idxB[voiceCount] = {
    4u, 9u, 14u, 19u, 3u, 8u, 13u, 18u, 2u, 7u, 12u, 17u,
    1u, 6u, 11u, 16u, 0u, 5u, 10u, 15u, 4u, 8u, 11u, 17u
    };

static const uint8_t idxC[voiceCount] = {
    2u, 7u, 12u, 17u, 0u, 5u, 10u, 15u, 4u, 9u, 14u, 19u,
    1u, 6u, 11u, 16u, 3u, 8u, 13u, 18u, 2u, 9u, 10u, 19u
    };

static const uint8_t rotBy[voiceCount] = {
    1u, 2u, 3u, 4u, 5u, 6u, 7u, 1u, 2u, 3u, 4u, 5u,
    6u, 7u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 2u, 5u, 3u
    };

    // Split constants to avoid obvious direct tables in static strings.
static const uint8_t mixA[voiceCount] = {
    0xBBu, 0x54u, 0xAAu, 0xC4u, 0xB8u, 0x9Du, 0xC8u, 0x68u,
    0xBAu, 0x37u, 0xD9u, 0xCCu, 0x21u, 0xB2u, 0xCEu, 0xCEu,
    0x9Fu, 0x09u, 0xB4u, 0x3Cu, 0xEBu, 0x7Eu, 0x57u, 0xA0u
    };

static const uint8_t mixB[voiceCount] = {
    0x8Au, 0xF3u, 0xE6u, 0x56u, 0xB5u, 0xF3u, 0x39u, 0x3Du,
    0x79u, 0x4Fu, 0xF3u, 0x57u, 0x66u, 0x0Fu, 0xD0u, 0xAAu,
    0x10u, 0xDBu, 0x8Du, 0x90u, 0xB8u, 0x99u, 0x43u, 0xCBu
    };

static const uint8_t foldA[voiceCount] = {
    0xEAu, 0x87u, 0x66u, 0x22u, 0x16u, 0x24u, 0xD0u, 0x1Bu,
    0x08u, 0x64u, 0x64u, 0x35u, 0x91u, 0x64u, 0xE7u, 0xA0u,
    0x06u, 0xAAu, 0xDDu, 0x75u, 0x17u, 0x9Du, 0x6Du, 0x5Cu
    };

static const uint8_t foldB[voiceCount] = {
    0xF8u, 0x09u, 0x47u, 0x78u, 0xD1u, 0x19u, 0x40u, 0x34u,
    0xB9u, 0x2Cu, 0xB9u, 0x33u, 0xE2u, 0xCDu, 0xD3u, 0x4Fu,
    0x5Fu, 0xB6u, 0x5Fu, 0xBEu, 0x57u, 0x0Au, 0x46u, 0xA9u
    };

static const uint8_t hiA0[voiceCount] = {
    0x5Eu, 0x19u, 0xFDu, 0xE9u, 0x0Cu, 0xF9u, 0xB4u, 0x83u,
    0x86u, 0x22u, 0x42u, 0x1Eu, 0x57u, 0xA1u, 0x28u, 0x62u,
    0xE1u, 0x81u, 0x1Bu, 0x4Cu, 0xDAu, 0xB2u, 0x15u, 0xDCu
    };

static const uint8_t hiB0[voiceCount] = {
    0x2Eu, 0xD9u, 0x3Du, 0xA9u, 0xBCu, 0x59u, 0xF4u, 0x73u,
    0xD6u, 0x42u, 0xA2u, 0x2Eu, 0xF7u, 0x71u, 0xA8u, 0xB2u,
    0x51u, 0x41u, 0xABu, 0xDCu, 0x8Au, 0x12u, 0x35u, 0xCCu
    };

static const uint8_t hiA1[voiceCount] = {
    0x93u, 0x4Fu, 0x1Cu, 0xECu, 0xB1u, 0xC2u, 0x23u, 0x6Au,
    0xB4u, 0x86u, 0x6Du, 0x62u, 0x45u, 0xF7u, 0xC8u, 0xDBu,
    0x81u, 0x51u, 0x71u, 0xAAu, 0xC9u, 0x63u, 0xD5u, 0x51u
    };

static const uint8_t hiB1[voiceCount] = {
    0xF3u, 0x8Fu, 0xDCu, 0x9Cu, 0xC1u, 0x62u, 0x63u, 0x6Au,
    0x84u, 0xE6u, 0x8Du, 0x52u, 0x25u, 0x27u, 0x48u, 0xEBu,
    0x31u, 0x91u, 0xC1u, 0x2Au, 0x19u, 0xC3u, 0xF5u, 0xF1u
    };

static const uint8_t bucketOrder[4][6] = {
    { 0u, 4u, 8u, 12u, 16u, 20u },
    { 1u, 5u, 9u, 13u, 17u, 21u },
    { 2u, 6u, 10u, 14u, 18u, 22u },
    { 3u, 7u, 11u, 15u, 19u, 23u }
    };

static const uint8_t coreA[7] = { 0x3Cu, 0xA3u, 0x34u, 0x72u, 0xD7u, 0xFBu, 0xE1u };
static const uint8_t coreB[7] = { 0xF7u, 0xFFu, 0x84u, 0x5Cu, 0xE4u, 0x32u, 0x46u };

static const uint8_t realCountExpected[4] = { 6u, 7u, 3u, 8u };
static const uint8_t earlyCountExpected[4] = { 8u, 4u, 8u, 4u };

// Split words for signature relations.
static const uint32_t sigMask = 0xA5C3F17Du;
static const uint32_t realAddPart = 0x82171A50u;
static const uint32_t realGoalPart = 0xF719B1DEu;
static const uint32_t fakeAddPart = 0x941A4F92u;
static const uint32_t fakeGoalPart = 0x11B05077u;

// Real and fake payloads are encrypted bytes only.
static const uint8_t realEnc[] = {
    0xF4u, 0xF9u, 0x4Bu, 0xF6u, 0xA8u, 0x58u, 0x29u, 0x7Du, 0xBEu,
    0x28u, 0xB5u, 0x9Du, 0xFBu, 0x96u, 0x77u, 0x41u, 0xB3u, 0x7Bu, 0x0Du
    };

static const uint8_t fakeEnc[] = {
    0xCEu, 0xCEu, 0x3Fu, 0xBEu, 0x0Fu, 0x5Fu, 0xC0u, 0x17u, 0x45u, 0x75u, 0xF8u, 0x76u, 0x4Du
    };

    // Split salts used by key derivation paths.
static const uint8_t realSaltA[5] = { 0x33u, 0xA1u, 0x77u, 0x19u, 0xE4u };
static const uint8_t realSaltB[5] = { 0x2Au, 0x75u, 0xD5u, 0x76u, 0xD1u };
static const uint8_t fakeSaltA[4] = { 0x91u, 0x4Eu, 0x2Fu, 0xC4u };
static const uint8_t fakeSaltB[4] = { 0xEDu, 0x6Fu, 0x97u, 0x89u };

static uint32_t rotl32(uint32_t value, uint32_t amount) {
    return (value << amount) | (value >> (32u - amount));
    }

static uint8_t rotl8(uint8_t value, uint8_t amount) {
    return (uint8_t)((value << amount) | (value >> (8u - amount)));
    }

    // Lightweight opaque transform used in selector code paths.
static uint32_t opaqueScramble(uint32_t value) {
    uint32_t y = value * 0x45D9F3Bu;
    y ^= y >> 16;
    return y * 0x27D4EB2Du;
    }

    // Opaque predicate that is intentionally always true.
static int opaqueAlways(uint32_t value) {
    uint32_t y = value ^ 0xA5A5A5A5u;
    return (((y | 1u) & 1u) == 1u) ? 1 : 0;
    }

    // Split-byte loader with an opaque branch around the final value.
static uint8_t loadSplitByte(const uint8_t* left, const uint8_t* right, size_t index) {
    uint8_t out = (uint8_t)(left[index] ^ right[index]);
    if (opaqueAlways((uint32_t)index + (uint32_t)out)) {
        return out;
        }
    return (uint8_t)(out ^ 0u);
    }

static uint32_t loadSplitWord(uint32_t part) {
    uint32_t value = part ^ sigMask;
    if (opaqueAlways(value)) {
        return value;
        }
    return value ^ 0u;
    }

    // Parses XXXX-XXXX-XXXX-XXXX-XXXX into a 20-byte uppercase buffer.
static int parseToken(const char* line, uint8_t out[rawTokenLen]) {
    size_t i = 0u;
    size_t w = 0u;

    if (line == NULL || out == NULL) {
        return 0;
        }

    if (strlen(line) != dashedTokenLen) {
        return 0;
        }

    for (i = 0u; i < dashedTokenLen; i++) {
        if (i == 4u || i == 9u || i == 14u || i == 19u) {
            if (line[i] != '-') {
                return 0;
                }
            continue;
            }

        if (line[i] < 'A' || line[i] > 'Z') {
            return 0;
            }

        if (w >= rawTokenLen) {
            return 0;
            }
        out[w++] = (uint8_t)line[i];
        }

    return (w == rawTokenLen) ? 1 : 0;
    }

    // Initializes rolling state and derives deterministic path taint from input.
static void initState(choirState_t* st, const uint8_t in[rawTokenLen]) {
    size_t i = 0u;
    uint8_t ta = 0u;

    memset(st, 0, sizeof(*st));
    st->s0 = 0xA51C39E7u;
    st->s1 = 0xB4D28A6Cu;
    st->s2 = 0xC0DEC0DEu;
    st->s3 = 0x9137F00Du;

    for (i = 0u; i < rawTokenLen; i++) {
        ta = (uint8_t)(ta + in[i]);
        }
    ta ^= 0x5Au;
    ta ^= (uint8_t)(in[1] * 3u + in[18]);
    st->taint = ta;
    st->classAcc = (uint8_t)(((ta >> 1u) ^ 3u) & 0x03u);
    }

    // Core voice transform and state mutation shared by all 24 voice wrappers.
static int voiceCore(choirState_t* st, const uint8_t in[rawTokenLen], uint8_t voiceIdx) {
    uint8_t m = loadSplitByte(mixA, mixB, voiceIdx);
    uint8_t f = loadSplitByte(foldA, foldB, voiceIdx);
    uint8_t t0 = (uint8_t)(loadSplitByte(hiA0, hiB0, voiceIdx) & 0xF0u);
    uint8_t t1 = (uint8_t)(loadSplitByte(hiA1, hiB1, voiceIdx) & 0xF0u);
    uint8_t lhs = 0u;
    int pass = 0;

    lhs = (uint8_t)(
        (
            rotl8((uint8_t)(in[idxA[voiceIdx]] ^ m), rotBy[voiceIdx]) +
            (uint8_t)(in[idxB[voiceIdx]] + f)
            ) ^
        (uint8_t)(in[idxC[voiceIdx]] + (uint8_t)(voiceIdx * 7u))
        );

        // Each voice accepts one of two high-nibble classes.
    pass = ((((lhs ^ t0) & 0xF0u) == 0u) || (((lhs ^ t1) & 0xF0u) == 0u)) ? 1 : 0;

    st->trace[voiceIdx] = lhs;
    st->passMask[voiceIdx] = (uint8_t)pass;

    st->s0 = (
        rotl32((st->s0 ^ (uint32_t)((lhs + (uint8_t)(voiceIdx * 13u)) & 0xFFu)) + 0x9E3779B9u, 5u) +
        0x7F4A7C15u +
        voiceIdx
        );
    st->s1 += (uint32_t)(((lhs << 1u) & 0xFFu) ^ ((voiceIdx * 29u) & 0xFFu) ^ 0xA6u);
    st->s1 ^= rotl32(st->s0, (uint32_t)((voiceIdx % 7u) + 3u));
    st->s2 = rotl32(st->s2 + (uint32_t)lhs + st->s1 + 0x13579BDFu, 7u) ^ (uint32_t)((pass & 1) << (voiceIdx % 13u));
    st->s3 ^= rotl32(st->s2 + 0x2468ACE1u + voiceIdx, (uint32_t)((voiceIdx % 11u) + 1u));
    st->classAcc = (uint8_t)((st->classAcc + ((lhs ^ st->taint) & 3u) + (uint8_t)pass + ((voiceIdx >> 2u) & 1u)) & 3u);
    return pass;
    }

    // 24 separate voice handlers are intentionally kept as distinct call targets.
static int voice00(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 0u); }
static int voice01(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 1u); }
static int voice02(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 2u); }
static int voice03(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 3u); }
static int voice04(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 4u); }
static int voice05(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 5u); }
static int voice06(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 6u); }
static int voice07(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 7u); }
static int voice08(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 8u); }
static int voice09(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 9u); }
static int voice10(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 10u); }
static int voice11(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 11u); }
static int voice12(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 12u); }
static int voice13(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 13u); }
static int voice14(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 14u); }
static int voice15(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 15u); }
static int voice16(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 16u); }
static int voice17(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 17u); }
static int voice18(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 18u); }
static int voice19(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 19u); }
static int voice20(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 20u); }
static int voice21(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 21u); }
static int voice22(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 22u); }
static int voice23(choirState_t* st, const uint8_t in[rawTokenLen]) { return voiceCore(st, in, 23u); }

static const voiceFn_t voiceTable[voiceCount] = {
    voice00, voice01, voice02, voice03, voice04, voice05,
    voice06, voice07, voice08, voice09, voice10, voice11,
    voice12, voice13, voice14, voice15, voice16, voice17,
    voice18, voice19, voice20, voice21, voice22, voice23
    };

    // Dispatches voices through a class-driven selector so order is state-dependent.
static void dispatchVoices(choirState_t* st, const uint8_t in[rawTokenLen]) {
    uint8_t cursor[4] = { 0u, 0u, 0u, 0u };
    uint8_t used[voiceCount] = { 0u };
    uint8_t step = 0u;

    for (step = 0u; step < voiceCount; step++) {
        uint8_t cls = 0u;
        uint8_t idx = 0xFFu;
        uint8_t off = 0u;
        uint8_t seed = (uint8_t)(
            st->classAcc ^
            step ^
            (uint8_t)((st->s0 >> (8u * (step & 3u))) & 0xFFu) ^
            (uint8_t)((step & 1u) ? st->taint : 0xA5u)
            );

            // Opaque selector keeps class routing less obvious in static reading.
        if (opaqueAlways(seed + step)) {
            cls = (uint8_t)(opaqueScramble(seed) & 3u);
            }
        else {
            cls = (uint8_t)((seed + 1u) & 3u);
            }

        st->classHist[step] = cls;

        for (off = 0u; off < 4u; off++) {
            uint8_t bucket = (uint8_t)((cls + off) & 3u);
            while (cursor[bucket] < 6u && used[bucketOrder[bucket][cursor[bucket]]] != 0u) {
                cursor[bucket]++;
                }
            if (cursor[bucket] < 6u) {
                idx = bucketOrder[bucket][cursor[bucket]];
                cursor[bucket]++;
                break;
                }
            }

        if (idx == 0xFFu) {
            for (idx = 0u; idx < voiceCount; idx++) {
                if (used[idx] == 0u) {
                    break;
                    }
                }
            }

        used[idx] = 1u;
        st->voiceOrder[step] = idx;
        (void)voiceTable[idx](st, in);
        }

    st->passCount = 0u;
    for (step = 0u; step < voiceCount; step++) {
        st->passCount = (uint8_t)(st->passCount + st->passMask[step]);
        }

    memset(st->classCounts, 0, sizeof(st->classCounts));
    for (step = 0u; step < voiceCount; step++) {
        st->classCounts[st->classHist[step]]++;
        }

    st->edge = 0u;
    for (step = 0u; step < (voiceCount - 1u); step++) {
        uint8_t c0 = st->classHist[step];
        uint8_t c1 = st->classHist[step + 1u];
        uint8_t p = st->passMask[st->voiceOrder[step]];
        uint16_t term = (uint16_t)(((c0 << 2u) ^ c1 ^ p) * (uint8_t)(0x11u + step * 7u));
        st->edge = (uint16_t)((st->edge + term) % 65521u);
        }
    }

static int stateMachineGate(const choirState_t* st) {
    size_t i = 0u;
    if (st->edge != 14789u) {
        return 0;
        }
    for (i = 0u; i < 4u; i++) {
        if (st->classCounts[i] != realCountExpected[i]) {
            return 0;
            }
        }
    return 1;
    }

    // Early gate for fake branch A.
static int earlyStateGate(const choirState_t* st) {
    size_t i = 0u;
    if (st->edge != 14031u) {
        return 0;
        }
    for (i = 0u; i < 4u; i++) {
        if (st->classCounts[i] != earlyCountExpected[i]) {
            return 0;
            }
        }
    return 1;
    }

    // Cross-voice constraints are split into core and hidden-late checks.
static void constraintGate(const choirState_t* st, const uint8_t in[rawTokenLen], int* coreOk, int* lateOk) {
    uint8_t eq[7];
    uint8_t expected[7];
    size_t i = 0u;
    uint8_t lateValue = 0u;

    eq[0] = (uint8_t)(st->trace[2] + st->trace[17] + in[0]);
    eq[1] = (uint8_t)(st->trace[5] ^ st->trace[12] ^ in[7]);
    eq[2] = (uint8_t)(st->trace[8] + st->trace[9] + st->trace[10]);
    eq[3] = (uint8_t)(st->trace[4] - st->trace[15] + in[11]);
    eq[4] = (uint8_t)(st->trace[1] ^ st->trace[6] ^ st->trace[18]);
    eq[5] = (uint8_t)(in[3] + in[14] + st->trace[22]);
    eq[6] = (uint8_t)(st->trace[0] + in[19] - st->trace[23]);

    for (i = 0u; i < 7u; i++) {
        expected[i] = (uint8_t)(coreA[i] ^ coreB[i]);
        }

    *coreOk = 1;
    for (i = 0u; i < 7u; i++) {
        if (eq[i] != expected[i]) {
            *coreOk = 0;
            break;
            }
        }

    lateValue = (uint8_t)((st->trace[21] ^ st->trace[7]) + in[19]);
    *lateOk = (lateValue == 159u) ? 1 : 0;
    }

    // Computes real and decoy signatures from final state and trace.
static void computeSignatures(choirState_t* st, const uint8_t in[rawTokenLen]) {
    uint32_t sigA = 0x811C9DC5u;
    uint32_t sigB = 0x9E3779B9u;
    size_t i = 0u;

    for (i = 0u; i < voiceCount; i++) {
        sigA ^= (uint32_t)((st->trace[i] + (uint8_t)(i * 17u)) & 0xFFu);
        sigA *= 0x01000193u;
        }
    sigA ^= st->s1;

    for (i = 0u; i < rawTokenLen; i++) {
        sigB = rotl32(sigB ^ (uint32_t)((in[i] + (uint8_t)(i * 9u)) & 0xFFu), 5u);
        sigB += 0x7F4A7C15u + (uint32_t)(i * 0x1F123BB5u);
        }
    sigB ^= st->s2;

    st->sigA = sigA;
    st->sigB = sigB;
    st->chord = (uint8_t)(((sigA >> 8u) ^ (sigB >> 16u) ^ (st->passCount << 3u) ^ st->taint) & 0xFFu);
    }

static int signatureGateReal(const choirState_t* st) {
    uint32_t add = loadSplitWord(realAddPart);
    uint32_t goal = loadSplitWord(realGoalPart);
    uint32_t value = ((st->sigA ^ rotl32(st->sigB, 9u)) + add);
    return (value == goal) ? 1 : 0;
    }

static int signatureGateDecoy(const choirState_t* st) {
    uint32_t add = loadSplitWord(fakeAddPart);
    uint32_t goal = loadSplitWord(fakeGoalPart);
    uint32_t value = ((st->sigB ^ rotl32(st->sigA, 7u)) + add);
    return (value == goal) ? 1 : 0;
    }

static uint8_t deriveRealKeyByte(const choirState_t* st, size_t i) {
    uint8_t salt = (uint8_t)(loadSplitByte(realSaltA, realSaltB, i % 5u));
    uint8_t key = (uint8_t)(
        ((st->s0 >> (8u * (i % 4u))) & 0xFFu) ^
        ((st->s1 >> (8u * ((i + 1u) % 4u))) & 0xFFu) ^
        ((st->s2 >> (8u * ((i + 2u) % 4u))) & 0xFFu) ^
        salt ^
        (uint8_t)(0x33u + (uint8_t)(i * 7u))
        );
    return key;
    }

    // Fake branch uses per-branch folding with state-derived seed.
static uint8_t deriveFakeKeyByte(const choirState_t* st, size_t i, uint8_t foldConst) {
    uint8_t base = (uint8_t)((st->s0 ^ st->s1 ^ st->s2 ^ st->s3) & 0xFFu);
    uint8_t seed = (uint8_t)(base ^ foldConst);
    uint8_t salt = (uint8_t)(loadSplitByte(fakeSaltA, fakeSaltB, i % 4u));
    uint8_t key = (uint8_t)(
        (uint8_t)((seed << 4u) | (seed & 0x0Fu)) ^
        salt ^
        (uint8_t)(0x5Au + (uint8_t)(i * 11u))
        );
    return key;
    }

static void decryptRealFlag(const choirState_t* st, char out[sizeof(realEnc) + 1u]) {
    size_t i = 0u;
    for (i = 0u; i < sizeof(realEnc); i++) {
        out[i] = (char)(realEnc[i] ^ deriveRealKeyByte(st, i));
        }
    out[sizeof(realEnc)] = '\0';
    }

static void decryptFakeFlag(const choirState_t* st, char out[sizeof(fakeEnc) + 1u], uint8_t foldConst) {
    size_t i = 0u;
    for (i = 0u; i < sizeof(fakeEnc); i++) {
        out[i] = (char)(fakeEnc[i] ^ deriveFakeKeyByte(st, i, foldConst));
        }
    out[sizeof(fakeEnc)] = '\0';
    }

static outcome_t chooseOutcome(
    const choirState_t* st,
    int stateOk,
    int earlyOk,
    int coreOk,
    int lateOk,
    int sigReal,
    int sigDecoy
) {
    if (st->passCount == 24u && stateOk && coreOk && lateOk && sigReal) {
        return outcomeReal;
        }
    if (st->passCount == 24u && sigDecoy) {
        return outcomeFakeB;
        }
    if (st->passCount >= 18u && earlyOk && !lateOk) {
        return outcomeFakeA;
        }
    if (st->passCount >= 14u && st->chord == 0x8Au && (((st->sigA ^ st->sigB) & 0xFFu) == 0x37u)) {
        return outcomeFakeC;
        }
    return outcomeDeny;
    }

int main(void) {
    char line[128];
    uint8_t token[rawTokenLen];
    choirState_t st;
    int stateOk = 0;
    int earlyOk = 0;
    int coreOk = 0;
    int lateOk = 0;
    int sigReal = 0;
    int sigDecoy = 0;
    outcome_t outcome = outcomeDeny;

    puts("Ashen Choir");
    puts("At night, Ashengrave listens to the songs of the lost.");
    fputs("Offer your ritual> ", stdout);

    if (fgets(line, sizeof(line), stdin) == NULL) {
        puts(denyMsg);
        return 0;
        }
    line[strcspn(line, "\r\n")] = '\0';

    if (!parseToken(line, token)) {
        puts(denyMsg);
        return 0;
        }

    initState(&st, token);
    dispatchVoices(&st, token);
    constraintGate(&st, token, &coreOk, &lateOk);
    computeSignatures(&st, token);

    stateOk = stateMachineGate(&st);
    earlyOk = earlyStateGate(&st);
    sigReal = signatureGateReal(&st);
    sigDecoy = signatureGateDecoy(&st);
    outcome = chooseOutcome(&st, stateOk, earlyOk, coreOk, lateOk, sigReal, sigDecoy);

    if (outcome == outcomeReal) {
        char out[sizeof(realEnc) + 1u];
        decryptRealFlag(&st, out);
        puts(out);
        return 0;
        }

    if (outcome == outcomeFakeA) {
        char out[sizeof(fakeEnc) + 1u];
        decryptFakeFlag(&st, out, 0x52u);
        puts(out);
        return 0;
        }

    if (outcome == outcomeFakeB) {
        char out[sizeof(fakeEnc) + 1u];
        decryptFakeFlag(&st, out, 0xABu);
        puts(out);
        return 0;
        }

    if (outcome == outcomeFakeC) {
        uint32_t check = (st.sigA ^ st.sigB ^ st.s3) & 0xFFFu;
        printf("Ritual accepted. checksum=0x%03X\n", check);
        return 0;
        }

    puts(denyMsg);
    return 0;
    }
