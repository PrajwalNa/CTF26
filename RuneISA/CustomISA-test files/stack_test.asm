; stack_test.asm - test new stack opcodes
    MOV RB, 42
    PUSH RB
    MZERO RB
    POP RB
    MOV RA, 1
    SYSCALL RA, RB      ; PRINT_INT(RA) -> 42
    HALT
