#pragma once

#include "types.h"

// Build error response (returns payload length)
int bldErRes(errorCode_t code, uint8_t* out, uint32_t outLen);

// Get response message type for error code
uint8_t gtErRs(errorCode_t code);
