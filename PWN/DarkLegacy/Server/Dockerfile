FROM alpine:3.18

# Install Python and bash
RUN apk add --no-cache python3 bash attr

# Create unprivileged user for spawned shell commands
RUN adduser -D -s /bin/bash ctfuser

WORKDIR /home/ctfuser

# Server files — root-only, invisible to ctfuser
COPY util.py .
COPY server.py .
RUN chmod 700 util.py server.py

# Challenge binary — readable by everyone (VM needs to load it)
COPY Legacy.rune .
RUN chmod 644 Legacy.rune

# Fake Key
RUN printf '%s\n' \
    '-----BEGIN OPENSSH PRIVATE KEY-----' \
    'b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAlwAAAAdzc2gtcn' \
    'NhAAAAAwEAAQAAAIEA0Z2MPE1ePV9rN0FJhQXMkhj3eOScl7R6Cw9lXKMbPEFmuv3bRy' \
    'k7Y0KQwLt1Kp4SRzHP4yZ3LmN2AdfXqH8KaGRyFPKxl5TN8ki+FZ6VpTvR6+UaBme5WB' \
    'CTK4GPwtpY9JEk/cVOMR5BFcrD5mz2KILHVX+m0k8b7W5aTMOmZEAAAAFHJvb3RAZGFy' \
    'ay1sZWdhY3kAAAAHc3NoLXJzYQAAAIEA0Z2MPE1ePV9rN0FJhQXMkhj3eOScl7R6Cw9l' \
    'XKMbPEFmuv3bRyk7Y0KQwLt1Kp4SRzHP4yZ3LmN2AdfXqH8KaGRyFPKxl5TN8ki+FZ6' \
    'VpTvR6+UaBme5WBCTK4GPwtpY9JEk/cVOMR5BFcrD5mz2KILHVX+m0k8b7W5aTMOmZEA' \
    'AAADAQABAAAB+wJHT1hfZmxhZ19ub3RfaGVyZV9rZWVwX2xvb2tpbmcAAAAUcm9vdEBk' \
    'YXJrLWxlZ2FjeQ==' \
    '-----END OPENSSH PRIVATE KEY-----' \
    > /home/ctfuser/.ssh \
    && chown ctfuser:ctfuser /home/ctfuser/.ssh \
    && chmod 444 /home/ctfuser/.ssh

# Entrypoint sets the xattr then launches the server
COPY entrypoint.sh .
RUN chmod 700 entrypoint.sh

EXPOSE 8492

# Server runs as root so it can read its own source,
# but OS syscall drops to ctfuser before executing commands
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
# docker build -t dark-legacy .
# docker run -p 8492:8492 --rm --name dark-legacy dark-legacy