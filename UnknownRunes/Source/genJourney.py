# Generates journey.asm - the full RPG for Unknown Runes ISA
# All English strings are XOR-encrypted with key 0xCFA044
# XOR entire 24-bit words at once with 0x1FF1AD (LE).
# Strings are padded to multiples of 3 before null terminator.

KEY = [0xAD, 0xF1, 0x1F]  # encryprion for game strings [ADF11F]
KEY_WORD = KEY[0] | (KEY[1] << 8) | (KEY[2] << 16)  # 0x1FF1AD as loaded by VM

KEY_ANSM = [0xCF, 0xA0, 0x44]  # mage answer encryption [CFA044]
KEY_ANSM_WORD = KEY_ANSM[0] | (KEY_ANSM[1] << 8) | (KEY_ANSM[2] << 16)

KEY_FLAGM = [0x4E, 0x53, 0x46]  # mage flag encryption [NSF]
KEY_FLAGM_WORD = KEY_FLAGM[0] | (KEY_FLAGM[1] << 8) | (KEY_FLAGM[2] << 16)

KEY_ANSA = [0xFA, 0xCE, 0xAF]  # artificer answer encryption [FACEAF]
KEY_ANSA_WORD = KEY_ANSA[0] | (KEY_ANSA[1] << 8) | (KEY_ANSA[2] << 16)

KEY_FLAGA = [0x0B, 0xAD, 0xAF]  # artificer flag encryption [0BADAF]
KEY_FLAGA_WORD = KEY_FLAGA[0] | (KEY_FLAGA[1] << 8) | (KEY_FLAGA[2] << 16)


def xorEnc(s: str) -> list:
    raw = list(s.encode("ascii"))
    while len(raw) % 3 != 0:
        raw.append(0x00)
    return [(b ^ KEY[i % 3]) for i, b in enumerate(raw)]


def padLen(s: str) -> int:
    n = len(s)
    while n % 3 != 0:
        n += 1
    return n


S = {}
lines = []

# answers
MAGE_ANS = "I seek the p0wer of the dark 0ne: NOSFERATU"
MAGE_ANS_PLEN = padLen(MAGE_ANS)
# Mage Flag: {Hack3rs_Ar3_T3chinically_Dark_Mag3s}

ART_ANS = "resonance=core.tune:phase_314"
ART_ANS_PLEN = padLen(ART_ANS)
# Artificer Flag: {Artificer_Fl4g_1s_Res0n4nting@42}

# ========== Helper functions ==========


def emit(s):
    lines.append(s)


def add(label, text):
    S[label] = text


def prt(label):
    emit(f"    MOV RA, {label}")
    emit(f"    MOV RB, {SLENS[label]}")
    emit("    MOV RC, fn_print")
    emit("    CALL RC")


def prtK(label, key):
    emit(f"    MOV RA, {label}")
    emit(f"    MOV RB, {SLENS[label]}")
    emit(f"    MOV RC, 0x{key:06X}")
    emit("    STOREI RC, 0x10001E")
    emit("    MOV RC, fn_print")
    emit("    CALL RC")


def prt_save(label):
    emit("    PUSHA RA, RB, RC")
    emit(f"    MOV RA, {label}")
    emit(f"    MOV RB, {SLENS[label]}")
    emit("    MOV RC, fn_print")
    emit("    CALL RC")
    emit("    POPA RA, RB, RC")


def read_int():
    emit("    MOV RA, 3")
    emit("    SYSCALL RA")


def print_int_ra():
    emit("    PUSH RA")
    emit("    PUSH RB")
    emit("    MOVR RB, RA")
    emit("    MOV RA, 1")
    emit("    SYSCALL RA, RB")
    emit("    POP RB")
    emit("    POP RA")


def random_val():
    emit("    MOV RA, 8")
    emit("    SYSCALL RA")


def game_over():
    emit("    MZERO RB")
    emit("    MOV RA, 0")
    emit("    SYSCALL RA, RB")


# ========== STRINGS ==========
add("s_title", "=== UNKNOWN RUNES: A Journey Through the Arcane ===\n")
add("s_title2", "You find yourself in the city of Stormhaven...\n\n")
add("s_choose", "Choose your path:\n")
add("s_opt1", "  [1] The Mage\n")
add("s_opt2", "  [2] The Warrior\n")
add("s_opt3", "  [3] The Artificer\n")
add("s_opt4", "  [4] The Bard\n")
add("s_prompt", "> ")
add("s_invalid", "Invalid choice. Try again.\n")
add(
    "s_m_wake",
    "\n--- THE MAGE ---\nYou jolt awake, face pressed against a dusty tome.\nThe Grand Library is dim, candles guttering low.\nYou must have dozed off studying ancient incantations.\n\n",
)
add(
    "s_m_opts",
    "What do you do?\n  [1] Head to the Ruins to investigate strange energy\n  [2] Keep studying in the library\n  [3] Visit the tavern for food and drink\n",
)
add(
    "s_m_ruins",
    "\nYou gather your staff and head into the night.\nThe ruins of Ashenmoor loom before you, pulsing with eldritch light.\nTwo passages yawn open: left and right.\nA whisper tells you the scroll lies down one of them...\n\n",
)
add("s_m_left", "You take the LEFT passage...\n")
add("s_m_right", "You take the RIGHT passage...\n")
add(
    "s_m_scroll",
    "Among crumbled stones you find it - the Scroll of Binding!\nIts runes shimmer with barely contained power.\n\n",
)
add(
    "s_m_noscroll",
    "This passage leads to a dead end. Dust and silence.\nYou double back and find the scroll in the other path.\n\n",
)
add(
    "s_m_spirit",
    "A terrible presence materializes - an Unruly Spirit!\nIts form shifts between shadow and flame.\nYou must fight!\n\n",
)
add("s_m_hp", "  Your HP: ")
add("s_m_sphp", " | Spirit HP: ")
add(
    "s_m_atkopt",
    "\nChoose your spell:\n  [1] Fire Bolt\n  [2] Lightning Arc\n  [3] Ice Shard\n",
)
add("s_m_fire", "  You hurl a blazing Fire Bolt! ")
add("s_m_light", "  Lightning crackles from your fingers! ")
add("s_m_ice", "  You launch a shard of razor ice! ")
add("s_m_hit", "Hit! Damage: ")
add("s_m_miss", "The spell fizzles...\n")
add("s_m_spitatk", "  The spirit lashes out with dark tendrils! ")
add("s_m_spithit", "Hit! You take damage: ")
add("s_m_spitmiss", "You dodge the spectral strike!\n")
add(
    "s_m_spiritdie",
    "\nThe spirit shrieks and dissolves into motes of light!\nBut as it fades, the floor gives way beneath you...\n\n",
)
add(
    "s_m_youdie",
    "\nDarkness takes you. The spirit consumes your essence.\n=== GAME OVER ===\n",
)
add(
    "s_m_trap",
    "You fall into an ancient trap chamber!\nThe scroll glows in your hands. It demands an answer.\n\n",
)
add("s_m_riddle", "The scroll whispers: 'What is it that you seek?'\nAnswer: ")
add(
    "s_m_correct",
    "\nThe scroll shimmers with deep purple lighting!\nAncient knowledge floods your mind.\n\n",
)
add("s_m_flag", "{Hack3rs_Ar3_T3chinically_Dark_Mag3s}\n\n")
add(
    "s_m_evil",
    "But a small voice whispers to you...\n  [1] Embrace the Light - seal the ruins forever\n  [2] Continue into Darkness - claim the spirit's power\n",
)
add(
    "s_m_light_end",
    "\nWith a change of heart you let go of the scroll after healing yourself and seal the ruins. Peace returns to Stormhaven.\nYou are hailed as a hero of the Eldermis Magic Tower.\n=== THE SCHOLAR'S END ===\n",
)
add(
    "s_m_dark_end",
    "\nDark energy courses through your veins. Your eyes turn inky black.\nYou feel the power... you feel POWERFUL!! ... what would you do with your newfound strength, I wonder.\n=== THE DARK MAGE'S END ===\n",
)
add(
    "s_m_wrong",
    "\nThe scroll sears white-hot! Wrong answer.\nAncient runes crawl up your arms, draining your life force.\nYou scream, but the sound is swallowed by the void.\nThe scroll consumes what remains.\n=== GAME OVER ===\n",
)
add(
    "s_m_study",
    "\nYou bury yourself deeper in the books.\nPage after page, tome after tome...\nYour vision blurs. Your heart slows.\nThey find you in the morning, slumped over the desk.\n=== GAME OVER ===\n",
)
add(
    "s_m_tavern",
    "\nYou head to the Drunken Boar for a warm meal.\nThe barmaid serves you stew and ale.\nFeeling refreshed, you consider your next move.\n\n",
)
add("s_m_tav_opts", "  [1] Return to the library\n  [2] Head to the ruins\n")
add(
    "s_w_wake",
    "\n--- THE WARRIOR ---\n'Oi! We're closin' up!' the barmaid shouts.\nYou blink awake at your table in the Drunken Boar.\nEmpty tankards surround you. Your sword rests against the chair.\n\n",
)
add(
    "s_w_bump",
    "As you stumble toward the door, a hooded figure bumps you hard.\nYour temper flares.\n\n",
)
add(
    "s_w_opts",
    "What do you do?\n  [1] Grab them and teach them a lesson\n  [2] Let it go and walk outside\n",
)
add("s_w_fight", "\nYou seize the stranger by the collar. Fists fly!\n\n")
add("s_w_youhit", "  You land a solid punch! Damage: ")
add("s_w_youmiss", "  You swing wide and miss!\n")
add("s_w_enemhit", "  The stranger jabs you! Damage: ")
add("s_w_enemmiss", "  The stranger stumbles and misses!\n")
add("s_w_whp", "  Your HP: ")
add("s_w_ehp", " | Stranger HP: ")
add("s_w_fightopt", "\n  [1] Punch\n  [2] Headbutt\n  [3] Kick\n")
add("s_w_headbutt", "  You slam your forehead into them! Damage: ")
add("s_w_kick", "  You drive a boot into their gut! Damage: ")
add(
    "s_w_barwin",
    "\nThe stranger crumples. But the guard arrives.\nIrons clamp around your wrists.\n=== ARRESTED - GAME OVER ===\n",
)
add(
    "s_w_barlose",
    "\nA bottle smashes over your head. You wake in chains.\n=== ARRESTED - GAME OVER ===\n",
)
add(
    "s_w_peace",
    "\nYou take a breath and step into the cold night.\nYour coin purse is empty. You need gold.\n\n",
)
add(
    "s_w_peace_opt",
    "What do you do?\n  [1] Head to the forest to hunt\n  [2] Find somewhere to rest\n",
)
add(
    "s_w_forest",
    "\nYou venture into the Thornwood.\nA MUTANT BEAR appears! Twice normal size!\nIts eyes glow green. It charges!\n\n",
)
add("s_w_bearopt", "  [1] Slash\n  [2] Dodge\n  [3] Stab\n  [4] Flee!\n")
add("s_w_slash", "  You swing your blade! ")
add("s_w_dodge", "  You roll to the side! ")
add("s_w_stab", "  You thrust low at the beast! ")
add("s_w_flee", "  You turn and run! ")
add("s_w_flee_ok", "\nYou escape through the trees, battered but alive.\n\n")
add("s_w_flee_fail", "The bear swats you down! No escape!\n")
add("s_w_bhp", "  Your HP: ")
add("s_w_bearhp", " | Bear HP: ")
add("s_w_bearhit", "  The bear rakes you with claws! Damage: ")
add("s_w_bearmiss", "  The bear swings and misses!\n")
add("s_w_bearregen", "\nThe bear regenerates! It cannot be killed!\n")
add("s_w_wdie", "\nThe bear's jaws close. Darkness.\n=== GAME OVER ===\n")
add(
    "s_w_rest",
    "\nWith no coin for an inn, you curl up in an alley.\nThe night grows bitter cold. You never wake.\n=== FROZEN - GAME OVER ===\n",
)
add(
    "s_a_wake",
    "\n--- THE ARTIFICER ---\nYou come to on the workshop floor.\nScorch marks cover the ceiling. Your golem core lies cracked.\nAnother failed experiment. Your hands are singed.\n\n",
)
add(
    "s_a_opts",
    "What do you do?\n  [1] Fix the golem core now\n  [2] Head to the tavern\n  [3] Walk to the city centre\n",
)
add(
    "s_a_core",
    "\nYou pick up the cracked golem core.\nArcane circuitry pulses beneath the surface.\nThe instability is in the binding matrix.\n\n",
)
add("s_a_riddle", "Enter the resonance key to stabilize the core: ")
add(
    "s_a_correct",
    "\nThe core hums with perfect resonance!\nYour golem rises, eyes glowing steady blue.\nYou have created true artificial life!\n\n",
)
add("s_a_flag", "{Artificer_Fl4g_1s_Res0n4nting@42}\n\n")
add(
    "s_a_fame",
    "Word spreads. The Artificer who gave life to metal.\nYour name will echo through the ages.\n=== THE INVENTOR'S END ===\n",
)
add(
    "s_a_wrong",
    "\nThe core vibrates violently! Cracks spread...\nBOOOM!\nThe explosion levels your workshop.\n=== GAME OVER ===\n",
)
add(
    "s_a_tavern",
    "\nYou head to the Drunken Boar.\nMira the barmaid pours you an ale.\n'Another explosion?' she laughs.\nYou drink and chat until closing time.\n\n",
)
add("s_a_tav_opts", "  [1] Go work on the golem core\n  [2] Call it a night\n")
add(
    "s_a_rest",
    "\nYou collapse into bed. The golem haunts your dreams.\n=== THE DREAMER'S END ===\n",
)
add(
    "s_a_city",
    "\nYou wander the empty city streets.\nLanterns flicker. Footsteps echo behind you.\n\n",
)
add(
    "s_a_mug", "Two figures emerge from the shadows!\n'Empty your pockets, tinker!'\n\n"
)
add(
    "s_a_mugwin",
    "\nYou swing your heavy wrench and scatter the thugs!\nHeart racing, you hurry back to your workshop.\n\n",
)
add(
    "s_a_muglose",
    "\nA club meets the back of your skull.\nEverything goes dark. You never make it home.\n=== GAME OVER ===\n",
)
add(
    "s_b_wake",
    "\n--- THE BARD ---\nStars fill your vision. You're on a roof. Again.\nYour lute rests beside you, somehow intact.\nStormhaven stretches below, quiet under moonlight.\n\n",
)
add(
    "s_b_opts",
    "What do you do?\n  [1] Serenade the streets\n  [2] Sneak to the Lord's manor\n  [3] Perform at a tavern\n",
)
add(
    "s_b_serenade",
    "\nYou climb down and play a haunting melody.\nWindows open. People listen. Coins rain down.\nBut the city guard appears at 3 AM.\n'Move along, bard!' You bow and slip away.\n\n",
)
add(
    "s_b_ser_opts",
    "Where to next?\n  [1] The Lord's manor\n  [2] A tavern\n  [3] Leave town at dawn\n",
)
add(
    "s_b_lord",
    "\nYou creep across rooftops to the Lord's manor.\nIsolde waits at the balcony. 'You're late,' she whispers.\n\n...Some time later...\n\n'GUARDS! SOMEONE IN MY DAUGHTER'S CHAMBERS!'\n\n",
)
add(
    "s_b_escape",
    "You grab your lute and leap from the balcony!\nRolling through the garden, you sprint for the gates.\n\n",
)
add(
    "s_b_leave",
    "The Bard leaves Stormhaven forever,\nwith nothing but a lute, a grin, and a great story.\n=== THE WANDERER'S END ===\n",
)
add(
    "s_b_tavern",
    "\nYou find the Rusty Flagon still open.\nYou play ballads, jigs, and a rude song about the mayor.\nTips overflow your hat. A fine night.\n=== THE PERFORMER'S END ===\n",
)
add(
    "s_b_dawn",
    "\nDawn paints the sky amber. You hoist your pack\nand walk through the gates. New roads await.\n=== THE WANDERER'S END ===\n",
)
add("s_nl", "\n")

# ========== GENERATE ASSEMBLY ==========

SLENS = {k: padLen(v) for k, v in S.items()}
RAW_LENS = {k: len(v) for k, v in S.items()}


emit("; ============================================================")
emit("; journey.asm - Unknown Runes RPG")
emit("; All English strings XOR-encrypted with key 0xCFA044")
emit(f"; Decrypt: LOAD 3 bytes, XOR with 0x{KEY_WORD:06X} (LE), STORE back")
emit("; Generated by genJourney.py")
emit("; ============================================================")
emit("")
emit("; -------- MEMORY LAYOUT (STOREI/LOADI addresses) --------")
emit("; 0x100000 = player HP            0x100003 = enemy HP")
emit("; 0x100006 = temp var             0x100009 = temp var 2")
emit("; 0x10000C = fn_print: str addr   0x10000F = fn_print: str len")
emit("; 0x100012 = fn_print: loop idx")
emit("; 0x100015 = fn_check: ans addr   0x100018 = fn_check: ans len")
emit("; 0x10001B = fn_check: loop idx   0x10001E = fn_check: XOR key")
emit("; 0x100080 = input buffer (64B)   0x1000C0 = answer buffer (64B)")
emit(f"; XOR key (LE word): 0x{KEY_WORD:06X}")
emit("")
emit("; ===================== CODE START =====================")
emit("    JMP main")
emit("")

# ========== fn_print ==========
emit("; ========================================================")
emit("; fn_print: decrypt-in-place (3-byte XOR), print, re-encrypt")
emit("; IN:  RA = string addr, RB = padded length (mult of 3)")
emit("; ========================================================")
emit("fn_print:")
emit("    STOREI RA, 0x10000C")
emit("    STOREI RB, 0x10000F")
emit("    MZERO RC")
emit("    STOREI RC, 0x100012")
emit("fn_pr_dec:")
emit("    LOADI RA, 0x100012")
emit("    LOADI RB, 0x10000F")
emit("    JGE RA, RB, fn_pr_print")
emit("    LOADI RB, 0x10000C")
emit("    ADD RB, RB, RA")
emit("    LOAD RC, RB")
emit(f"    MOV RA, 0x{KEY_WORD:06X}")
emit("    XOR RC, RC, RA")
emit("    STORE RB, RC")
emit("    LOADI RA, 0x100012")
emit("    ADDI RA, 3")
emit("    STOREI RA, 0x100012")
emit("    JMP fn_pr_dec")
emit("fn_pr_print:")
emit("    MOV RA, 2")
emit("    LOADI RB, 0x10000C")
emit("    MZERO RC")
emit("    SYSCALL RA, RB, RC")
emit("    MZERO RA")
emit("    STOREI RA, 0x100012")
emit("fn_pr_enc:")
emit("    LOADI RA, 0x100012")
emit("    LOADI RB, 0x10000F")
emit("    JGE RA, RB, fn_pr_ret")
emit("    LOADI RB, 0x10000C")
emit("    ADD RB, RB, RA")
emit("    LOAD RC, RB")
emit(f"    MOV RA, 0x{KEY_WORD:06X}")
emit("    XOR RC, RC, RA")
emit("    STORE RB, RC")
emit("    LOADI RA, 0x100012")
emit("    ADDI RA, 3")
emit("    STOREI RA, 0x100012")
emit("    JMP fn_pr_enc")
emit("fn_pr_ret:")
emit("    RET")
emit("")

# ========== fn_read_str ==========
emit("fn_read_str:")
emit("    MOV RA, 4")
emit("    MOV RB, 0x100080")
emit("    MOV RC, 60")
emit("    SYSCALL RA, RB, RC")
emit("    RET")
emit("")

# ========== fn_check_answer ==========
emit("; fn_check_answer: decrypt expected answer, compare with input")
emit("; IN: RA = encrypted answer addr, RB = padded len")
emit("; OUT: RA = 0 if match")
emit("fn_check_answer:")
emit("    STOREI RA, 0x100015")
emit("    STOREI RB, 0x100018")
emit("    MZERO RC")
emit("    STOREI RC, 0x10001B")
emit("fn_ca_loop:")
emit("    LOADI RA, 0x10001B")
emit("    LOADI RB, 0x100018")
emit("    JGE RA, RB, fn_ca_cmp")
emit("    LOADI RB, 0x100015")
emit("    ADD RB, RB, RA")
emit("    LOAD RC, RB")
emit("    LOADI RA, 0x10001E")
emit("    XOR RC, RC, RA")
emit("    LOADI RA, 0x10001B")
emit("    MOV RB, 0x1000C0")
emit("    ADD RA, RB, RA")
emit("    STORE RA, RC")
emit("    LOADI RA, 0x10001B")
emit("    ADDI RA, 3")
emit("    STOREI RA, 0x10001B")
emit("    JMP fn_ca_loop")
emit("fn_ca_cmp:")
emit("    MOV RA, 6")
emit("    MOV RB, 0x100080")
emit("    MOV RC, 0x1000C0")
emit("    SYSCALL RA, RB, RC")
emit("    RET")
emit("")


# ==================== MAIN ====================
emit("; ===================== MAIN =====================")
emit("main:")
prt("s_title")
prt("s_title2")

emit("main_choose:")
prt("s_choose")
prt("s_opt1")
prt("s_opt2")
prt("s_opt3")
prt("s_opt4")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, path_mage")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, path_warrior")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, path_artificer")
emit("    MOV RB, 4")
emit("    JEQ RA, RB, path_bard")
prt("s_invalid")
emit("    JMP main_choose")
emit("")

# ==================== MAGE ====================
emit("; ==================== MAGE ====================")
emit("path_mage:")
prt("s_m_wake")

emit("mage_choice:")
prt("s_m_opts")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, mage_ruins")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, mage_study")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, mage_tavern")
prt("s_invalid")
emit("    JMP mage_choice")
emit("")

emit("mage_study:")
prt("s_m_study")
game_over()
emit("")

emit("mage_tavern:")
prt("s_m_tavern")
prt("s_m_tav_opts")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, mage_study")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, mage_ruins")
prt("s_invalid")
emit("    JMP mage_tavern")
emit("")

emit("mage_ruins:")
prt("s_m_ruins")
random_val()
emit("    MZERO RB")
emit("    JGE RA, RB, mage_r_pos")
emit("    NOT RA")
emit("    INC RA")
emit("mage_r_pos:")
emit("    MOV RB, 2")
emit("    MOD RA, RA, RB")
emit("    STOREI RA, 0x100006")
prt("s_m_left")
emit("    LOADI RA, 0x100006")
emit("    MZERO RB")
emit("    JEQ RA, RB, mage_scroll_found")
prt("s_m_noscroll")
emit("    JMP mage_got_scroll")
emit("mage_scroll_found:")
prt("s_m_scroll")
emit("mage_got_scroll:")
prt("s_m_spirit")
emit("    MOV RA, 50")
emit("    STOREI RA, 0x100000")
emit("    MOV RA, 100")
emit("    STOREI RA, 0x100003")
emit("")

emit("mage_combat:")
prt_save("s_m_hp")
emit("    LOADI RA, 0x100000")
print_int_ra()
prt_save("s_m_sphp")
emit("    LOADI RA, 0x100003")
print_int_ra()
prt("s_nl")
emit("    LOADI RA, 0x100003")
emit("    MZERO RB")
emit("    JLE RA, RB, mage_spirit_dead")
emit("    LOADI RA, 0x100000")
emit("    JLE RA, RB, mage_player_dead")
prt("s_m_atkopt")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, mage_fire")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, mage_lightning")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, mage_ice")
emit("    JMP mage_combat")
emit("")

for spell, sname in [
    ("fire", "s_m_fire"),
    ("lightning", "s_m_light"),
    ("ice", "s_m_ice"),
]:
    emit(f"mage_{spell}:")
    prt_save(sname)
    random_val()
    emit("    MZERO RB")
    emit("    JLT RA, RB, mage_spell_miss")
    random_val()
    emit("    MZERO RB")
    emit(f"    JGE RA, RB, mage_{spell}_dp")
    emit("    NOT RA")
    emit("    INC RA")
    emit(f"mage_{spell}_dp:")
    emit("    MOV RB, 11")
    emit("    MOD RA, RA, RB")
    emit("    ADDI RA, 5")
    emit("    PUSH RA")
    prt_save("s_m_hit")
    emit("    POP RA")
    emit("    PUSH RA")
    print_int_ra()
    prt("s_nl")
    emit("    POP RA")
    emit("    LOADI RB, 0x100003")
    emit("    SUB RB, RB, RA")
    emit("    STOREI RB, 0x100003")
    emit("    JMP mage_spirit_turn")
    emit("")

emit("mage_spell_miss:")
prt("s_m_miss")
emit("")
emit("mage_spirit_turn:")
prt_save("s_m_spitatk")
random_val()
emit("    MZERO RB")
emit("    JLT RA, RB, mage_spirit_miss")
random_val()
emit("    MZERO RB")
emit("    JGE RA, RB, mage_st_dp")
emit("    NOT RA")
emit("    INC RA")
emit("mage_st_dp:")
emit("    MOV RB, 8")
emit("    MOD RA, RA, RB")
emit("    ADDI RA, 3")
emit("    PUSH RA")
prt_save("s_m_spithit")
emit("    POP RA")
emit("    PUSH RA")
print_int_ra()
prt("s_nl")
emit("    POP RA")
emit("    LOADI RB, 0x100000")
emit("    SUB RB, RB, RA")
emit("    STOREI RB, 0x100000")
emit("    JMP mage_combat")
emit("")

emit("mage_spirit_miss:")
prt("s_m_spitmiss")
emit("    JMP mage_combat")
emit("")

emit("mage_player_dead:")
prt("s_m_youdie")
game_over()
emit("")

emit("mage_spirit_dead:")
prt("s_m_spiritdie")
prt("s_m_trap")
emit("")
emit("mage_scroll_riddle:")
prt("s_m_riddle")
emit("    MOV RC, fn_read_str")
emit("    CALL RC")
emit("    MOV RB, 0x100080")
emit("    ADD RA, RB, RA")
emit("    MZERO RC")
emit("    STORE RA, RC")
emit(f"    MOV RA, 0x{KEY_ANSM_WORD:06X}")
emit("    STOREI RA, 0x10001E")
emit("    MOV RA, s_m_ans")
emit(f"    MOV RB, {MAGE_ANS_PLEN}")
emit("    MOV RC, fn_check_answer")
emit("    CALL RC")
emit("    MZERO RB")
emit("    JEQ RA, RB, mage_correct")
prt("s_m_wrong")
game_over()
emit("")

emit("mage_correct:")
prt("s_m_correct")
prt("s_m_evil")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, mage_light_end")
prt("s_m_dark_end")
prtK("s_m_flag", KEY_FLAGM_WORD)
game_over()
emit("")

emit("mage_light_end:")
prt("s_m_light_end")
game_over()
emit("")

# ==================== WARRIOR ====================
emit("; ==================== WARRIOR ====================")
emit("path_warrior:")
prt("s_w_wake")
prt("s_w_bump")

emit("warrior_choice:")
prt("s_w_opts")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, warrior_fight")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, warrior_peace")
prt("s_invalid")
emit("    JMP warrior_choice")
emit("")

emit("warrior_fight:")
prt("s_w_fight")
emit("    MOV RA, 60")
emit("    STOREI RA, 0x100000")
emit("    MOV RA, 80")
emit("    STOREI RA, 0x100003")
emit("")

emit("warrior_bar_combat:")
prt_save("s_w_whp")
emit("    LOADI RA, 0x100000")
print_int_ra()
prt_save("s_w_ehp")
emit("    LOADI RA, 0x100003")
print_int_ra()
prt("s_nl")
emit("    LOADI RA, 0x100003")
emit("    MZERO RB")
emit("    JLE RA, RB, warrior_bar_win")
emit("    LOADI RA, 0x100000")
emit("    JLE RA, RB, warrior_bar_lose")
prt("s_w_fightopt")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, warrior_punch")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, warrior_headbutt")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, warrior_kick")
emit("    JMP warrior_bar_combat")
emit("")

for atk, slabel in [
    ("punch", "s_w_youhit"),
    ("headbutt", "s_w_headbutt"),
    ("kick", "s_w_kick"),
]:
    emit(f"warrior_{atk}:")
    prt_save(slabel)
    random_val()
    emit("    MZERO RB")
    emit("    JLT RA, RB, warrior_you_miss")
    random_val()
    emit("    MZERO RB")
    emit(f"    JGE RA, RB, warrior_{atk}_dp")
    emit("    NOT RA")
    emit("    INC RA")
    emit(f"warrior_{atk}_dp:")
    emit("    MOV RB, 10")
    emit("    MOD RA, RA, RB")
    emit("    ADDI RA, 5")
    emit("    PUSH RA")
    print_int_ra()
    prt("s_nl")
    emit("    POP RA")
    emit("    LOADI RB, 0x100003")
    emit("    SUB RB, RB, RA")
    emit("    STOREI RB, 0x100003")
    emit("    JMP warrior_enemy_turn")
    emit("")

emit("warrior_you_miss:")
prt("s_w_youmiss")
emit("")
emit("warrior_enemy_turn:")
prt_save("s_w_enemhit")
random_val()
emit("    MZERO RB")
emit("    JLT RA, RB, warrior_enemy_miss")
random_val()
emit("    MZERO RB")
emit("    JGE RA, RB, warrior_et_dp")
emit("    NOT RA")
emit("    INC RA")
emit("warrior_et_dp:")
emit("    MOV RB, 8")
emit("    MOD RA, RA, RB")
emit("    ADDI RA, 3")
emit("    PUSH RA")
print_int_ra()
prt("s_nl")
emit("    POP RA")
emit("    LOADI RB, 0x100000")
emit("    SUB RB, RB, RA")
emit("    STOREI RB, 0x100000")
emit("    JMP warrior_bar_combat")
emit("")

emit("warrior_enemy_miss:")
prt("s_w_enemmiss")
emit("    JMP warrior_bar_combat")
emit("")

emit("warrior_bar_win:")
prt("s_w_barwin")
game_over()
emit("")

emit("warrior_bar_lose:")
prt("s_w_barlose")
game_over()
emit("")

emit("warrior_peace:")
prt("s_w_peace")
emit("warrior_peace_choice:")
prt("s_w_peace_opt")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, warrior_forest")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, warrior_rest")
prt("s_invalid")
emit("    JMP warrior_peace_choice")
emit("")

emit("warrior_rest:")
prt("s_w_rest")
game_over()
emit("")

emit("warrior_forest:")
prt("s_w_forest")
emit("    MOV RA, 60")
emit("    STOREI RA, 0x100000")
emit("    MOV RA, 120")
emit("    STOREI RA, 0x100003")
emit("    MZERO RA")
emit("    STOREI RA, 0x100006")
emit("")

emit("warrior_bear_combat:")
prt_save("s_w_bhp")
emit("    LOADI RA, 0x100000")
print_int_ra()
prt_save("s_w_bearhp")
emit("    LOADI RA, 0x100003")
print_int_ra()
prt("s_nl")
emit("    LOADI RA, 0x100000")
emit("    MZERO RB")
emit("    JLE RA, RB, warrior_bear_die")
emit("    LOADI RA, 0x100006")
emit("    MOV RB, 3")
emit("    JGE RA, RB, warrior_bear_regen")
prt("s_w_bearopt")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, warrior_b_slash")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, warrior_b_dodge")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, warrior_b_stab")
emit("    MOV RB, 4")
emit("    JEQ RA, RB, warrior_b_flee")
emit("    JMP warrior_bear_combat")
emit("")

for atk, slabel in [("slash", "s_w_slash"), ("stab", "s_w_stab")]:
    emit(f"warrior_b_{atk}:")
    prt_save(slabel)
    random_val()
    emit("    MZERO RB")
    emit("    JLT RA, RB, warrior_b_youmiss")
    random_val()
    emit("    MZERO RB")
    emit(f"    JGE RA, RB, warrior_b_{atk}_dp")
    emit("    NOT RA")
    emit("    INC RA")
    emit(f"warrior_b_{atk}_dp:")
    emit("    MOV RB, 12")
    emit("    MOD RA, RA, RB")
    emit("    ADDI RA, 3")
    emit("    PUSH RA")
    prt_save("s_m_hit")
    emit("    POP RA")
    emit("    PUSH RA")
    print_int_ra()
    prt("s_nl")
    emit("    POP RA")
    emit("    LOADI RB, 0x100003")
    emit("    SUB RB, RB, RA")
    emit("    STOREI RB, 0x100003")
    emit("    LOADI RA, 0x100006")
    emit("    INC RA")
    emit("    STOREI RA, 0x100006")
    emit("    JMP warrior_bear_turn")
    emit("")

emit("warrior_b_dodge:")
prt("s_w_dodge")
emit("    LOADI RA, 0x100006")
emit("    INC RA")
emit("    STOREI RA, 0x100006")
emit("    JMP warrior_bear_turn")
emit("")

emit("warrior_b_youmiss:")
prt("s_m_miss")
emit("    LOADI RA, 0x100006")
emit("    INC RA")
emit("    STOREI RA, 0x100006")
emit("    JMP warrior_bear_turn")
emit("")

emit("warrior_b_flee:")
prt_save("s_w_flee")
random_val()
emit("    MZERO RB")
emit("    JGE RA, RB, warrior_flee_ok")
prt("s_w_flee_fail")
emit("    JMP warrior_bear_turn")
emit("")

emit("warrior_flee_ok:")
prt("s_w_flee_ok")
prt("s_w_rest")
game_over()
emit("")

emit("warrior_bear_turn:")
prt_save("s_w_bearhit")
random_val()
emit("    MZERO RB")
emit("    JLT RA, RB, warrior_bear_misses")
random_val()
emit("    MZERO RB")
emit("    JGE RA, RB, warrior_bt_dp")
emit("    NOT RA")
emit("    INC RA")
emit("warrior_bt_dp:")
emit("    MOV RB, 10")
emit("    MOD RA, RA, RB")
emit("    ADDI RA, 5")
emit("    PUSH RA")
print_int_ra()
prt("s_nl")
emit("    POP RA")
emit("    LOADI RB, 0x100000")
emit("    SUB RB, RB, RA")
emit("    STOREI RB, 0x100000")
emit("    JMP warrior_bear_combat")
emit("")

emit("warrior_bear_misses:")
prt("s_w_bearmiss")
emit("    JMP warrior_bear_combat")
emit("")

emit("warrior_bear_regen:")
prt("s_w_bearregen")
emit("    MOV RA, 100")
emit("    STOREI RA, 0x100003")
emit("    MZERO RA")
emit("    STOREI RA, 0x100006")
emit("    JMP warrior_bear_combat")
emit("")

emit("warrior_bear_die:")
prt("s_w_wdie")
game_over()
emit("")

# ==================== ARTIFICER ====================
emit("; ==================== ARTIFICER ====================")
emit("path_artificer:")
prt("s_a_wake")

emit("artificer_choice:")
prt("s_a_opts")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, artificer_core")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, artificer_tavern")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, artificer_city")
prt("s_invalid")
emit("    JMP artificer_choice")
emit("")

emit("artificer_core:")
prt("s_a_core")
emit("artificer_riddle:")
prt("s_a_riddle")
emit("    MOV RC, fn_read_str")
emit("    CALL RC")
emit("    MOV RB, 0x100080")
emit("    ADD RA, RB, RA")
emit("    MZERO RC")
emit("    STORE RA, RC")
emit(f"    MOV RA, 0x{KEY_ANSA_WORD:06X}")
emit("    STOREI RA, 0x10001E")
emit("    MOV RA, s_a_ans")
emit(f"    MOV RB, {ART_ANS_PLEN}")
emit("    MOV RC, fn_check_answer")
emit("    CALL RC")
emit("    MZERO RB")
emit("    JEQ RA, RB, artificer_correct")
prt("s_a_wrong")
game_over()
emit("")

emit("artificer_correct:")
prt("s_a_correct")
prtK("s_a_fame", KEY_FLAGA_WORD)
game_over()
emit("")

emit("artificer_tavern:")
prt("s_a_tavern")
prt("s_a_tav_opts")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, artificer_core")
prt("s_a_rest")
game_over()
emit("")

emit("artificer_city:")
prt("s_a_city")
prt("s_a_mug")
random_val()
emit("    MZERO RB")
emit("    JGE RA, RB, artificer_mug_win")
prt("s_a_muglose")
game_over()
emit("")

emit("artificer_mug_win:")
prt("s_a_mugwin")
emit("    JMP artificer_core")
emit("")

# ==================== BARD ====================
emit("; ==================== BARD ====================")
emit("path_bard:")
prt("s_b_wake")

emit("bard_choice:")
prt("s_b_opts")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, bard_serenade")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, bard_lord")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, bard_tavern")
prt("s_invalid")
emit("    JMP bard_choice")
emit("")

emit("bard_serenade:")
prt("s_b_serenade")
prt("s_b_ser_opts")
prt("s_prompt")
read_int()
emit("    MOV RB, 1")
emit("    JEQ RA, RB, bard_lord")
emit("    MOV RB, 2")
emit("    JEQ RA, RB, bard_tavern")
emit("    MOV RB, 3")
emit("    JEQ RA, RB, bard_dawn")
prt("s_invalid")
emit("    JMP bard_serenade")
emit("")

emit("bard_lord:")
prt("s_b_lord")
prt("s_b_escape")
prt("s_b_leave")
game_over()
emit("")

emit("bard_tavern:")
prt("s_b_tavern")
game_over()
emit("")

emit("bard_dawn:")
prt("s_b_dawn")
game_over()
emit("")

# ==================== DATA SECTION ====================
emit("; ==================== DATA SECTION ====================")
emit(f"; XOR key: 0xCF, 0xA0, 0x44 | LE word: 0x{KEY_WORD:06X}")
emit("; Strings padded to mult of 3, then null terminated")
emit("")

for label, text in S.items():
    enc = xorEnc(text)
    enc.append(0x00)
    hexvals = ", ".join(f"0x{b:02X}" for b in enc)
    preview = text[:50].replace("\n", "\\n")
    emit(f'; "{preview}" (raw={RAW_LENS[label]}, pad={SLENS[label]})')
    emit(f"{label}: .DB {hexvals}")
    emit("")

# Answers


def pad3(s):
    r = list(s.encode("ascii"))
    while len(r) % 3 != 0:
        r.append(0x00)
    return r


encM = [(b ^ KEY_ANSM[i % 3]) for i, b in enumerate(pad3(MAGE_ANS))]
encA = [(b ^ KEY_ANSA[i % 3]) for i, b in enumerate(pad3(ART_ANS))]

emit(f"; Mage answer (encrypted), padded len={MAGE_ANS_PLEN}")
emit(f"s_m_ans: .DB {', '.join(f'0x{b:02X}' for b in encM)}")
emit("")
emit(f"; Artificer answer (encrypted), padded len={ART_ANS_PLEN}")
emit(f"s_a_ans: .DB {', '.join(f'0x{b:02X}' for b in encA)}")
emit("")

# Write file
with open(r"journey.asm", "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"Generated journey.asm ({len(lines)} lines)")
print(f"Strings: {len(S)}, Key word: 0x{KEY_WORD:06X}")
