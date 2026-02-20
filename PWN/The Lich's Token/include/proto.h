#pragma once

#include "types.h"

// Serialize header to buffer (returns bytes written) 
int seH(lichHeader_t* hdr, uint8_t* buf, uint32_t bufLen);

// Deserialize header from buffer (returns bytes read or -1 on error) 
int dseH(uint8_t* buf, uint32_t bufLen, lichHeader_t* hdr);

// Validate header (magic, version, hash) 
int vdH(lichHeader_t* hdr, uint8_t* payload, uint32_t payloadLen);

// Parse payload structures 
int pAReq(uint8_t* payload, uint32_t len, ariseReq_t* out);             // Arise request
int pSReq(uint8_t* payload, uint32_t len, soulbindReq_t* out);          // SoulBind request
int pBCRts(uint8_t* payload, uint32_t len, boneCourierRts_t* out);      // BoneCourier RTS
// Encode responses 
int eARes(ariseResp_t* resp, uint8_t* buf, uint32_t bufLen);            // Arise response
int eSBRes(soulbindResp_t* resp, uint8_t* buf, uint32_t bufLen);        // SoulBind response
int eBCCts(boneCourierCts_t* cts, uint8_t* buf, uint32_t bufLen);       // BoneCourier CTS
int pBCData(uint8_t* payload, uint32_t len, boneCourierData_t* out);    // BoneCourier Data packet

// Build complete message (header + payload) 
int bldMes(uint16_t protoId, uint8_t msgType, uint8_t* payload, uint32_t payloadLen, uint8_t* out, uint32_t outLen);
