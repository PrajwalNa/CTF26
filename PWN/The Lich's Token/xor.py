# xor with key to get flag bytes
flag = b'\x7B\x75\x6E\x44\x45\x41\x44\x5F\x54\x48\x52\x30\x4E\x33\x7D'
key = b'\xF0\x15\xAC\x71\xEE'

for i in range(len(flag)):
    print(hex(flag[i] ^ key[i % len(key)]), end="")
     