#include "error.h"

// bldErRes: Build Error Response - Encode error code to payload
int bldErRes(errorCode_t code, uint8_t* out, uint32_t outLen) {
    if (outLen < 2) return -1;

    // Error code as 2 bytes, little-endian
    out[0] = code & 0xFF;
    out[1] = (code >> 8) & 0xFF;

    return 2;
    }

// gtErRs: Get Error Response Type - Return msg type for error
uint8_t gtErRs(errorCode_t code) {
    switch (code) {
        case ERR_MAGIC_VER:

        case ERR_HASH_FAIL:
        case ERR_TOKEN_EXP:
        case ERR_MALFORMED:
        case ERR_CONFIG_NOTFOUND:
            return MSG_ER_IDK;      // 0x52 - "IDK you"

        case ERR_UNAUTHORIZED:
        case ERR_CMD_DENIED:
            return MSG_UW_INVALID;  // 0x42 - "InvalidToken"

        case ERR_CHUNK_HASH:
            return MSG_BC_ACK;      // 0x23 - "DataAck with error"

        case ERR_TRANSFER_DENY:
            return MSG_BC_CTS;      // 0x21 - "ClearToSend deny"

        default:
            return MSG_ER_IDK;      // Default to "IDK you" for unknown errors
        }
    }
