; hello.asm - Hello World for Unknown Runes ISA

    MOV  RA, 2          ; syscall PRINT_STR
    MOV  RB, msg        ; string address
    MOV  RC, 0          ; length 0 = null-terminated
    SYSCALL RA, RB, RC  ; print "Hello, World!"

    MOV  RA, 0          ; syscall EXIT
    MOV  RB, 0          ; exit code 0
    SYSCALL RA, RB      ; exit

    HALT

msg:
    .ds "Hello, World!\n"
