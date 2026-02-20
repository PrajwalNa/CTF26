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

    MOV  RA, 40
    ADDI RA, 2          ; RA = 42
    MOV  RB, 1
    SYSCALL RB, RA      ; print 42

    MOV  RA, 50
    SUBI RA, 8          ; RA = 42
    MOV  RB, 1
    SYSCALL RB, RA      ; print 42

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

    MOV  RA, 1
    SHL  RA, 4          ; RA = 16
    MOV  RB, 1
    SYSCALL RB, RA      ; print 16

    MOV  RA, 64
    SHR  RA, 3          ; RA = 8
    MOV  RB, 1
    SYSCALL RB, RA      ; print 8

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC

; === Misc ops ===
    MOV  RA, 999
    MZERO RA            ; RA = 0
    MOV  RB, 1
    SYSCALL RB, RA      ; print 0

    MOV  RA, 41
    INC  RA             ; RA = 42
    MOV  RB, 1
    SYSCALL RB, RA      ; print 42

    MOV  RA, 43
    DEC  RA             ; RA = 42
    MOV  RB, 1
    SYSCALL RB, RA      ; print 42

    MOV  RA, 42
    NOT  RA             ; RA = -42 (negation)
    MOV  RB, 1
    SYSCALL RB, RA      ; print -42

    MOV  RA, 0
    NEG  RA             ; RA = ~0 = -1
    MOV  RB, 1
    SYSCALL RB, RA      ; print -1

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC

; === Jumps & loop ===
    MZERO RA            ; RA = 0 (counter)
    MOV  RB, 5          ; limit
loop:
    MOV  RC, 1          ; PRINT_INT
    SYSCALL RC, RA      ; print counter
    INC  RA
    JLT  RA, RB, loop   ; loop while RA < 5

; === Print separator ===
    MOV  RA, 2
    MOV  RB, sep
    MOV  RC, 0
    SYSCALL RA, RB, RC

; === Memory ===
    MOV  RA, 42
    MOV  RB, 0x300
    STORE RB, RA        ; MEM[0x300] = 42
    MZERO RA
    LOAD RA, RB         ; RA = MEM[0x300] = 42
    MOV  RC, 1
    SYSCALL RC, RA      ; print 42

    MOV  RA, 99
    STOREI RA, 0x400    ; MEM[0x400] = 99
    MZERO RA
    LOADI RA, 0x400     ; RA = 99
    MOV  RB, 1
    SYSCALL RB, RA      ; print 99

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
    MOV  RA, 255
    MOV  RB, 7          ; PRINT_HEX
    SYSCALL RB, RA      ; print 0xFF

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
