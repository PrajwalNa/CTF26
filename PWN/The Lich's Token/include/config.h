#pragma once

#include "types.h"

typedef enum {
    CFGK_TIMEOUT = 0,
    CFGK_MAX_CHUNK_SIZE,
    CFGK_ELE_ENABLED,
    CFGK_SERVER_PORT,
    CFGK_TKN_EXPIRE,
    CFGK_MAX_SESS,
    CFGK_MAX_PAYLOAD,
    CFGK_EN_CMD_EXEC,
    CFGK_CMD_SIZE,
    CFGK_COUNT
    } cfgKeyId_t;

typedef struct {
    char key[MAX_CONFIG_LEN];
    char value[MAX_CONFIG_LEN];
    int requiresAdmin;
    } configEntry_t;

// Initialize config subsystem
int cfgInit(void);

// Get config value
int cfgG(const char* key, char* out, uint32_t outLen);

// Set config value
int cfgS(const char* key, const char* value, int requiresAdmin);

// Check if user can modify key
int cfgCA(authLevel_t level, const char* key);

// Resolve a config key string from its obfuscated static table.
const char* cfgK(cfgKeyId_t keyId);
