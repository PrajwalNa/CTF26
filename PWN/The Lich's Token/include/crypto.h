#pragma once

#include <stdint.h>

// Blake3 hash (32 bytes output)
void b3H(uint8_t* data, uint32_t len, uint8_t* out);

// MD5 hash (16 bytes output)
void md5H(uint8_t* data, uint32_t len, uint8_t* out);

// Base64 encode
int b64E(uint8_t* data, uint32_t len, char* out, uint32_t outLen);

// Base64 decode
int b64D(const char* data, uint8_t* out, uint32_t outLen);

// Generate random token
void gT(uint8_t* out, uint32_t len);

// Hash algorithms enum
#define HASH_BLAKE3 0
#define HASH_MD5 1
