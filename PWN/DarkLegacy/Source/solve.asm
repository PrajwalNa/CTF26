MOV RA, 10
MOV RB, CMD
MOV RC, LEN
SYSCALL RA, RB, RC
HALT

CMD: .DS "pwdgetfattr -n /home/ctfuser/.ssh", 0
LEN: .DW 36