; ============================================================
; legacy.asm - Runes ISA
; A continuation of Unknown Runes RPG
; ============================================================

; ======================== CODE START ========================

JMP main

; RB should be set by the caller
fn_print:
    MOV RA, 2
    MZERO RC
    SYSCALL RA, RB, RC
    MZERO RA
    RET

fn_read:
    ; act like seting space for buffer
    MZERO RC
    MZERO RA
    MOV RC, 8492
    loop:
        PUSHI 0
        INC RA
        POP RB
        JLE RA, RC, loop
    
    ; read the answer
    MOV RA, 4
    MOV RB, buffer
    MOV RC, 35
    SYSCALL RA, RB, RC
    MZERO RA
    RET

main:
    ; print the first prompt
    MOV RB, begin
    MOV RC, fn_print
    CALL RC

    ; print the second prompt
    MOV RB, begin2
    MOV RC, fn_print
    CALL RC

    ; print the third prompt
    MOV RB, begin3
    MOV RC, fn_print
    CALL RC

    ; print the question
    MOV RB, quest1
    MOV RC, fn_print
    CALL RC

    ; print the prompt
    MOV RB, promt
    MOV RC, fn_print
    CALL RC

    ; read the answer
    MOV RC, fn_read
    CALL RC
       
    ; validate
    JMP validate


; ======================= DATA SECTION =======================
; prompt string
begin: .DS "So, you've finally found this little gift that I left.\n", 0
begin2: .DS "Well, you sure took you're time, but I guess that's what makes it fun, right?\n", 0
begin3: .DS "Anyway, I'm not going to give you the boilerplate wise words about using power responsibly,\nI mean if you pass this last test of mine then you can rule the world or destroy it for all I care.\n", 0
quest1: .DS "Well far be it from me to bore you with tales of a dead man,\nYour final test is: 'what was it that I wanted?'\n", 0
promt: .DS "> ", 0


; =================== INPUT BUFFER ===========================
; 35 bytes - refernce for the 35 DB flag for UnknownRunes RPG {Hack3rs_Ar3_T3chinically_Dark_Mag3s}
; Overflow past 35 corrupts the validate handler below.
buffer:
    .DB 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    .DB 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    .DB 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    .DB 0, 0, 0, 0, 0

; =================== VALIDATE HANDLER =======================
; Overflow from buffer overwrites this handler
validate:
    MZERO RA
    MOVR RB, RA
    SYSCALL RA, RB