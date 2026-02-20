#pragma once

#include "types.h"

// Dispatcher
int disMes(uint16_t protoId, uint8_t msgType, session_t* sess, uint8_t* payload, uint32_t payloadLen, int sock);

// Send error response
int ErRes(int sock, errorCode_t code);
