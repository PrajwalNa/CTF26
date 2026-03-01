; test.asm - Exercise all major opcodes

; === Arithmetic ===
    MOV  RA, 30
    MOV  RB, 12
    ADD  RC, RA, RB     ; RC = 42
    MOV  RA, 1          ; PRINT_INT
    SYSCALL RA, RC      ; print 42

    MOV  RA, 100
    MOV  RB, 58
    SUB  RC, RA, RB     ; RC = 42
    MOV  RA, 1
    SYSCALL RA, RC      ; print 42

    MOV  RB, 40
    ADDI RB, 2          ; RB = 42
    MOV  RA, 1
    SYSCALL RA, RB      ; print 42

    MOV  RB, 50
    SUBI RB, 8          ; RB = 42
    MOV  RA, 1
    SYSCALL RA, RB      ; print 42

    MOV  RA, 6
    MOV  RB, 7
    MUL  RC, RA, RB     ; RC = 42
    MOV  RA, 1
    SYSCALL RA, RC      ; print 42

    MOV  RA, 85
    MOV  RB, 2
    DIV  RC, RA, RB     ; RC = 42
    MOV  RA, 1
    SYSCALL RA, RC      ; print 42

    MOV  RA, 47
    MOV  RB, 5
    MOD  RC, RA, RB     ; RC = 2
    MOV  RA, 1
    SYSCALL RA, RC      ; print 2

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC  ; print newline

; === Bitwise ===
    MOV  RA, 0xFF
    MOV  RB, 0x0F
    AND  RC, RA, RB     ; RC = 15
    MOV  RA, 1
    SYSCALL RA, RC      ; print 15

    MOV  RA, 0xF0
    MOV  RB, 0x0F
    OR   RC, RA, RB     ; RC = 255
    MOV  RA, 1
    SYSCALL RA, RC      ; print 255

    MOV  RA, 0xFF
    MOV  RB, 0xF0
    XOR  RC, RA, RB     ; RC = 15
    MOV  RA, 1
    SYSCALL RA, RC      ; print 15

    MOV  RB, 1
    SHL  RB, 4          ; RB = 16
    MOV  RA, 1
    SYSCALL RA, RB      ; print 16

    MOV  RB, 64
    SHR  RB, 3          ; RB = 8
    MOV  RA, 1
    SYSCALL RA, RB      ; print 8

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC

; === Misc ops ===
    MOV  RB, 999
    MZERO RB            ; RB = 0
    MOV  RA, 1
    SYSCALL RA, RB      ; print 0

    MOV  RB, 41
    INC  RB             ; RB = 42
    MOV  RA, 1
    SYSCALL RA, RB      ; print 42

    MOV  RB, 43
    DEC  RB             ; RB = 42
    MOV  RA, 1
    SYSCALL RA, RB      ; print 42

    MOV  RB, 42
    NOT  RB             ; RB = ~42 = -43 (bitwise NOT)
    MOV  RA, 1
    SYSCALL RA, RB      ; print -43

    MOV RB, 42
    NEG RB             ; RB = -42 (two's complement)
    MOV RA, 1
    SYSCALL RA, RB      ; print -42

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC

; === Jumps & loop ===
    MZERO RC            ; RC = 0 (counter)
    MOV  RB, 5          ; limit
loop:
    MOV  RA, 1          ; PRINT_INT
    SYSCALL RA, RC      ; print counter
    INC  RC
    JLT  RC, RB, loop   ; loop while RC < 5

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC

; === Memory ===
    MOV  RC, 42
    MOV  RB, 0x300
    STORE RB, RC        ; MEM[0x300] = 42
    MZERO RC
    LOAD RC, RB         ; RC = MEM[0x300] = 42
    MOV  RA, 1
    SYSCALL RA, RC      ; print 42

    MOV  RB, 99
    STOREI RB, 0x400    ; MEM[0x400] = 99
    MZERO RB
    LOADI RB, 0x400     ; RB = 99
    MOV  RA, 1
    SYSCALL RA, RB      ; print 99

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC

; === MOVR ===
    MOV  RA, 42
    MOVR RB, RA         ; RB = 42
    MOV  RA, 1
    SYSCALL RA, RB      ; print 42

; === PRINT_HEX ===
    MOV  RB, 255
    MOV  RA, 7          ; PRINT_HEX
    SYSCALL RA, RB      ; print 0xFF

; === Done ===
    MOV  RA, 2
    MOV  RB, done_msg
    MOV  RC, 0
    SYSCALL RA, RB, RC

    MOV  RA, 0
    MOV  RB, 0
    SYSCALL RA, RB      ; EXIT(0)

    HALT

sep:
    .ds "\n"

done_msg:
    .ds "\nAll tests passed!\n"
