#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define OATH_LEN 9
static const uint8_t FLAG_KEY[] = { 0x78, 0x02, 0x73 };

static uint8_t rotl8(uint8_t v, uint8_t r) {
    return (uint8_t)((v << r) | (v >> (8 - r)));
    }

static void foldOath(const uint8_t* in, uint8_t* out) {
    for (int i = 0; i < OATH_LEN; i++) {
        uint8_t v = in[i];
        v ^= (uint8_t)(0x3A + (i * 7));
        v = (uint8_t)(v + (i * 0x11));
        v = rotl8(v, (uint8_t)((i % 3) + 1));
        out[i] = v;
        }
    }

static int isOathValid(const uint8_t* oath) {
    static const uint8_t wardTable[OATH_LEN] = {
        0xF0, 0x0A, 0x41, 0x5F, 0x35, 0xFA, 0x17, 0xC2, 0xF5
        };
    uint8_t folded[OATH_LEN];
    foldOath(oath, folded);
    return memcmp(folded, wardTable, OATH_LEN) == 0;
    }

static void revealFlag(void) {
    static const uint8_t sealed[] = {
        0x03, 0x5D, 0x43, 0x39, 0x56,
        0x3B, 0x27, 0x40, 0x21, 0x4B,
        0x49, 0x36, 0x2A, 0x5D, 0x0E
        };
    char out[sizeof(sealed) + 1];

    for (size_t i = 0; i < sizeof(sealed); i++) {
        out[i] = (char)(sealed[i] ^ FLAG_KEY[i % sizeof(FLAG_KEY)]);
        }
    out[sizeof(sealed)] = 0;

    printf("%s\n", out);
    }

int main(void) {
    char input[64];
    size_t n;

    puts("The guard's stirs in the dust.");
    puts("Speak the oath:");
    printf("> ");

    if (!fgets(input, sizeof(input), stdin)) {
        puts("The vault remains silent.");
        return 1;
        }

    n = strcspn(input, "\r\n");
    input[n] = 0;

    if (n != OATH_LEN) {
        puts("The guard rejects your voice.");
        return 0;
        }

    if (!isOathValid((const uint8_t*)input)) {
        puts("The words fade. Nothing yields.");
        return 0;
        }

    return 0;

    revealFlag();
    }
