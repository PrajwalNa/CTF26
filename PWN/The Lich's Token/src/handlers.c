#include "handlers.h"
#include "proto.h"
#include "net.h"
#include "state.h"
#include "config.h"
#include "error.h"
#include "crypto.h"
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <time.h>
#include <winsock2.h>
#include <ws2tcpip.h>


#define HS_CACHE_SIZE 32    // Cache size for client IP handshakes
#define HS_TTL_SEC 30       // Time-to-live for handshake cache entries (30 seconds)

typedef struct {
    uint32_t ip;
    time_t ts;
    int valid;
    } hsEntry_t;            // Handshake cache entry structure

// Handshake cache table
static hsEntry_t hsTbl[HS_CACHE_SIZE];

// Hardcoded passphrase (to be discovered in binary)
static const char HARDCODED_PASSPHRASE[] = "SBLCHT42";

// XOR byte for obfuscating "elevateRequest" string in binary
#define ELEV_REQ_XOR 0x5A
// Obfuscated "elevateRequest" string (XORed with 0x5A)
static const uint8_t ELEV_REQ_OBF[] = {
    0x3F, 0x36, 0x3F, 0x2C, 0x3B, 0x2E, 0x3F,
    0x08, 0x3F, 0x2B, 0x2F, 0x3F, 0x29, 0x2E
    };

// key for encrypted flag for elevation
static const uint8_t ELE_KEY[] = { 0xF0, 0x15, 0xAC, 0x71, 0xEE };
// Obfuscated flag
static const uint8_t ELE_FLAG_BYTES[] = { 0x8B, 0x60, 0xC2, 0x35, 0xAB, 0xB1, 0x51, 0xF3, 0x25, 0xA6, 0xA2, 0x25, 0xE2, 0x42, 0x93 };

// Check whether client-supported hash list includes Blake3
static int hasB3(const char* list) {
    if (!list) return 0;

    const char* tag = "blake3";
    for (const char* p = list; *p; p++) {
        int i = 0;
        while (tag[i] && p[i] && tolower((unsigned char)p[i]) == tag[i]) {
            i++;
            }
        if (!tag[i]) return 1;
        }

    return 0;
    }


// Resolve the peer IPv4 address for this connection
static int gtPeerIp(int sock, uint32_t* ipOut) {
    if (!ipOut) return 0;

    struct sockaddr_in pAddr;
    int pLen = sizeof(pAddr);
    if (getpeername((SOCKET)sock, (struct sockaddr*)&pAddr, &pLen) != 0) return 0;
    if (pAddr.sin_family != AF_INET) return 0;

    *ipOut = (uint32_t)ntohl(pAddr.sin_addr.s_addr);
    return 1;
    }

// Record a successful handshake for this client IP
static void markHs(int sock) {
    uint32_t ip = 0;
    if (!gtPeerIp(sock, &ip)) return;

    time_t now = time(NULL);
    int slot = -1;
    time_t oldest = now;

    // Find existing entry for this IP or an empty/old slot to use
    for (int i = 0; i < HS_CACHE_SIZE; i++) {
        if (hsTbl[i].valid && hsTbl[i].ip == ip) {
            slot = i;
            break;
            }
        if (!hsTbl[i].valid && slot < 0) slot = i;
        if (hsTbl[i].valid && hsTbl[i].ts <= oldest) {
            oldest = hsTbl[i].ts;
            if (slot < 0) slot = i;
            }
        }

    // if no slot found (shouldn't happen), just return without caching
    if (slot < 0) return;

    // Update cache entry
    hsTbl[slot].ip = ip;
    hsTbl[slot].ts = now;
    hsTbl[slot].valid = 1;
    }

// Require a recent handshake from the same client IP
static int hasRecentHs(int sock) {
    uint32_t ip = 0;
    if (!gtPeerIp(sock, &ip)) return 0;

    time_t now = time(NULL);

    for (int i = 0; i < HS_CACHE_SIZE; i++) {
        if (!hsTbl[i].valid) continue;
        if (hsTbl[i].ip != ip) continue;

        if ((now - hsTbl[i].ts) > HS_TTL_SEC) {
            hsTbl[i].valid = 0;
            return 0;
            }
        return 1;
        }

    return 0;
    }

// Match "elevateRequest" without embedding plaintext in the binary
static int isElevReq(const uint8_t* s, uint32_t sLen) {
    size_t reqLen = sizeof(ELEV_REQ_OBF);
    if (!s || sLen < (uint32_t)(reqLen + 1)) return 0;

    for (size_t i = 0; i < reqLen; i++) {
        if (s[i] != (uint8_t)(ELEV_REQ_OBF[i] ^ ELEV_REQ_XOR)) return 0;
        }
    return s[reqLen] == 0;
    }

// Arise handshake: parse client info and respond with server hash selection
static int handleAR(session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {
    (void)sess;

    ariseReq_t aReq;

    if (pAReq(payload, payloadLen, &aReq) < 0) return ErRes(sock, ERR_MALFORMED);
    if (!hasB3(aReq.supportedHashes)) return ErRes(sock, ERR_MALFORMED);

    markHs(sock);

    ariseResp_t aRes;
    aRes.magicPart = (uint16_t)MAGIC_B0 | ((uint16_t)MAGIC_B1 << 8);
    aRes.version = PROTOCOL_VERSION;
    strcpy(aRes.chosenHash, "Blake3, MD5");

    uint8_t rPld[256];
    int rLen = eARes(&aRes, rPld, sizeof(rPld));
    if (rLen < 0) return -1;

    uint8_t msg[512];
    int mLen = bldMes(PROTO_ARISE, MSG_ARISE_RESP, rPld, rLen, msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }

// SoulBind login: validate passphrase and issue unprivileged token
static int handleSBReq(uint8_t* payload, uint32_t payloadLen, int sock) {
    if (!hasRecentHs(sock)) return ErRes(sock, ERR_UNAUTHORIZED);

    soulbindReq_t sbReq;
    if (pSReq(payload, payloadLen, &sbReq) < 0) return ErRes(sock, ERR_MALFORMED);

    if (strcmp(sbReq.password, HARDCODED_PASSPHRASE) != 0) return ErRes(sock, ERR_UNAUTHORIZED);

    uint8_t tok[TOKEN_SIZE];
    gT(tok, TOKEN_SIZE);

    session_t* sNew = stCS(sbReq.username, tok, AUTH_UNPRIVILEGED);
    if (!sNew) return ErRes(sock, ERR_MALFORMED);

    soulbindResp_t sbRes;
    sbRes.accept = 0x01;
    memcpy(sbRes.token, tok, TOKEN_SIZE);
    sbRes.authLevel = AUTH_UNPRIVILEGED;

    uint8_t rPld[256];
    int rLen = eSBRes(&sbRes, rPld, sizeof(rPld));
    if (rLen < 0) return -1;

    uint8_t msg[512];
    int mLen = bldMes(PROTO_SOULBIND, MSG_SB_RESP, rPld, rLen, msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }

// SoulBind elevate: validate token + elevate request, then upgrade auth level
static int handleSBEle(uint8_t* payload, uint32_t payloadLen, int sock) {
    if (!payload || payloadLen < TOKEN_SIZE + 2) return ErRes(sock, ERR_MALFORMED);

    uint8_t tok[TOKEN_SIZE];
    memcpy(tok, payload, TOKEN_SIZE);

    session_t* s = stLT(tok);
    if (!s || !s->isActive) return ErRes(sock, ERR_UNAUTHORIZED);

    uint32_t rLen = (uint32_t)strnlen((char*)(payload + TOKEN_SIZE), payloadLen - TOKEN_SIZE);
    if (rLen == 0 || rLen >= (payloadLen - TOKEN_SIZE)) return ErRes(sock, ERR_MALFORMED);

    char eleEn[16];
    if (cfgG(cfgK(CFGK_ELE_ENABLED), eleEn, sizeof(eleEn)) < 0) return ErRes(sock, ERR_CONFIG_NOTFOUND);
    if (strcmp(eleEn, "True") != 0) return ErRes(sock, ERR_UNAUTHORIZED);

    if (!isElevReq(payload + TOKEN_SIZE, payloadLen - TOKEN_SIZE)) return ErRes(sock, ERR_UNAUTHORIZED);

    s->authLevel = AUTH_ADMIN;
    stUA(s);

    soulbindResp_t sbRes;
    sbRes.accept = 0x01;
    memcpy(sbRes.token, s->token, TOKEN_SIZE);
    sbRes.authLevel = AUTH_ADMIN;

    for (int i = 0; i < sizeof(ELE_FLAG_BYTES); i++) {
        sbRes.flag[i] = (ELE_FLAG_BYTES[i] ^ ELE_KEY[i % sizeof(ELE_KEY)]);
        }

    uint8_t rPld[256];
    int oLen = eSBRes(&sbRes, rPld, sizeof(rPld));
    if (oLen < 0) return -1;

    uint8_t msg[512];
    // put flag {unDEAD_THR0N3} in the response


    int mLen = bldMes(PROTO_SOULBIND, MSG_SB_RESP, rPld, oLen, msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }

// BoneCourier RTS: enforce configured max chunk and reply with CTS
static int handleBC(session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {
    boneCourierRts_t rts;
    if (pBCRts(payload, payloadLen, &rts) < 0) return ErRes(sock, ERR_MALFORMED);

    if (!stVT(sess, rts.token)) return ErRes(sock, ERR_UNAUTHORIZED);

    char maxChunkS[16];
    if (cfgG(cfgK(CFGK_MAX_CHUNK_SIZE), maxChunkS, sizeof(maxChunkS)) < 0) return ErRes(sock, ERR_CONFIG_NOTFOUND);

    int maxChunk = atoi(maxChunkS);
    if (maxChunk < 0 || rts.dataSize >(uint32_t)maxChunk) return ErRes(sock, ERR_TRANSFER_DENY);

    boneCourierCts_t cts;
    uint8_t ctsPld[8];
    int cLen = eBCCts(&cts, ctsPld, sizeof(ctsPld));
    if (cLen < 0) return -1;

    if (cts.accept == 0) return ErRes(sock, ERR_TRANSFER_DENY);

    // set transfer state to expect incoming 
    sess->inDataTransfer = 1;
    sess->expectedDataSize = rts.dataSize;

    uint8_t msg[512];
    int mLen = bldMes(PROTO_BONECOUR, MSG_BC_CTS, ctsPld, cLen, msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }

// BoneCourier Data: validate token, enforce remaining data size, verify chunk hash, and ack receipt
static int handleBCData(session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {
    boneCourierData_t data;

    if (pBCData(payload, payloadLen, &data) < 0) return ErRes(sock, ERR_MALFORMED);

    if (!stVT(sess, data.token)) return ErRes(sock, ERR_UNAUTHORIZED);

    if (data.dataLen > sess->expectedDataSize) {
        sess->inDataTransfer = 0;  // reset transfer state on protocol violation
        sess->expectedDataSize = 0;
        return ErRes(sock, ERR_TRANSFER_DENY);
        }

    // repurposing header hash validation to check chunk hash
    lichHeader_t tmp;
    tmp.protoId[0] = 'A';
    tmp.protoId[1] = 'R';
    memcpy(tmp.hash, data.chunkHash, 16);
    if (!vdH(&tmp, data.data, data.dataLen)) return ErRes(sock, ERR_CHUNK_HASH);

    uint8_t ack[512];
    int aLen = bldMes(PROTO_BONECOUR, MSG_BC_ACK, NULL, 0, ack, sizeof(ack));
    if (aLen < 0) return -1;
    sess->expectedDataSize -= data.dataLen;  // decrement remaining expected data size
    // if this was the last chunk, reset transfer state
    if (sess->expectedDataSize == 0) sess->inDataTransfer = 0;
    return nSA(sock, ack, aLen);            // just send acknowledgment, no actual processing of data in this challenge
    }

// NecroticWeave GetConfig: read key after token validation
static int handleNecroGet(session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {
    uint32_t kLen = (uint32_t)strnlen((char*)payload, payloadLen);
    if (kLen == 0 || kLen >= payloadLen) return ErRes(sock, ERR_MALFORMED);

    uint32_t pos = kLen + 1;
    if (pos + TOKEN_SIZE > payloadLen) return ErRes(sock, ERR_MALFORMED);
    if (!stVT(sess, payload + pos)) return ErRes(sock, ERR_UNAUTHORIZED);

    char key[MAX_CONFIG_LEN];
    memcpy(key, payload, kLen);
    key[kLen] = 0;

    char val[MAX_CONFIG_LEN];
    if (cfgG(key, val, sizeof(val)) < 0) return ErRes(sock, ERR_CONFIG_NOTFOUND);

    uint8_t msg[512];
    uint32_t oLen = (uint32_t)strnlen(val, MAX_CONFIG_LEN - 1) + 1;
    int mLen = bldMes(PROTO_NECRO, MSG_NW_GETCFG, (uint8_t*)val, oLen, msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }

// Build and send NW Approve/Deny payload: "key\0decision\0"
static int sendNWAp(int sock, const char* key, const char* decision) {
    uint8_t pld[MAX_CONFIG_LEN + 16];
    uint32_t kLen = (uint32_t)strnlen(key, MAX_CONFIG_LEN - 1);
    uint32_t dLen = (uint32_t)strnlen(decision, 15);
    uint32_t pos = 0;

    memcpy(pld + pos, key, kLen);
    pos += kLen;
    pld[pos++] = 0;
    memcpy(pld + pos, decision, dLen);
    pos += dLen;
    pld[pos++] = 0;

    uint8_t msg[512];
    int mLen = bldMes(PROTO_NECRO, MSG_NW_APPROVE, pld, pos, msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }

// NecroticWeave SetConfig: validate key/value/token and apply auth rules
static int handleNecroSet(session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {
    uint32_t kLen = (uint32_t)strnlen((char*)payload, payloadLen);
    if (kLen == 0 || kLen >= payloadLen) return ErRes(sock, ERR_MALFORMED);

    uint32_t pos = kLen + 1;
    uint32_t vLen = (uint32_t)strnlen((char*)(payload + pos), payloadLen - pos);
    if (vLen >= (payloadLen - pos)) return ErRes(sock, ERR_MALFORMED);

    uint32_t tPos = pos + vLen + 1;
    if (tPos + TOKEN_SIZE > payloadLen) return ErRes(sock, ERR_MALFORMED);
    if (!stVT(sess, payload + tPos)) return ErRes(sock, ERR_UNAUTHORIZED);

    char key[MAX_CONFIG_LEN];
    char val[MAX_CONFIG_LEN];
    memcpy(key, payload, kLen);
    key[kLen] = 0;
    memcpy(val, payload + pos, vLen);
    val[vLen] = 0;

    char valOld[MAX_CONFIG_LEN];
    if (cfgG(key, valOld, sizeof(valOld)) < 0) return ErRes(sock, ERR_CONFIG_NOTFOUND);

    if (!cfgCA(sess->authLevel, key)) return sendNWAp(sock, key, "deny");

    if (cfgS(key, val, sess->authLevel == AUTH_ADMIN) < 0) return ErRes(sock, ERR_CONFIG_NOTFOUND);

    return sendNWAp(sock, key, "approve");
    }


// UndeadWhisper exec path. The copy below is intentionally unsafe for challenge exploitability
// does not actually execute commands, just checks config gate and command length policy before responding with a stub result
static int handleUW(session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {

    if (payloadLen >= TOKEN_SIZE + 1) {
        if (!stVT(sess, payload + payloadLen - TOKEN_SIZE)) return ErRes(sock, ERR_UNAUTHORIZED);
        }
    else return ErRes(sock, ERR_MALFORMED);


    if (!payload || payloadLen == 0) return ErRes(sock, ERR_MALFORMED);

    if (sess->authLevel != AUTH_ADMIN) return ErRes(sock, ERR_CMD_DENIED);

    char cmdBuf[MAX_CMD_LEN];
    strcpy(cmdBuf, (const char*)payload);  // intended challenge vulnerability

    // Feature gate is checked after parsing/copy
    char enExecS[16];
    if (cfgG(cfgK(CFGK_EN_CMD_EXEC), enExecS, sizeof(enExecS)) < 0) return ErRes(sock, ERR_CONFIG_NOTFOUND);
    if (strcmp(enExecS, "True") != 0) return ErRes(sock, ERR_CMD_DENIED);

    // Command size policy is configurable
    char cmdSizeS[16];
    int cmdMax = MAX_CMD_LEN;
    if (cfgG(cfgK(CFGK_CMD_SIZE), cmdSizeS, sizeof(cmdSizeS)) == 0) {
        int p = atoi(cmdSizeS);
        if (p > 0) cmdMax = p;
        }
    if (cmdMax < 1) cmdMax = 1;

    size_t cmdLen = strnlen((char*)payload, payloadLen);
    if (cmdLen > (size_t)cmdMax) return ErRes(sock, ERR_CMD_DENIED);

    uint8_t rPld[1] = { 0x00 };
    uint8_t msg[512];
    int mLen = bldMes(PROTO_UNDEAD, MSG_UW_RESULT, rPld, sizeof(rPld), msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }


// EternalRest: invalidate session and send goodbye
static int handleER(session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {
    (void)payload;
    (void)payloadLen;

    if (!sess || !sess->isActive) return ErRes(sock, ERR_UNAUTHORIZED);

    stIS(sess);

    uint8_t rPld[] = { 0x00 };
    uint8_t msg[512];
    int mLen = bldMes(PROTO_ETERNAL, MSG_ER_RESP, rPld, 1, msg, sizeof(msg));
    if (mLen < 0) return -1;
    return nSA(sock, msg, mLen);
    }

// Central protocol dispatcher by protocol ID and message type
int disMes(uint16_t protoId, uint8_t msgType, session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock) {

    switch (protoId) {
        case PROTO_ARISE:
            return handleAR(sess, payload, payloadLen, sock);

        case PROTO_SOULBIND:
            if (msgType == MSG_SB_REQ) return handleSBReq(payload, payloadLen, sock);
            if (msgType == MSG_SB_ELEVATE) return handleSBEle(payload, payloadLen, sock);
            return ErRes(sock, ERR_MALFORMED);

        case PROTO_BONECOUR:
            if (msgType == MSG_BC_RTS) return handleBC(sess, payload, payloadLen, sock);
            if (msgType == MSG_BC_DATA && sess->inDataTransfer == 1) return handleBCData(sess, payload, payloadLen, sock);
            return ErRes(sock, ERR_MALFORMED);

        case PROTO_NECRO:
            if (msgType == MSG_NW_GETCFG) return handleNecroGet(sess, payload, payloadLen, sock);
            if (msgType == MSG_NW_SETCFG) return handleNecroSet(sess, payload, payloadLen, sock);
            return ErRes(sock, ERR_MALFORMED);

        case PROTO_UNDEAD:
            if (msgType != MSG_UW_EXEC) return ErRes(sock, ERR_MALFORMED);
            return handleUW(sess, payload, payloadLen, sock);

        case PROTO_ETERNAL:
            if (msgType != MSG_ER_REQ) return ErRes(sock, ERR_MALFORMED);
            return handleER(sess, payload, payloadLen, sock);

        default:
            return ErRes(sock, ERR_MALFORMED);
        }
    }

// Encode and send protocol-level error payload
int ErRes(int sock, errorCode_t code) {
    uint8_t pld[256];
    int pLen = bldErRes(code, pld, sizeof(pld));
    if (pLen < 0) return -1;

    uint8_t mType = gtErRs(code);

    uint8_t msg[512];
    int mLen = bldMes(PROTO_ERROR, mType, pld, pLen, msg, sizeof(msg));
    if (mLen < 0) return -1;

    return nSA(sock, msg, mLen);
    }
