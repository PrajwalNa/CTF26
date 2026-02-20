#pragma once

#include "types.h"

// Create new session
session_t* stCS(const char* username, uint8_t* token, authLevel_t level);

// Lookup session by token (with expiry validation)
session_t* stLT(uint8_t* token);

// Validate token for session
int stVT(session_t* sess, uint8_t* token);

// Check if token expired
int stTE(session_t* sess);

// Mark session as inactive
void stIS(session_t* sess);

// Update last activity timestamp
void stUA(session_t* sess);

// Cleanup all sessions
void stCA(void);

// Initialize session manager
int stInit(void);
