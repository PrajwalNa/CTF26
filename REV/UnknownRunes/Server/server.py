from customISA import UnknownRunesVM
import socket
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HOST = "0.0.0.0"
PORT = 666
PROGRAM = "journey.rune"
MAX_CONNECTIONS = 20


def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")
    try:
        r = conn.makefile("r", buffering=1, encoding="utf-8", errors="replace")
        w = conn.makefile("w", buffering=1, encoding="utf-8", errors="replace")

        vm = UnknownRunesVM(inStream=r, outStream=w)
        vm.loadProgFile(PROGRAM)
        vm.run()

        w.flush()
    except (ConnectionResetError, BrokenPipeError):
        print(f"[-] {addr} disconnected")
    except SystemExit:
        pass  # VM called EXIT syscall
    except Exception as e:
        print(f"[!] Error for {addr}: {e}")  # only logged server-side
    finally:
        try:
            conn.close()
        except Exception:
            pass
        print(f"[-] Closed {addr}")


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(MAX_CONNECTIONS)
    print(f"[*] Listening on {HOST}:{PORT}")
    print(f"[*] Running program: {PROGRAM}")

    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        PROGRAM = sys.argv[1]
    if len(sys.argv) > 2:
        PORT = int(sys.argv[2])
    main()
