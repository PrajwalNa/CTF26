#include "proto.h"
#include "crypto.h"
#include <string.h>
#include <stdlib.h>

// Serialize header fields in wire order (little-endian for multi-byte fields)
int seH(lichHeader_t* hdr, uint8_t* buf, uint32_t bufLen) {
    if (bufLen < HEADER_SIZE) return -1;

    int pos = 0;
    buf[pos++] = hdr->protoId[0];
    buf[pos++] = hdr->protoId[1];
    buf[pos++] = hdr->msgType;
    uint32_t len = hdr->payloadLen;
    buf[pos++] = (len) & 0xFF;
    buf[pos++] = (len >> 8) & 0xFF;
    buf[pos++] = (len >> 16) & 0xFF;
    buf[pos++] = (len >> 24) & 0xFF;

    for (int i = 0; i < MAGIC_SIZE; i++) {
        buf[pos++] = hdr->magic[i];
        }

    buf[pos++] = hdr->version;
    memcpy(&buf[pos], hdr->hash, HASH_SIZE);
    pos += HASH_SIZE;

    return pos;
    }

// Deserialize header fields from wire order (LE)
int dseH(uint8_t* buf, uint32_t bufLen, lichHeader_t* hdr) {
    if (bufLen < HEADER_SIZE) return -1;

    int pos = 0;
    hdr->protoId[0] = buf[pos++];
    hdr->protoId[1] = buf[pos++];
    hdr->msgType = buf[pos++];
    hdr->payloadLen = buf[pos++];
    hdr->payloadLen |= (buf[pos++] << 8);
    hdr->payloadLen |= (buf[pos++] << 16);
    hdr->payloadLen |= (buf[pos++] << 24);

    for (int i = 0; i < MAGIC_SIZE; i++) {
        hdr->magic[i] = buf[pos++];
        }

    hdr->version = buf[pos++];
    memcpy(hdr->hash, &buf[pos], HASH_SIZE);
    pos += HASH_SIZE;

    return pos;
    }

// Verify payload hash (magic/version checks are handled by caller)
int vdH(lichHeader_t* hdr, uint8_t* payload, uint32_t payloadLen) {
    uint8_t comp[HASH_SIZE];
    int hType = (hdr->protoId[0] == 'A' && hdr->protoId[1] == 'R') ? HASH_MD5 : HASH_BLAKE3;
    if (hType == HASH_MD5) {
        md5H(payload, payloadLen, comp);
        return memcmp(hdr->hash, comp, 16) == 0;
        }
    else {
        b3H(payload, payloadLen, comp);
        return memcmp(hdr->hash, comp, HASH_SIZE) == 0;
        }
    }

// Parse Arise request payload
int pAReq(uint8_t* payload, uint32_t len, ariseReq_t* out) {
    if (len < 3) return -1;

    int pos = 0;
    out->magicPart = payload[pos++];
    out->magicPart |= (payload[pos++] << 8);
    out->version = payload[pos++];
    uint32_t hashLen = len - pos;
    if (hashLen >= sizeof(out->supportedHashes)) return -1;

    memcpy(out->supportedHashes, &payload[pos], hashLen);
    out->supportedHashes[hashLen] = 0;

    return 0;
    }

// Parse SoulBind credentials as two null-terminated fields (username, password)
int pSReq(uint8_t* payload, uint32_t len, soulbindReq_t* out) {
    if (!payload || !out || len == 0) return -1;

    uint32_t pos = 0;
    uint32_t uLen = (uint32_t)strnlen((char*)&payload[pos], len);
    if (uLen >= MAX_USERNAME_LEN) return -1;
    if (pos + uLen >= len) return -1;

    memcpy(out->username, &payload[pos], uLen);
    out->username[uLen] = 0;
    pos += uLen + 1;

    if (pos >= len) return -1;

    uint32_t pLen = (uint32_t)strnlen((char*)&payload[pos], len - pos);
    if (pLen >= MAX_PASSWORD_LEN) return -1;
    if (pos + pLen >= len) return -1;

    memcpy(out->password, &payload[pos], pLen);
    out->password[pLen] = 0;

    return 0;
    }

// Parse BoneCourier RTS payload
int pBCRts(uint8_t* payload, uint32_t len, boneCourierRts_t* out) {
    if (len < 4 + TOKEN_SIZE) return -1;

    int pos = 0;
    out->dataSize = payload[pos++];
    out->dataSize |= (payload[pos++] << 8);
    out->dataSize |= (payload[pos++] << 16);
    out->dataSize |= (payload[pos++] << 24);
    memcpy(out->token, &payload[pos], TOKEN_SIZE);

    return 0;
    }

// Parse BoneCourier Data payload
int pBCData(uint8_t* payload, uint32_t len, boneCourierData_t* out) {
    if (len < 16 + TOKEN_SIZE) return -1;

    int pos = 0;
    out->dataLen = len - 16 - TOKEN_SIZE;
    if (out->dataLen > MAX_CHUNK_SIZE) return -1;
    memcpy(out->data, &payload[pos], out->dataLen);
    pos += out->dataLen;
    memcpy(out->chunkHash, &payload[pos], 16);
    pos += 16;
    memcpy(out->token, &payload[pos], TOKEN_SIZE);

    return 0;
    }

// Encode Arise response payload
int eARes(ariseResp_t* resp, uint8_t* buf, uint32_t bufLen) {
    if (bufLen < 3 + strlen(resp->chosenHash)) return -1;

    int pos = 0;
    buf[pos++] = (resp->magicPart) & 0xFF;
    buf[pos++] = (resp->magicPart >> 8) & 0xFF;
    buf[pos++] = resp->version;
    uint32_t hLen = strlen(resp->chosenHash);
    memcpy(&buf[pos], resp->chosenHash, hLen);
    pos += hLen;

    return pos;
    }

// Encode SoulBind response payload
int eSBRes(soulbindResp_t* resp, uint8_t* buf, uint32_t bufLen) {
    if (bufLen < 1 + TOKEN_SIZE + 1) return -1;

    buf[0] = resp->accept;
    memcpy(&buf[1], resp->token, TOKEN_SIZE);
    buf[1 + TOKEN_SIZE] = resp->authLevel;
    if (resp->flag[0] != 0) {
        memcpy(&buf[1 + TOKEN_SIZE + 1], resp->flag, 15);
        return (1 + TOKEN_SIZE + 16);
        }
    return 1 + TOKEN_SIZE + 1;
    }

// Encode BoneCourier CTS payload
int eBCCts(boneCourierCts_t* cts, uint8_t* buf, uint32_t bufLen) {
    if (bufLen < 1) return -1;

    srand(42);
    // random accept/deny
    cts->accept = (rand() % 2 == 0) ? 1 : 0;
    buf[0] = cts->accept;

    return 1;
    }

// Build full protocol frame (header + payload) and compute payload hash
int bldMes(uint16_t protoId, uint8_t msgType, uint8_t* payload, uint32_t payloadLen, uint8_t* out, uint32_t outLen) {
    if (!out) return -1;
    if (payloadLen > 0 && !payload) return -1;
    if (outLen < HEADER_SIZE + payloadLen) return -1;

    lichHeader_t hdr;
    // Zero-init avoids leaking stack bytes when Arise uses 16-byte MD5 hash
    memset(&hdr, 0, sizeof(hdr));
    hdr.protoId[0] = (protoId >> 8) & 0xFF;
    hdr.protoId[1] = protoId & 0xFF;
    hdr.msgType = msgType;
    hdr.payloadLen = payloadLen;
    if (protoId == PROTO_ARISE) {
        memset(hdr.magic, 0, MAGIC_SIZE);
        }
    else {
        const uint8_t m[MAGIC_SIZE] = { MAGIC_B0, MAGIC_B1, MAGIC_B2, MAGIC_B3, MAGIC_B4, MAGIC_B5 };
        memcpy(hdr.magic, m, MAGIC_SIZE);
        }
    hdr.version = PROTOCOL_VERSION;
    static uint8_t emptyPayload = 0;
    uint8_t* payloadPtr = (payloadLen == 0) ? &emptyPayload : payload;

    int hType = (hdr.protoId[0] == 'A' && hdr.protoId[1] == 'R') ? HASH_MD5 : HASH_BLAKE3;
    if (hType == HASH_MD5) {
        md5H(payloadPtr, payloadLen, hdr.hash);
        }
    else {
        b3H(payloadPtr, payloadLen, hdr.hash);
        }

    int hLen = seH(&hdr, out, outLen);
    if (hLen < 0) return -1;

    if (payloadLen > 0) {
        memcpy(&out[hLen], payload, payloadLen);
        }

    return hLen + payloadLen;
    }
