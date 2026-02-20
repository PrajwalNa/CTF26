#!/bin/bash
# Set xattr at runtime (overlay2 strips them at build time)
setfattr -n user.description -v "{0ne_Last_T3st:Little0ne}" /home/ctfuser/.ssh
exec python3 -u server.py
