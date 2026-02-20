#pragma once
#include <stdint.h>

// Initialize server socket on port
int nInt(int port);

// Accept incoming connection
int nAcc(int serverSock);

// Receive exact N bytes with timeout
int nRec(int sock, uint8_t* buf, int len, int timeoutSec);

// Send all bytes, return bytes sent or -1 on error
int nSA(int sock, uint8_t* buf, int len);

// Close socket
void nC(int sock);
