#include "config.h"
#include <stdlib.h>
#include <string.h>

#define MAX_CONFIG_ENTRIES 50
#define CFG_OBF_XOR 0x5A
#define CFG_KEY_MAX 16

// Configuration management with obfuscated keys to reduce string leakage in binaries
typedef struct {
    const uint8_t* data;
    uint8_t len;
    } cfgKeyBlob_t;

// XOR-obfuscated config keys for sending in the NecroticWeave protocol
static const uint8_t k0[] = { 0x2E, 0x33, 0x37, 0x3F, 0x35, 0x2F, 0x2E };                               // timeout
static const uint8_t k1[] = { 0x37, 0x3B, 0x22, 0x19, 0x32, 0x2F, 0x34, 0x31, 0x09, 0x33, 0x20, 0x3F }; // maxChunkSize
static const uint8_t k2[] = { 0x1F, 0x36, 0x3F, 0x1F, 0x34, 0x3B, 0x38, 0x36, 0x3F, 0x3E };             // EleEnabled
static const uint8_t k3[] = { 0x29, 0x3F, 0x28, 0x2C, 0x3F, 0x28, 0x0A, 0x35, 0x28, 0x2E };             // serverPort
static const uint8_t k4[] = { 0x2E, 0x31, 0x34, 0x1F, 0x22, 0x2A, 0x33, 0x28, 0x3F };                   // tknExpire
static const uint8_t k5[] = { 0x37, 0x3B, 0x22, 0x09, 0x3F, 0x29, 0x29 };                               // maxSess
static const uint8_t k6[] = { 0x37, 0x3B, 0x22, 0x0A, 0x3B, 0x23, 0x36, 0x35, 0x3B, 0x3E };             // maxPayload
static const uint8_t k7[] = { 0x1F, 0x34, 0x19, 0x37, 0x3E, 0x1F, 0x22, 0x3F, 0x39 };                   // EnCmdExec
static const uint8_t k8[] = { 0x19, 0x37, 0x3E, 0x09, 0x33, 0x20, 0x3F };                               // CmdSize

static const cfgKeyBlob_t kTbl[CFGK_COUNT] = {
    { k0, sizeof(k0) },
    { k1, sizeof(k1) },
    { k2, sizeof(k2) },
    { k3, sizeof(k3) },
    { k4, sizeof(k4) },
    { k5, sizeof(k5) },
    { k6, sizeof(k6) },
    { k7, sizeof(k7) },
    { k8, sizeof(k8) },
    };

static char kDec[CFGK_COUNT][CFG_KEY_MAX];
static int kReady = 0;

// cfgTbl = configuration table
static configEntry_t cfgTbl[MAX_CONFIG_ENTRIES];
// cfgCnt = configuration entry count
static int cfgCnt = 0;

// Decode Function
static void decKeys(void) {
    if (kReady) return;

    for (int i = 0; i < CFGK_COUNT; i++) {
        uint8_t len = kTbl[i].len;
        if (len >= CFG_KEY_MAX) len = CFG_KEY_MAX - 1;

        for (uint8_t j = 0; j < len; j++) {
            kDec[i][j] = (char)(kTbl[i].data[j] ^ CFG_OBF_XOR);
            }
        kDec[i][len] = 0;
        }

    kReady = 1;
    }

// cfgK: Config Key - Resolve obfuscated key from static table
const char* cfgK(cfgKeyId_t keyId) {
    decKeys();
    if (keyId < 0 || keyId >= CFGK_COUNT) return "";
    return kDec[keyId];
    }

// addCfg: Helper to add config entry to table
static void addCfg(cfgKeyId_t keyId, const char* value, int requiresAdmin) {
    if (cfgCnt >= MAX_CONFIG_ENTRIES) return;   // Should never happen with defined keys

    // Resolve key string and add to config table
    strncpy(cfgTbl[cfgCnt].key, cfgK(keyId), MAX_CONFIG_LEN - 1);
    cfgTbl[cfgCnt].key[MAX_CONFIG_LEN - 1] = 0;
    strncpy(cfgTbl[cfgCnt].value, value, MAX_CONFIG_LEN - 1);
    cfgTbl[cfgCnt].value[MAX_CONFIG_LEN - 1] = 0;
    cfgTbl[cfgCnt].requiresAdmin = requiresAdmin;
    cfgCnt++;
    }

// cfgInit: Config Initialize - Set up default config
int cfgInit(void) {
    memset(cfgTbl, 0, sizeof(cfgTbl));
    cfgCnt = 0;

    // Initialize default configs
    // Only EleEnabled can be modified by unprivileged users, all others require admin token
    addCfg(CFGK_TIMEOUT, "10", 1);
    addCfg(CFGK_MAX_CHUNK_SIZE, "256", 1);
    addCfg(CFGK_ELE_ENABLED, "False", 0);
    addCfg(CFGK_SERVER_PORT, "9001", 1);
    addCfg(CFGK_TKN_EXPIRE, "60", 1);
    addCfg(CFGK_MAX_SESS, "5", 1);
    addCfg(CFGK_MAX_PAYLOAD, "256", 1);
    addCfg(CFGK_EN_CMD_EXEC, "False", 1);
    addCfg(CFGK_CMD_SIZE, "256", 1);

    return 0;
    }

// cfgG: Config Get - Retrieve configuration value
int cfgG(const char* key, char* out, uint32_t outLen) {
    if (!key || !out || outLen == 0) return -1;

    for (int i = 0; i < cfgCnt; i++) {
        if (strcmp(cfgTbl[i].key, key) == 0) {
            strncpy(out, cfgTbl[i].value, outLen - 1);
            out[outLen - 1] = 0;
            return 0;  // Success
            }
        }

    return -1;  // Not found
    }

// cfgS: Config Set - Update configuration value
int cfgS(const char* key, const char* value, int requiresAdmin) {
    if (!key || !value) return -1;

    int keyIndex = -1;
    for (int i = 0; i < cfgCnt; i++) {
        if (strcmp(cfgTbl[i].key, key) == 0) {
            keyIndex = i;
            break;
            }
        }

    if (keyIndex == -1) {
        return -1;  // Key not found
        }

    if (cfgTbl[keyIndex].requiresAdmin && !requiresAdmin) {
        return -1;  // Unauthorized
        }

    strncpy(cfgTbl[keyIndex].value, value, MAX_CONFIG_LEN - 1);
    cfgTbl[keyIndex].value[MAX_CONFIG_LEN - 1] = 0;
    return 0;  // Success
    }


// cfgCA: Config Check Auth - Verify user permission
int cfgCA(authLevel_t level, const char* key) {
    // Admin can modify anything
    if (level == AUTH_ADMIN) return 1;

    for (int i = 0; i < cfgCnt; i++) {
        if (strcmp(key, cfgTbl[i].key) == 0 && !cfgTbl[i].requiresAdmin) {
            return 1;
            }
        }

    return 0;
    }
