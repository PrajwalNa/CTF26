#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>

#define ingredientCount 6
#define totalChecks 10
#define maxAttempts 3
#define cooldownMs 1500u
#define meterStepMs 110u
#define explodeStepMs 70u

// Delay failed attempts to slow down rapid guessing.
static void sleepMs(unsigned int ms) {
    Sleep(ms);
    }

// Ingredient runes are limited to lowercase letters and digits.
static int isAllowedIngredient(char ch) {
    if (ch >= 'a' && ch <= 'z') {
        return 1;
        }
    if (ch >= '0' && ch <= '9') {
        return 1;
        }
    return 0;
    }

// Render heat + stability on one terminal line.
static void renderMeters(int heatLevel, int stabilityLevel) {
    const int meterWidth = 20;
    const int heatFilled = (heatLevel * meterWidth) / totalChecks;
    const int stabilityFilled = (stabilityLevel * meterWidth) / totalChecks;
    int i = 0;

    printf("\rHeat: [");
    for (i = 0; i < meterWidth; i++) {
        putchar((i < heatFilled) ? '#' : '.');
        }
    printf("] %d/%d  Stability: [", heatLevel, totalChecks);
    for (i = 0; i < meterWidth; i++) {
        putchar((i < stabilityFilled) ? '#' : '.');
        }
    printf("] %d/%d", stabilityLevel, totalChecks);
    fflush(stdout);
    }

// Smoothly move both bars toward target values.
static void animateMeters(int* heat, int targetHeat, int* stability, int targetStability, unsigned int stepMs) {
    if (targetHeat < 0) {
        targetHeat = 0;
        }
    if (targetHeat > totalChecks) {
        targetHeat = totalChecks;
        }
    if (targetStability < 0) {
        targetStability = 0;
        }
    if (targetStability > totalChecks) {
        targetStability = totalChecks;
        }

    while ((*heat != targetHeat) || (*stability != targetStability)) {
        if (*heat < targetHeat) {
            (*heat)++;
            }
        else if (*heat > targetHeat) {
            (*heat)--;
            }

        if (*stability < targetStability) {
            (*stability)++;
            }
        else if (*stability > targetStability) {
            (*stability)--;
            }

        renderMeters(*heat, *stability);
        sleepMs(stepMs);
        }
    }

// One check result:
// pass -> cool slightly; fail -> heat rises and stability drops.
static void applyCheckResult(int passed, int* heat, int* stability, int* failCount) {
    if (passed != 0) {
        int targetHeat = (*heat > 0) ? (*heat - 1) : *heat;

        if (targetHeat != *heat) {
            animateMeters(heat, targetHeat, stability, *stability, meterStepMs);
            }
        else {
            renderMeters(*heat, *stability);
            sleepMs(meterStepMs);
            }
        return;
        }

    (*failCount)++;
    animateMeters(heat, *heat + 1, stability, *stability - 1, meterStepMs);
    }

// Final detonation animation once stability reaches zero.
static void explodeAnimation(int* heat, int* stability) {
    animateMeters(heat, totalChecks, stability, 0, explodeStepMs);
    putchar('\n');
    printf("BOOM!\n");
    }

// Constraint-based validator; no direct compare against plaintext input.
// Returns: 1 = stable/pass, 0 = failed but still alive, -1 = exploded.
static int validateMixture(const char mix[ingredientCount]) {
    int heat = 0;
    int stability = totalChecks;
    int failCount = 0;
    int ember = (int)mix[0];
    int frost = (int)mix[1];
    int bile = (int)mix[2];
    int root = (int)mix[3];
    int mist = (int)mix[4];
    int ash = (int)mix[5];

    puts("Balancing the brew...");
    renderMeters(heat, stability);

    // Always execute all checks; instability accumulates within this attempt.
    applyCheckResult((ember + (int)frost) == 150, &heat, &stability, &failCount);
    applyCheckResult((bile ^ 0x33) == 95, &heat, &stability, &failCount);
    applyCheckResult((frost + (int)root) == 149, &heat, &stability, &failCount);
    applyCheckResult((bile - (int)root) == 11, &heat, &stability, &failCount);
    applyCheckResult((root - (int)mist) == -13, &heat, &stability, &failCount);
    applyCheckResult(((ember * 7 + (int)mist) % 26) == 16, &heat, &stability, &failCount);
    applyCheckResult(((mist ^ (int)ember)) == 12, &heat, &stability, &failCount);
    applyCheckResult(((ash & 0xF)) == 3, &heat, &stability, &failCount);
    applyCheckResult((bile + (int)ash) == 207, &heat, &stability, &failCount);
    applyCheckResult(((frost * 3 + (int)ash) % 26) == 21, &heat, &stability, &failCount);

    if (failCount == 0) {
        // Fully correct recipe restores stability to full.
        animateMeters(&heat, 0, &stability, totalChecks, meterStepMs);
        putchar('\n');
        return 1;
        }

    if (stability <= 0) {
        explodeAnimation(&heat, &stability);
        return -1;
        }

    // Attempt failed, but cauldron survived: recover to stable before next attempt.
    animateMeters(&heat, 0, &stability, totalChecks, meterStepMs);
    putchar('\n');
    return 0;
    }

__attribute__((noinline, used))
static void revealReward(void) {
    // Decrypt reward only after the mixture is stable.
    static const uint8_t sealed[] = {
        0x2D, 0x19, 0x63, 0x17, 0x14, 0x13, 0x0A, 0x67, 0x09, 0x0B,
        0x7B, 0x0B, 0x11, 0x09, 0x13, 0x18, 0x0A, 0x63, 0x01, 0x2F
        };
    // UTF-8 bytes for "VIPER".
    static const uint8_t key[] = { 0x56, 0x49, 0x50, 0x45, 0x52 };
    char out[sizeof(sealed) + 1];
    size_t i = 0u;

    for (i = 0u; i < sizeof(sealed); i++) {
        out[i] = (char)(sealed[i] ^ key[i % sizeof(key)]);
        }
    out[sizeof(sealed)] = '\0';

    puts(out);
    }

int main(void) {
    char input[64];
    size_t n = 0u;
    size_t i = 0u;
    int attempt = 0;

    puts("The potion needs exactly six ingredients.");
    puts("Too many or too few and the cauldron turns unstable.");
    puts("The cauldron allows only a handful of attempts.");

    // Local lockout policy: finite attempts plus cooldown after failures.
    for (attempt = 1; attempt <= maxAttempts; attempt++) {
        printf("\nAttempt %d/%d\n", attempt, maxAttempts);
        puts("Enter the 6-character ingredient code:");
        printf("> ");

        if (fgets(input, sizeof(input), stdin) == NULL) {
            puts("The fire dies before the brew is tested.");
            return 1;
            }

        n = strcspn(input, "\r\n");
        input[n] = '\0';

        if (n != ingredientCount) {
            puts("Unstable mixture: the cauldron requires exactly six ingredients.");
            }
        else {
            // Reject invalid rune charset before running constraint checks.
            int allowed = 1;
            for (i = 0u; i < ingredientCount; i++) {
                if (!isAllowedIngredient(input[i])) {
                    allowed = 0;
                    break;
                    }
                }

            if (!allowed) {
                puts("That ingredient code is forbidden in this lab.");
                }
            else {
                int result = validateMixture(input);
                if (result == 1) {
                    // Success path: print decrypted reward and exit.
                    puts("The brew stabilizes. Reward revealed:");
                    revealReward();
                    return 0;
                    }
                if (result == -1) {
                    puts("The potion destabilizes and explodes.");
                    return 0;
                    }
                puts("The brew wobbles, but the cauldron holds.");
                }
            }

        if (attempt < maxAttempts) {
            printf("Cooling the cauldron for %u ms...\n", cooldownMs);
            sleepMs(cooldownMs);
            }
        }

    puts("\nLockout: the cauldron seals itself after repeated failed attempts.");
    return 0;
    }
