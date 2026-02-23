# Lich Protocol Spec

Custom protocol for 'The Lich's Token' challenge.

## Overview
- Purpose: Hello (Arise), Remote Auth (SoulBind), Data Transfer (BoneCourier), Configuration (NecroticWeave), Command/Control (UndeadWhisper), Goodbye (EternalRest)
- Transport: TCP
- Message Format: `Header|Payload`
- Header: `ProtocolID|MessageType|PayloadLength|MagicBytes|Version|PayloadHash|Payload`
- MagicBytes: 0x4C1C48849200
- Version: 0.6
- PayloadHash: Blake3 of the payload for integrity verification
    - Messages with null payloads will still include a hash of an empty string to maintain consistency.


## State Machine
`Handshake (Arise) -> Authentication (SoulBind) -> Data Transfer (BoneCourier) / Configuration (NecroticWeave) / Command/Control (UndeadWhisper) -> Goodbye (EternalRest)`


## Protocols
| Protocol        | Name          | Message Type  | Code | Payload                                                       |
| --------------- | ------------- | ------------- | ---- | ------------------------------------------------------------- |
| Hello           | Arise         |               | AR   |
|                 |               | Request       | 0x01 | `AR\|0x01\|Len\|Hash\|clientInfo`                             |
|                 |               | Response      | 0x02 | `AR\|0x02\|Len\|Hash\|serverInfo`                             |
| Authentication  | SoulBind      |               | SB   |
|                 |               | Request       | 0x10 | `SB\|0x10\|...\|username\|pass`                               |
|                 |               | Response      | 0x11 | `SB\|0x11\|...\|accept/deny`                                  |
|                 |               | Elevate       | 0x12 | `SB\|0x12\|...\|token\|elevateRequest/AdminApprove\|flag`     |
| Data Transfer   | BoneCourier   |               | BC   |
|                 |               | RequestToSend | 0x20 | `BC\|0x20\|...\|dataSize\|userToken`                          |
|                 |               | ClearToSend   | 0x21 | `BC\|0x21\|...\|accept/deny`                                  |
|                 |               | DataPacket    | 0x22 | `BC\|0x22\|...\|dataChunk\|chunkHash\|userToken`              |
|                 |               | DataAck       | 0x23 | `BC\|0x23\|...\|\|Error\|chunkHash`                           |
| Configuration   | NecroticWeave |               | NW   |
|                 |               | SetConfig     | 0x30 | `NW\|0x30\|...\|configKey\|configValue\|adminToken/userToken` |
|                 |               | GetConfig     | 0x31 | `NW\|0x31\|...\|configKey\|adminToken/userToken`              |
|                 |               | GetConfigResp | 0x31 | `NW\|0x31\|...\|configKey\|configValue`                       |
|                 |               | Approve/Deny  | 0x34 | `NW\|0x34\|...\|configKey\|approve/deny`                      |
| Command/Control | UndeadWhisper |               | UW   |
|                 |               | CmdExec       | 0x40 | `UW\|0x40\|...\|command\|AdminToken`                          |
|                 |               | CmdResult     | 0x41 | `UW\|0x41\|...\|commandOutput`                                |
|                 |               | InvalidToken  | 0x42 | `UW\|0x42\|...\|errorMessage`                                 |
| Goodbye         | EternalRest   |               | ER   |
|                 |               | Request       | 0x50 | `ER\|0x50\|...\|userToken`                                    |
|                 |               | Response      | 0x51 | `ER\|0x51\|...\|goodbyeMessage`                               |
|                 |               | IDK you       | 0x52 | `ER\|0x52\|...\|errorMessage`                                 |

#### Notes:
- Any invalid/malformed message will receive 'IDK you' (0x52) response with an error message.
- Authentication tokens are required for all operations except the initial 'Arise' handshake.
- `SoulBind` login is only accepted after a successful `Arise` handshake from the same client IP within a short window (~30s).
- Config changes can be staged/run for the session by the user if the user is authorized for it, but require admin approval to be committed.
- Only the 'Arise' has no magic in the header and the hash is MD5.
- `clientInfo` carries client magic hint bytes (0x84 0x92), client version, and supported hash algorithms for compatibility checks.
- `serverInfo` returns server magic hint bytes (0x4C 0x1C), server version, and the hash algorithm chosen by the server.
- If `supported_hashes` does not include `Blake3`, the server returns `IDK you` (0x52) and closes the request.
- `chunkHash` is MD5 of the data chunk, server will verify it against the hash sent by client to ensure data integrity before acknowledging receipt.
- `...` is `PayloadLength|MagicBytes|Version|PayloadHash`
- NecroticWeave replies with Approve/Deny 0x34 for config changes depending on auth level for the chosen config change.
- username/pass are max 8 bytes each.


## Detail
- Header Size: 46 bytes
    - ProtocolID: 2 bytes (e.g., 'AR', 'SB', etc.)
    - MessageType: 1 byte (e.g., 0x01, 0x10, etc.)
    - PayloadLength: 4 bytes (unsigned integer)
    - MagicBytes: 6 bytes (0x4C 0x1C 0x48 0x84 0x92 0x00)
    - Version: 1 byte (0.6 -> 0x06)
    - PayloadHash: 32 bytes (Blake3 hash of the payload/MD5 for 'Arise')
- Payload: Variable length based on PayloadLength field, content depends on ProtocolID and MessageType.
- All multi-byte fields are in little-endian format.
- String encoding: UTF-8 for all string fields
- The server will validate the magic bytes & version followed by the payload hash & the token (except for the 'Arise' handshake) before processing the message. If any validation fails, it will respond with 'IDK you' (0x52) and an appropriate error code.
- Timeout of 10 seconds for every message by default, connection closed if client with `IDK you` response or if no message received within timeout period.


## Handshake (Arise)
- Client needs to initiate this before any login/auth or other operations. 
- Server will only accept login/auth attempts after a successful handshake from the same client IP within a short window (~30s).
- If clientInfo is invalid (wrong magicPart/version) or does not include "Blake3" in supported hashes, server responds with 'IDK you' (0x52).

#### clientInfo Structure
```
|magicPart|version|supportedHashes|
```
- magicPart: 2 bytes (0x84 0x92 hint bytes)
- version: 1 byte (client version, e.g., 0x06)
- supportedHashes: comma-delimited UTF-8 string that must include "Blake3"

#### serverInfo Structure
```
|magicPart|version|chosenHash|
```
- magicPart: 2 bytes (0x4C 0x1C hint bytes)
- version: 1 byte (server version)
- chosenHash: UTF-8 string (server's selected hash algorithm list, e.g., "Blake3, MD5")


## Authentication (SoulBind)
- First-time auth uses a hardcoded passphrase (to be discovered in binary reversing)
- Token size: 16 bytes (128 bits)
- Tokens are generated by the server upon successful authentication and must be included in subsequent messages for authorization.
- Tokens expire after 1 minute of inactivity by default, requiring re-authentication.
- One user can only have one active session at a time, subsequent auth attempts from same user will invalidate previous session.
- Authorization levels: 
  - Unprivileged: Users/regular tokens, cannot execute commands, limited config operations
  - Admin/Privileged: Admin tokens, can execute all commands, approve config changes


## Data Transfer (BoneCourier)
- Client needs to request to send data by specifying total data size and user token.
- Maximum data chunk size: 256 bytes
- Raw 16 byte MD5 hash of data chunk.
- Client must wait for 'ClearToSend' (0x21) response before sending data chunks. If denied, client can retry the request or abort the transfer.


## Configuration (NecroticWeave)
- Config keys and values are strings with a maximum length of 256 characters.
- Reads key/value from global config store. If not found, returns 'IDK you' (0x52).
- Can change default timeout, max data chunk size, and other parameters if authorized.
- Each session has their run config which can be modified for the specific session.
- Each new change will overwrite the previous.
- Server replies with approve/deny on config changes if user has sufficient authorization for that specific config key.
- Config keys: `["timeout=10", "maxChunkSize=256", "EleEnabled=False", "serverPort=9001", "tknExpire=60", "maxSess=5", "maxPayload=256", "EnCmdExec=False", "CmdSize=256"]`


## Command/Control (UndeadWhisper)
- Commands are strings with a maximum length of 256 characters by default.
- Command output is 256 bytes by default; if output exceeds this, it will be truncated and a warning included in response.
- Only admin/privileged tokens can execute commands. Unprivileged tokens attempting command execution will receive 'InvalidToken' (0x42) response with error code 0x0003 (Unauthorized).
- Specific commands may be whitelisted; unauthorized command attempts return error code 0x0004 (Command Not Allowed).


## Error Codes
| Code   | Meaning                          | Response Message Type                                          |
| ------ | -------------------------------- | -------------------------------------------------------------- |
| 0x0000 | Success                          | (varies)                                                       |
| 0x0001 | Invalid Magic/Version            | 0x52 (IDK you)                                                 |
| 0x0002 | Hash Verification Failed         | 0x52 (IDK you)                                                 |
| 0x0003 | Unauthorized (wrong token level) | 0x42 (InvalidToken if already authenticated) or 0x52 (IDK you) |
| 0x0004 | Command Not Allowed              | 0x42 (InvalidToken)                                            |
| 0x0005 | Token Expired                    | 0x52 (IDK you)                                                 |
| 0x0006 | Malformed Payload                | 0x52 (IDK you)                                                 |
| 0x0007 | Config Key Not Found             | 0x52 (IDK you)                                                 |
| 0x0008 | Data Chunk Hash Mismatch         | 0x23 (DataAck with error)                                      |
| 0x0009 | Transfer Denied                  | 0x21 (ClearToSend deny)                                        |


