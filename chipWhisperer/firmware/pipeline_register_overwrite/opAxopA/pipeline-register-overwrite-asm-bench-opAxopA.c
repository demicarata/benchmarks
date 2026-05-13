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
        "LDR r1, [%[p0], #0]  \n\t"   // r1 = x0
        "LDR r2, [%[pm0], #0] \n\t"   // r2 = m0
        "LDR r3, [%[p1], #0]  \n\t"   // r3 = x1
        "LDR r4, [%[pm1], #0] \n\t"   // r4 = m1
        "EORS r1, r2           \n\t"   // x0 ^= m0
        "EORS r3, r4           \n\t"   // x1 ^= m1
        :
        : [p0]  "r" (data),
                      [pm0] "r" (data + 4),
                      [p1]  "r" (data + 8),
                      [pm1] "r" (data + 12)
                      : "r1", "r2", "r3", "r4", "cc"
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
