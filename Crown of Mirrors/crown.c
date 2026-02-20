#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define STAR_COUNT 20
#define INPUT_LEN 24
#define DENY_MSG "The throne remains silent."

// Bitfield filled before main, used to select real/decoy execution paths.
static volatile uint32_t g_preTaint = 0;

// Split key tables used to reconstruct bytes at runtime.
static const uint8_t keyA[6] = { 0xC1u, 0xD2u, 0xA3u, 0xB4u, 0x95u, 0x86u };
static const uint8_t keyB[6] = { 0x87u, 0x93u, 0xEFu, 0xFFu, 0xD0u, 0xC8u };
static const uint8_t saltA[3] = { 0x55u, 0xE3u, 0x18u };
static const uint8_t saltB[3] = { 0x5Fu, 0x3Cu, 0x19u };

// Small rotate helpers used across signature mixers.
static uint32_t rol32(uint32_t v, unsigned int r) {
    return (v << r) | (v >> (32u - r));
    }

static uint16_t rol16(uint16_t v, unsigned int r) {
    return (uint16_t)((v << r) | (v >> (16u - r)));
    }

// Anti-debug check 1: direct WinAPI debugger presence.
static uint32_t chkApiDebug(void) {
    return IsDebuggerPresent() ? 1u : 0u;
    }

// Anti-debug check 2: remote debugger presence probe.
static uint32_t chkRemoteDebug(void) {
    BOOL remote = FALSE;
    if (CheckRemoteDebuggerPresent(GetCurrentProcess(), &remote) && remote) {
        return 1u;
        }
    return 0u;
    }

// Anti-debug check 3: very low sleep delta can indicate time tampering.
static uint32_t chkTimingSkew(void) {
    LARGE_INTEGER freq;
    LARGE_INTEGER t0;
    LARGE_INTEGER t1;

    if (!QueryPerformanceFrequency(&freq) || !QueryPerformanceCounter(&t0)) {
        return 0u;
        }

    Sleep(25);

    if (!QueryPerformanceCounter(&t1)) {
        return 0u;
        }

    {
    double elapsedMs = ((double)(t1.QuadPart - t0.QuadPart) * 1000.0) / (double)freq.QuadPart;
    return (elapsedMs < 20.0) ? 1u : 0u;
    }
    }

// Constructor runs before main and combines all taint bits.
__attribute__((constructor)) static void preInitGate(void) {
    uint32_t taint = 0u;

    taint |= chkApiDebug();
    taint |= (chkRemoteDebug() << 1);
    taint |= (chkTimingSkew() << 2);

    g_preTaint = taint;
    }

// Route selector:
// 0 -> real path, 1 -> decoy no-flag path, 2 -> decoy fake-flag path.
static int selectPath(uint32_t taint) {
    if (taint == 0u) {
        return 0;
        }
    if ((taint & 1u) == 0u) {
        return 1;
        }
    return 2;
    }

// Reads a single line and trims trailing newline bytes.
static int readInput(char* buf, size_t bufLen) {
    size_t n;

    if (buf == NULL || bufLen == 0u) {
        return 0;
        }

    if (fgets(buf, (int)bufLen, stdin) == NULL) {
        return 0;
        }

    n = strcspn(buf, "\r\n");
    buf[n] = '\0';
    return 1;
    }

// Enforces XXXX-XXXX-XXXX-XXXX-XXXX and flattens to 20 letters.
static int parseStars(const char* in, char out[STAR_COUNT]) {
    size_t i;
    size_t w = 0u;

    if (in == NULL || out == NULL) {
        return 0;
        }

    if (strlen(in) != INPUT_LEN) {
        return 0;
        }

    for (i = 0u; i < INPUT_LEN; i++) {
        if (i == 4u || i == 9u || i == 14u || i == 19u) {
            if (in[i] != '-') {
                return 0;
                }
            continue;
            }

        if (in[i] == '-') {
            return 0;
            }

        if (w >= STAR_COUNT) {
            return 0;
            }

        out[w++] = in[i];
        }

    return (w == STAR_COUNT) ? 1 : 0;
    }

// Strict uppercase gate for all flattened star letters.
static int allUpperAZ(const char in[STAR_COUNT]) {
    size_t i;

    for (i = 0u; i < STAR_COUNT; i++) {
        if (in[i] < 'A' || in[i] > 'Z') {
            return 0;
            }
        }

    return 1;
    }

// Real crown stage:
// validates per-group tags, then computes sigA.
static uint32_t crownReal(const char c[STAR_COUNT]) {
    static const uint16_t tag[5] = { 0x9720u, 0xFB37u, 0x8BC0u, 0x6488u, 0x48CFu };
    static const uint16_t k[5] = { 0xFB6Fu, 0x931Cu, 0xBD97u, 0x8756u, 0x89CCu };

    uint32_t sig = 0x811C9DC5u;
    size_t g;
    size_t i;

    for (g = 0u; g < 5u; g++) {
        uint16_t raw = (uint16_t)(((uint16_t)(uint8_t)c[g * 4u] << 8u) | (uint16_t)(uint8_t)c[g * 4u + 1u]);
        uint16_t mix = (uint16_t)(((uint16_t)(uint8_t)c[g * 4u + 2u] << 8u) | (uint16_t)(uint8_t)c[g * 4u + 3u]);
        uint16_t calc = (uint16_t)(raw ^ rol16(mix, 3u) ^ k[g]);

        if (calc != tag[g]) {
            return 0u;
            }
        }

    for (i = 0u; i < STAR_COUNT; i++) {
        sig ^= (uint32_t)(((uint8_t)c[i] + (uint8_t)(i * 13u)) & 0xFFu);
        sig *= 0x01000193u;
        }

    sig ^= 0xAE88B2B5u;
    return sig;
    }

// Real mirror stage:
// enforces relation constraints, then computes sigB.
static uint32_t mirrorReal(const char c[STAR_COUNT], int* ok) {
    uint32_t sig = 0x9E3779B9u;
    size_t i;

    if (ok == NULL) {
        return 0u;
        }

    *ok = 0;

    if (((uint32_t)(uint8_t)c[0] + (uint32_t)(uint8_t)c[19]) != 159u) {
        return 0u;
        }

    if (((uint8_t)c[3] ^ (uint8_t)c[12]) != 0u) {
        return 0u;
        }

    if ((((c[4] - 'A') + (c[5] - 'A') + (c[6] - 'A')) % 26) != 5) {
        return 0u;
        }

    if (((int)c[1] - (int)c[8]) != 1) {
        return 0u;
        }

    if (((uint8_t)c[10] ^ (uint8_t)c[14]) != 26u) {
        return 0u;
        }

    if (((uint32_t)(uint8_t)c[7] + (uint32_t)(uint8_t)c[11] + (uint32_t)(uint8_t)c[15]) != 224u) {
        return 0u;
        }

    for (i = 0u; i < STAR_COUNT; i++) {
        sig = rol32(sig ^ (((uint32_t)(uint8_t)c[i] + (uint32_t)(i * 7u)) & 0xFFu), 5u);
        sig += 0x7F4A7C15u + (uint32_t)(i * 0x1F123BB5u);
        }

    *ok = 1;
    return sig;
    }

// Final real gate linking sigA and sigB.
static int realFinalGate(uint32_t sigA, uint32_t sigB) {
    return (((sigA ^ rol32(sigB, 7u)) + 0x27D4EB2Du) == 0x613283A6u) ? 1 : 0;
    }

// Decoy path A crown stage with separate permutation/constants.
static uint32_t crownDecoyNone(const char c[STAR_COUNT]) {
    static const uint8_t p[STAR_COUNT] = {
        2u, 0u, 3u, 1u,
        6u, 4u, 7u, 5u,
        10u, 8u, 11u, 9u,
        14u, 12u, 15u, 13u,
        18u, 16u, 19u, 17u
        };

    static const uint16_t tag[5] = { 0xA47Bu, 0x8D11u, 0x7C30u, 0x9124u, 0xB06Fu };

    uint32_t sig = 0x13579BDFu;
    size_t g;

    for (g = 0u; g < 5u; g++) {
        uint16_t v = (uint16_t)(((uint16_t)(uint8_t)c[p[g * 4u]] << 8u) | (uint16_t)(uint8_t)c[p[g * 4u + 1u]]);
        uint16_t w = (uint16_t)(((uint16_t)(uint8_t)c[p[g * 4u + 2u]] << 8u) | (uint16_t)(uint8_t)c[p[g * 4u + 3u]]);
        uint16_t mix = (uint16_t)(v + rol16(w, 1u) + (uint16_t)(0x1111u * (g + 1u)));

        if (mix != tag[g]) {
            return 0u;
            }

        sig = rol32(sig ^ (uint32_t)mix, (unsigned int)(g + 3u));
        sig += (uint32_t)(0x01010101u * (g + 1u));
        }

    return sig;
    }

// Decoy path A mirror stage.
static uint32_t mirrorDecoyNone(const char c[STAR_COUNT], int* ok) {
    uint32_t sig = 0xCAFEBABEu;
    size_t i;

    if (ok == NULL) {
        return 0u;
        }

    *ok = 0;

    if (((uint8_t)c[0] + (uint8_t)c[5] - (uint8_t)c[10]) != 80) {
        return 0u;
        }

    if (((uint8_t)c[3] ^ (uint8_t)c[7] ^ (uint8_t)c[11]) != 0x15u) {
        return 0u;
        }

    if (((uint8_t)c[4] + (uint8_t)c[9] + (uint8_t)c[14] + (uint8_t)c[19]) != 306u) {
        return 0u;
        }

    for (i = 0u; i < STAR_COUNT; i++) {
        sig ^= (uint32_t)(uint8_t)c[i] + (uint32_t)(i * 0x31u);
        sig = rol32(sig, 7u);
        sig += 0x0043210Fu;
        }

    *ok = 1;
    return sig;
    }

// Decoy path B crown stage with its own constants.
static uint32_t crownDecoyFake(const char c[STAR_COUNT]) {
    static const uint16_t tag[5] = { 0x09EBu, 0xBE83u, 0x553Du, 0xCEA3u, 0xFB4Du };
    static const uint16_t k[5] = { 0x8F8Eu, 0xBAF0u, 0x3386u, 0x6432u, 0xD097u };

    uint32_t sig = 0xA5B3571Du;
    size_t g;
    size_t i;

    for (g = 0u; g < 5u; g++) {
        uint16_t raw = (uint16_t)(((uint16_t)(uint8_t)c[g * 4u] << 8u) | (uint16_t)(uint8_t)c[g * 4u + 1u]);
        uint16_t mix = (uint16_t)(((uint16_t)(uint8_t)c[g * 4u + 2u] << 8u) | (uint16_t)(uint8_t)c[g * 4u + 3u]);
        uint16_t calc = (uint16_t)(raw ^ rol16(mix, 5u) ^ k[g]);

        if (calc != tag[g]) {
            return 0u;
            }
        }

    for (i = 0u; i < STAR_COUNT; i++) {
        sig ^= ((uint32_t)(uint8_t)c[i] * (uint32_t)(i + 3u));
        sig = rol32(sig, 9u);
        sig += 0x10204081u + (uint32_t)(i * 0x1337u);
        }

    return sig;
    }

// Decoy path B mirror stage.
static uint32_t mirrorDecoyFake(const char c[STAR_COUNT], int* ok) {
    uint32_t sig = 0x6C8E9CF5u;
    size_t i;

    if (ok == NULL) {
        return 0u;
        }

    *ok = 0;

    if (((uint32_t)(uint8_t)c[2] + (uint32_t)(uint8_t)c[17]) != 168u) {
        return 0u;
        }

    if (((uint8_t)c[0] ^ (uint8_t)c[19]) != 26u) {
        return 0u;
        }

    if ((((c[4] - 'A') + (c[9] - 'A') + (c[13] - 'A')) % 26) != 0) {
        return 0u;
        }

    if (((int)c[6] - (int)c[1]) != 3) {
        return 0u;
        }

    if (((uint8_t)c[10] ^ (uint8_t)c[14]) != 14u) {
        return 0u;
        }

    if (((uint32_t)(uint8_t)c[3] + (uint32_t)(uint8_t)c[8] + (uint32_t)(uint8_t)c[12]) != 211u) {
        return 0u;
        }

    for (i = 0u; i < STAR_COUNT; i++) {
        sig += (((uint32_t)(uint8_t)c[i] ^ (uint32_t)(i * 17u)) & 0xFFu) + 0x9Du;
        sig = rol32(sig, (unsigned int)((i % 11u) + 3u));
        sig ^= 0x7F4A9E21u;
        }

    *ok = 1;
    return sig;
    }

// Final decoy gate for fake flag path.
static int fakeFinalGate(uint32_t sigA, uint32_t sigB) {
    return (((sigA ^ rol32(sigB, 3u)) + 0x31D9BEEFu) == 0x628E1F60u) ? 1 : 0;
    }

// Shared keystream byte generator using reconstructed key/salt bytes.
static uint8_t keyByte(size_t i) {
    uint8_t keyWordByte = (uint8_t)(keyA[i % 6u] ^ keyB[i % 6u]);
    uint8_t saltByte = (uint8_t)(saltA[i % 3u] ^ saltB[i % 3u]);
    return (uint8_t)(keyWordByte ^ saltByte);
    }

// Shared XOR decrypt helper for embedded payload bytes.
static void xorDecrypt(const uint8_t* enc, size_t n, char* out) {
    size_t i;

    for (i = 0u; i < n; i++) {
        out[i] = (char)(enc[i] ^ keyByte(i));
        }

    out[n] = '\0';
    }

// Decrypts real reward payload.
static void decryptRealFlag(char out[64]) {
    static const uint8_t enc[] = {
        0x37u, 0xCDu, 0x7Au, 0x00u, 0xC8u, 0x09u, 0x0Du, 0xD2u, 0x01u,
        0x1Eu, 0xCEu, 0x07u, 0x1Eu, 0xAEu, 0x03u, 0x72u, 0xE7u
        };

    xorDecrypt(enc, sizeof(enc), out);
    }

// Decrypts fake reward payload.
static void decryptFakeFlag(char out[64]) {
    static const uint8_t enc[] = {
        0x0Eu, 0xCCu, 0x7Du, 0x0Au, 0xA9u, 0x01u, 0x13u,
        0xCAu, 0x05u, 0x13u, 0xAAu, 0x01u, 0x7Fu
        };

    xorDecrypt(enc, sizeof(enc), out);
    }

// Real path orchestrator.
static int runRealPath(const char c[STAR_COUNT], char out[64]) {
    uint32_t sigA;
    uint32_t sigB;
    int ok = 0;

    sigA = crownReal(c);
    if (sigA == 0u) {
        return 0;
        }

    sigB = mirrorReal(c, &ok);
    if (!ok) {
        return 0;
        }

    if (!realFinalGate(sigA, sigB)) {
        return 0;
        }

    decryptRealFlag(out);
    return 1;
    }

// Decoy path A orchestrator.
// Even if internal checks pass, it never returns success.
static int runDecoyNoFlagPath(const char c[STAR_COUNT]) {
    uint32_t sigA;
    uint32_t sigB;
    int ok = 0;

    sigA = crownDecoyNone(c);
    if (sigA == 0u) {
        return 0;
        }

    sigB = mirrorDecoyNone(c, &ok);
    if (!ok || sigB == 0u) {
        return 0;
        }

    return 0;
    }

// Decoy path B orchestrator.
static int runDecoyFakePath(const char c[STAR_COUNT], char out[64]) {
    uint32_t sigA;
    uint32_t sigB;
    int ok = 0;

    sigA = crownDecoyFake(c);
    if (sigA == 0u) {
        return 0;
        }

    sigB = mirrorDecoyFake(c, &ok);
    if (!ok) {
        return 0;
        }

    if (!fakeFinalGate(sigA, sigB)) {
        return 0;
        }

    decryptFakeFlag(out);
    return 1;
    }

// Main flow:
// parse input, choose path from pre-main taint, print success output or generic denial.
int main(void) {
    char input[128] = { 0 };
    char stars[STAR_COUNT] = { 0 };
    char flagOut[64] = { 0 };
    int success = 0;

    puts("Five stars must align to awaken the throne.");

    if (!readInput(input, sizeof(input))) {
        puts(DENY_MSG);
        return 0;
        }

    if (!parseStars(input, stars) || !allUpperAZ(stars)) {
        puts(DENY_MSG);
        return 0;
        }

    switch (selectPath(g_preTaint)) {
        case 0:
            success = runRealPath(stars, flagOut);
            break;
        case 1:
            success = runDecoyNoFlagPath(stars);
            break;
        default:
            success = runDecoyFakePath(stars, flagOut);
            break;
        }

    if (success) {
        puts(flagOut);
        }
    else {
        puts(DENY_MSG);
        }

    return 0;
    }
