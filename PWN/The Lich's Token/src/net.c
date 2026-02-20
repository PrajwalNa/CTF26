#include "net.h"
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#ifdef _MSC_VER
#pragma comment(lib, "ws2_32.lib")
#endif

static int wsaInit = 0;  // wsaInit = WSA initialized flag

// Initialize Windows Sockets API
static void _initWSA(void) {
    if (!wsaInit) {
        // wsd = Windows Sockets Data
        WSADATA wsd;
        WSAStartup(MAKEWORD(2, 2), &wsd);
        wsaInit = 1;
        }
    }

// nInt: Network Initialize - Create and bind server socket
int nInt(int port) {
    _initWSA();

    // s = socket handle
    SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
    if (s == INVALID_SOCKET) return -1;

    // opt = socket option for reuse address
    int opt = 1;
    if (setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt)) < 0) {
        closesocket(s);
        return -1;
        }

    // addr = socket address structure
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(s, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        closesocket(s);
        return -1;
        }

    if (listen(s, 5) < 0) {
        closesocket(s);
        return -1;
        }

    return (int)s;
    }

// nAcc: Network Accept - Accept client connection
int nAcc(int serverSock) {
    // caddr = client address
    struct sockaddr_in caddr;
    int caddr_len = sizeof(caddr);

    // cs = client socket accepted
    SOCKET cs = accept((SOCKET)serverSock, (struct sockaddr*)&caddr, &caddr_len);
    return (cs == INVALID_SOCKET) ? -1 : (int)cs;
    }

// nRec: Network Receive - Read exact N bytes with timeout
int nRec(int sock, uint8_t* buf, int len, int timeoutSec) {
    int tot = 0;  // tot = total bytes received

    while (tot < len) {
        // rset = read set for select
        fd_set rset;
        FD_ZERO(&rset);
        FD_SET((SOCKET)sock, &rset);

        // tv = timeout value
        struct timeval tv;
        tv.tv_sec = timeoutSec;
        tv.tv_usec = 0;

        int ret = select(0, &rset, NULL, NULL, &tv);
        if (ret <= 0) {
            return -1;  // Timeout or error
            }

        // br = bytes received
        int br = recv((SOCKET)sock, (char*)&buf[tot], len - tot, 0);
        if (br <= 0) {
            return -1;
            }

        tot += br;
        }

    return tot;
    }

// nSA: Network Send All - Send all bytes
int nSA(int sock, uint8_t* buf, int len) {
    int tot = 0;  // tot = total bytes sent

    while (tot < len) {
        // bs = bytes sent
        int bs = send((SOCKET)sock, (const char*)&buf[tot], len - tot, 0);
        if (bs <= 0) {
            return -1;
            }

        tot += bs;
        }

    return tot;
    }

// nC: Network Close - Close socket  
void nC(int sock) {
    if (sock >= 0) {
        closesocket((SOCKET)sock);
        }
    }

