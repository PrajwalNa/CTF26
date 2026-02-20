#include "net.h"
#include "proto.h"
#include "state.h"
#include "handlers.h"
#include "config.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <time.h>

#define DEFAULT_PORT 9001

static int srvRun = 1;
static const uint8_t srvMagic[MAGIC_SIZE] = { MAGIC_B0, MAGIC_B1, MAGIC_B2, MAGIC_B3, MAGIC_B4, MAGIC_B5 };

// Stop the server loop on termination signals.
static void handleSignal(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        srvRun = 0;
        }
    }

// Read maxPayload from config and clamp it to compile-time hard max.
static int gtMaxPayload(void) {
    char maxPldS[16];
    int limit = 256;

    if (cfgG(cfgK(CFGK_MAX_PAYLOAD), maxPldS, sizeof(maxPldS)) == 0) {
        int parsed = atoi(maxPldS);
        if (parsed > 0) {
            limit = parsed;
            }
        }

    // Keep protocol usable: login payloads are >13 bytes with normal creds.
    if (limit < 16) limit = 16;
    if (limit > MAX_PAYLOAD_LEN) limit = MAX_PAYLOAD_LEN;
    return limit;
    }

// Read timeout from config and keep it in a sane runtime range.
static int gtTimeout(void) {
    char tmoS[16];
    int tmo = TIMEOUT_SEC;

    if (cfgG(cfgK(CFGK_TIMEOUT), tmoS, sizeof(tmoS)) == 0) {
        int p = atoi(tmoS);
        if (p > 0) tmo = p;
        }

    if (tmo < 1) tmo = 1;
    if (tmo > 120) tmo = 120;
    return tmo;
    }

// Extract the token field from protocol-specific payload layouts.
static int exTok(uint16_t protoId, uint8_t msgType, uint8_t* payload, uint32_t payloadLen, uint8_t* outTok) {
    if (!payload || !outTok) return 0;

    switch (protoId) {
        case PROTO_BONECOUR:
            if (msgType == MSG_BC_RTS) {
                if (payloadLen < 4 + TOKEN_SIZE) return 0;
                memcpy(outTok, payload + 4, TOKEN_SIZE);
                return 1;
                }
            if (msgType == MSG_BC_DATA) {
                if (payloadLen < payloadLen + 16 + TOKEN_SIZE) return 0;
                memcpy(outTok, payload + payloadLen - TOKEN_SIZE, TOKEN_SIZE);
                return 1;
                }
            return 0;

        case PROTO_NECRO: {
        uint32_t kLen = strnlen((char*)payload, payloadLen);
        if (kLen >= payloadLen) return 0;
        uint32_t pos = kLen + 1;

        if (msgType == MSG_NW_GETCFG) {
            if (pos + TOKEN_SIZE > payloadLen) return 0;
            memcpy(outTok, payload + pos, TOKEN_SIZE);
            return 1;
            }
        if (msgType == MSG_NW_SETCFG || msgType == MSG_NW_APPROVE) {
            uint32_t vLen = strnlen((char*)(payload + pos), payloadLen - pos);
            if (pos + vLen >= payloadLen) return 0;
            pos += vLen + 1;
            if (pos + TOKEN_SIZE > payloadLen) return 0;
            memcpy(outTok, payload + pos, TOKEN_SIZE);
            return 1;
            }
        return 0;
        }

        case PROTO_UNDEAD: {
        uint32_t cmdLen = strnlen((char*)payload, payloadLen);
        if (cmdLen >= payloadLen) return 0;
        if (cmdLen + 1 + TOKEN_SIZE > payloadLen) return 0;
        memcpy(outTok, payload + cmdLen + 1, TOKEN_SIZE);
        return 1;
        }

        case PROTO_ETERNAL:
            if (payloadLen < TOKEN_SIZE) return 0;
            memcpy(outTok, payload, TOKEN_SIZE);
            return 1;

        default:
            return 0;
        }
    }

    // Main loop: parse frame, validate header/hash, resolve session, dispatch.
int main(int argc, char* argv[]) {
    int port = DEFAULT_PORT;
    uint64_t connCnt = 0;

    if (argc > 1) {
        port = atoi(argv[1]);
        }

    printf("[*] Lich server starting\n");

    srand(time(NULL));
    stInit();
    cfgInit();

    signal(SIGINT, handleSignal);
    signal(SIGTERM, handleSignal);

    int sSock = nInt(port);
    if (sSock < 0) {
        printf("[!] Listener init failed on port %d\n", port);
        return 1;
        }
    printf("[*] Listening on port %d\n", port);

    while (srvRun) {
        // One request per connection.
        int cSock = nAcc(sSock);
        if (cSock < 0) continue;
        connCnt++;
        printf("[*] Connection #%llu\n", (unsigned long long)connCnt);

        uint8_t hdrBuf[HEADER_SIZE];
        uint8_t pldBuf[MAX_PAYLOAD_LEN];
        int tmo = gtTimeout();

        if (nRec(cSock, hdrBuf, HEADER_SIZE, tmo) < 0) {
            nC(cSock);
            continue;
            }

        lichHeader_t hdr;
        if (dseH(hdrBuf, HEADER_SIZE, &hdr) < 0) {
            ErRes(cSock, ERR_MAGIC_VER);
            nC(cSock);
            continue;
            }

        uint16_t pId = (uint16_t)((hdr.protoId[0] << 8) | hdr.protoId[1]);
        int maxPld = gtMaxPayload();

        if (hdr.payloadLen > MAX_PAYLOAD_LEN || (int)hdr.payloadLen > maxPld) {
            ErRes(cSock, ERR_MALFORMED);
            nC(cSock);
            continue;
            }

        if (hdr.payloadLen > 0) {
            if (nRec(cSock, pldBuf, hdr.payloadLen, tmo) < 0) {
                ErRes(cSock, ERR_MALFORMED);
                nC(cSock);
                continue;
                }
            }

        // Arise is the only protocol without magic validation.
        if (pId != PROTO_ARISE) {
            if (memcmp(hdr.magic, srvMagic, MAGIC_SIZE) != 0 || hdr.version != PROTOCOL_VERSION) {
                ErRes(cSock, ERR_MAGIC_VER);
                nC(cSock);
                continue;
                }
            }

        if (!vdH(&hdr, pldBuf, hdr.payloadLen)) {
            ErRes(cSock, ERR_HASH_FAIL);
            nC(cSock);
            continue;
            }

        // Resolve active session for token-protected protocols.
        session_t* sess = NULL;
        if (pId != PROTO_ARISE && pId != PROTO_SOULBIND) {
            uint8_t tok[TOKEN_SIZE];
            if (!exTok(pId, hdr.msgType, pldBuf, hdr.payloadLen, tok)) {
                ErRes(cSock, ERR_MALFORMED);
                nC(cSock);
                continue;
                }
            sess = stLT(tok);
            if (!sess || !sess->isActive) {
                ErRes(cSock, ERR_UNAUTHORIZED);
                nC(cSock);
                continue;
                }
            stUA(sess);
            }

        disMes(pId, hdr.msgType, sess, pldBuf, hdr.payloadLen, cSock);

        nC(cSock);
        }

    printf("[*] Server stopped\n");
    stCA();
    return 0;
    }
