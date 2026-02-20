#pragma once

#include <stdint.h>
#include <time.h>

// Protocol IDs (as hex values to minimize strings) 
#define PROTO_ARISE     0x4152    // "AR" 
#define PROTO_SOULBIND  0x5342    // "SB" 
#define PROTO_BONECOUR  0x4243    // "BC" 
#define PROTO_NECRO     0x4E57    // "NW" 
#define PROTO_UNDEAD    0x5557    // "UW" 
#define PROTO_ETERNAL   0x4552    // "ER" 
#define PROTO_ERROR     0x4552    // "ER" - same as ETERNAL for error responses 

// Message types 
#define MSG_ARISE_REQ       0x01
#define MSG_ARISE_RESP      0x02
#define MSG_SB_REQ          0x10
#define MSG_SB_RESP         0x11
#define MSG_SB_ELEVATE      0x12
#define MSG_BC_RTS          0x20
#define MSG_BC_CTS          0x21
#define MSG_BC_DATA         0x22
#define MSG_BC_ACK          0x23
#define MSG_NW_SETCFG       0x30
#define MSG_NW_GETCFG       0x31
#define MSG_NW_APPROVE      0x34
#define MSG_UW_EXEC         0x40
#define MSG_UW_RESULT       0x41
#define MSG_UW_INVALID      0x42
#define MSG_ER_REQ          0x50
#define MSG_ER_RESP         0x51
#define MSG_ER_IDK          0x52

// Constants 
#define HEADER_SIZE         46
#define MAX_CHUNK_SIZE      256
#define MAX_CONFIG_LEN      256
#define MAX_CMD_LEN         256
#define MAX_OUTPUT_LEN      128
#define TOKEN_SIZE          16
#define HASH_SIZE           32
#define TIMEOUT_SEC         10
#define TOKEN_EXPIRE_SEC    60
// 8-byte credential fields + 1 byte for null terminator in C storage.
#define MAX_USERNAME_LEN    9
#define MAX_PASSWORD_LEN    9
#define MAX_PAYLOAD_LEN     256

// Magic bytes for non-Arise traffic: L,0x1C,H,0x84,0x92 plus one pad byte
#define MAGIC_SIZE          6
#define MAGIC_B0            0x4C
#define MAGIC_B1            0x1C
#define MAGIC_B2            0x48
#define MAGIC_B3            0x84
#define MAGIC_B4            0x92
#define MAGIC_B5            0x00

// Version 
#define PROTOCOL_VERSION    0x06

// Authorization levels 
typedef enum {
    AUTH_NONE = -1,
    AUTH_UNPRIVILEGED = 0,
    AUTH_ADMIN = 1
    } authLevel_t;


// Error codes 
typedef enum {
    ERR_OK = 0x0000,
    ERR_MAGIC_VER = 0x0001,
    ERR_HASH_FAIL = 0x0002,
    ERR_UNAUTHORIZED = 0x0003,
    ERR_CMD_DENIED = 0x0004,
    ERR_TOKEN_EXP = 0x0005,
    ERR_MALFORMED = 0x0006,
    ERR_CONFIG_NOTFOUND = 0x0007,
    ERR_CHUNK_HASH = 0x0008,
    ERR_TRANSFER_DENY = 0x0009
    } errorCode_t;

// Protocol header (46 bytes, packed) 
typedef struct {
    char protoId[2];
    uint8_t msgType;
    uint32_t payloadLen;
    uint8_t magic[MAGIC_SIZE];
    uint8_t version;
    uint8_t hash[32];
    } __attribute__((packed)) lichHeader_t;

// Session structure 
typedef struct {
    char username[MAX_USERNAME_LEN];
    uint8_t token[TOKEN_SIZE];
    time_t lastActivity;
    authLevel_t authLevel;
    int isActive;
    int inDataTransfer;
    uint32_t expectedDataSize;
    void* stagedConfig;
    } session_t;

// Payload structures

typedef struct {
    uint16_t magicPart;
    uint8_t version;
    char supportedHashes[256];
    } ariseReq_t;

typedef struct {
    uint16_t magicPart;
    uint8_t version;
    char chosenHash[32];
    } ariseResp_t;

typedef struct {
    char username[MAX_USERNAME_LEN];
    char password[MAX_PASSWORD_LEN];
    } soulbindReq_t;

typedef struct {
    uint8_t accept;  // 0x00 = deny, 0x01 = accept 
    uint8_t token[TOKEN_SIZE];
    uint8_t authLevel;
    uint8_t flag[15];
    } soulbindResp_t;

typedef struct {
    uint32_t dataSize;
    uint8_t token[TOKEN_SIZE];
    } boneCourierRts_t;

typedef struct {
    uint8_t accept;  // 0x00 = deny, 0x01 = accept
    } boneCourierCts_t;

typedef struct {
    uint8_t data[MAX_CHUNK_SIZE];
    uint32_t dataLen;
    char chunkHash[16];  // Raw MD5 
    uint8_t token[TOKEN_SIZE];
    } boneCourierData_t;

typedef struct {
    char chunkHash[16];  // Raw MD5 
    uint8_t token[TOKEN_SIZE];
    } boneCourierAck_t;

typedef struct {
    char configKey[MAX_CONFIG_LEN];
    char configValue[MAX_CONFIG_LEN];
    uint8_t token[TOKEN_SIZE];
    } necroticSetCfg_t;

typedef struct {
    char configKey[MAX_CONFIG_LEN];
    uint8_t token[TOKEN_SIZE];
    } necroticGetCfg_t;

typedef struct {
    char command[MAX_CMD_LEN];
    uint8_t token[TOKEN_SIZE];
    } undeadExec_t;

typedef struct {
    char output[MAX_OUTPUT_LEN];
    uint32_t outputLen;
    } undeadResult_t;
