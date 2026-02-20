; stack_test.asm - test new stack opcodes
    MOV RA, 42
    PUSH RA
    MZERO RA
    POP RA
    MOV RB, 1
    SYSCALL RB, RA      ; PRINT_INT(RA) -> 42
    HALT
