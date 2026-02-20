#include "crypto.h"
#include <blake3.h>
#include <openssl/md5.h>
#include <string.h>
#include <stdlib.h>

// b64Tbl = base64 alphabet table
static const char b64Tbl[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

// b3H: Blake3 Hash - Hash data with Blake3
void b3H(uint8_t* data, uint32_t len, uint8_t* out) {
    // ctx = blake3_hasher context
    blake3_hasher ctx;
    blake3_hasher_init(&ctx);
    blake3_hasher_update(&ctx, data, len);
    blake3_hasher_finalize(&ctx, out, 32);  // 32 bytes for Blake3 output
    }

// md5H: MD5 Hash - Hash data with MD5
void md5H(uint8_t* data, uint32_t len, uint8_t* out) {
    // ctx = MD5 context
    MD5_CTX ctx;
    MD5_Init(&ctx);
    MD5_Update(&ctx, data, len);
    MD5_Final(out, &ctx);
    }

// b64E: Base64 Encode - Encode binary to base64 string
int b64E(uint8_t* data, uint32_t len, char* out, uint32_t outLen) {
    // i = input position, j = output position
    uint32_t i = 0, j = 0;
    // buf = 3-byte input buffer
    uint8_t buf[3];

    while (i < len) {
        // n = bytes in buffer
        int n = 0;
        buf[0] = buf[1] = buf[2] = 0;

        while (i < len&& n < 3) {
            buf[n++] = data[i++];
            }

        if (j + 4 > outLen) return -1;

        out[j++] = b64Tbl[(buf[0] >> 2) & 0x3F];
        out[j++] = b64Tbl[(((buf[0] & 0x03) << 4) | (buf[1] >> 4)) & 0x3F];
        out[j++] = n > 1 ? b64Tbl[(((buf[1] & 0x0F) << 2) | (buf[2] >> 6)) & 0x3F] : '=';
        out[j++] = n > 2 ? b64Tbl[buf[2] & 0x3F] : '=';
        }

    out[j] = 0;
    return j;
    }

// b64D: Base64 Decode - Decode base64 string to binary
int b64D(const char* data, uint8_t* out, uint32_t outLen) {
    // i = input position, j = output position
    uint32_t i = 0, j = 0;
    // buf = 4-byte input buffer
    uint8_t buf[4];

    while (data[i] && data[i] != '=') {
        // n = bytes in buffer
        int n = 0;
        memset(buf, 0, 4);

        while (n < 4 && data[i] && data[i] != '=') {
            // pos = position in base64 table
            char* pos = strchr(b64Tbl, data[i++]);
            if (!pos) return -1;
            buf[n++] = pos - b64Tbl;
            }

        if (n == 0) break;

        if (j + 1 > outLen) return -1;
        out[j++] = ((buf[0] << 2) | (buf[1] >> 4)) & 0xFF;

        if (n > 2 && j + 1 <= outLen) {
            out[j++] = (((buf[1] & 0x0F) << 4) | (buf[2] >> 2)) & 0xFF;
            }

        if (n > 3 && j + 1 <= outLen) {
            out[j++] = (((buf[2] & 0x03) << 6) | buf[3]) & 0xFF;
            }
        }

    return j;
    }

// gT: Generate Token - Create random token bytes
void gT(uint8_t* out, uint32_t len) {
    for (uint32_t i = 0; i < len; i++) {
        out[i] = rand() & 0xFF;
        }
    }
