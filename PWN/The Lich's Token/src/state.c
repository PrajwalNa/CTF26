#include "state.h"
#include "config.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_SESSIONS 100

static session_t stTbl[MAX_SESSIONS];  // stTbl = session table
static int stCnt = 0;  // stCnt = session count

static int gtMaxSess(void) {
    char maxSessS[16];
    int maxS = MAX_SESSIONS;

    if (cfgG(cfgK(CFGK_MAX_SESS), maxSessS, sizeof(maxSessS)) == 0) {
        int p = atoi(maxSessS);
        if (p > 0) maxS = p;
        }

    if (maxS < 1) maxS = 1;
    if (maxS > MAX_SESSIONS) maxS = MAX_SESSIONS;
    return maxS;
    }

static int gtTknExp(void) {
    char expS[16];
    int exp = TOKEN_EXPIRE_SEC;

    if (cfgG(cfgK(CFGK_TKN_EXPIRE), expS, sizeof(expS)) == 0) {
        int p = atoi(expS);
        if (p > 0) exp = p;
        }

    if (exp < 1) exp = 1;
    if (exp > 86400) exp = 86400;
    return exp;
    }

// stInit: State Initialize - Initialize session management
int stInit(void) {
    memset(stTbl, 0, sizeof(stTbl));
    stCnt = 0;
    return 0;
    }

// stCS: State Create Session - Create new session
session_t* stCS(const char* username, uint8_t* token, authLevel_t level) {
    if (!username || !token) return NULL;

    // Reap expired sessions so maxSess is enforced on live sessions only.
    for (int i = 0; i < stCnt; i++) {
        if (stTbl[i].isActive) {
            stTE(&stTbl[i]);
            }
        }

    // Invalidate any existing session for this user
    for (int i = 0; i < stCnt; i++) {
        if (strcmp(stTbl[i].username, username) == 0 && stTbl[i].isActive) {
            stTbl[i].isActive = 0;
            }
        }

    int maxS = gtMaxSess();
    int actS = 0;
    for (int i = 0; i < stCnt; i++) {
        if (stTbl[i].isActive) actS++;
        }
    if (actS >= maxS) return NULL;

    session_t* s = NULL;
    for (int i = 0; i < stCnt; i++) {
        if (!stTbl[i].isActive) {
            s = &stTbl[i];
            break;
            }
        }
    if (!s) {
        if (stCnt >= MAX_SESSIONS) return NULL;
        s = &stTbl[stCnt++];
        }

    strncpy(s->username, username, MAX_USERNAME_LEN - 1);
    s->username[MAX_USERNAME_LEN - 1] = 0;

    memcpy(s->token, token, TOKEN_SIZE);
    s->lastActivity = time(NULL);
    s->authLevel = level;
    s->isActive = 1;
    s->inDataTransfer = 0;
    s->expectedDataSize = 0;
    s->stagedConfig = NULL;

    return s;
    }

// stVT: State Validate Token - Verify token matches session
int stVT(session_t* sess, uint8_t* token) {
    if (!sess || !sess->isActive) return 0;
    return memcmp(sess->token, token, TOKEN_SIZE) == 0;
    }

// stTE: State Token Expired - Check if token expired
int stTE(session_t* sess) {
    if (!sess) return 1;

    time_t now = time(NULL);
    if ((now - sess->lastActivity) > gtTknExp()) {
        sess->isActive = 0;  // Auto-invalidate expired session
        return 1;
        }
    return 0;
    }

// stLT: State Lookup by Token - Find session by token and validate expiry
session_t* stLT(uint8_t* token) {
    if (!token) return NULL;

    for (int i = 0; i < stCnt; i++) {
        if (stTbl[i].isActive && memcmp(stTbl[i].token, token, TOKEN_SIZE) == 0) {
            // Check if expired
            if (stTE(&stTbl[i])) {
                return NULL;  // Expired
                }
            return &stTbl[i];
            }
        }
    return NULL;
    }

// stIS: State Invalidate Session - Mark session inactive
void stIS(session_t* sess) {
    if (sess) {
        sess->isActive = 0;
        }
    }

// stUA: State Update Activity - Refresh last activity timestamp
void stUA(session_t* sess) {
    if (sess) {
        sess->lastActivity = time(NULL);
        }
    }

// stCA: State Cleanup All - Clean up all sessions
void stCA(void) {
    // stCnt = session count to iterate
    for (int i = 0; i < stCnt; i++) {
        if (stTbl[i].stagedConfig) {
            free(stTbl[i].stagedConfig);
            stTbl[i].stagedConfig = NULL;
            }
        }
    stCnt = 0;
    }
