#include "hal.h"
#include "simpleserial.h"
#include <stdint.h>

// data[0..3]  = x0
// data[4..7]  = m0 (mask for x0)
// data[8..11] = x1
// data[12..15]= m1 (mask for x1)
uint8_t pip_reg_overwrite_bench(uint8_t cmd, uint8_t scmd, uint8_t dlen, uint8_t *data)
{
    if (dlen != 16) return 0x04;

    trigger_high();
    __asm__ volatile (
        ".syntax unified          \n\t"
        "LDR r1, [%[base], #0]  \n\t"   // r1 = x0
        "LDR r2, [%[base], #4]  \n\t"   // r2 = m0
        "LDR r3, [%[base], #12] \n\t"   // r3 = m1
        "LDR r4, [%[base], #8]  \n\t"   // r4 = x1
        "EORS r1, r2             \n\t"   // x0 ^= m0
        "ADDS r5, r5, #1         \n\t"   // pipeline separator
        "EORS r3, r4             \n\t"   // m1 ^= x1
        :
        : [base] "l" (data)
        : "r1", "r2", "r3", "r4", "r5", "cc"
    );
    trigger_low();

    return 0x00;
}

int main(void)
{
    platform_init();
    init_uart();
    trigger_setup();
    simpleserial_init();
    simpleserial_addcmd(0x01, 16, pip_reg_overwrite_bench);
    while(1)
        simpleserial_get();
}
