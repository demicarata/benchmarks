#include "hal.h"
#include "simpleserial.h"
#include <stdint.h>

// Pointers into data:
//   data+0  = a0   data+4  = a1
//   data+8  = b0   data+12 = b1
// c0,c1,s use SRAM scratch. All sites recombine a = a0 ^ a1 -> HD(a0,a1).
uint8_t isw_gadget(uint8_t cmd, uint8_t scmd, uint8_t dlen, uint8_t *data)
{
    if (dlen != 16) return 0x04;

    volatile uint32_t scratch[4];   // c0, c1, s, spare

    trigger_high();
    __asm__ volatile (
        ".syntax unified        \n\t"
        "LDR  r0, [%[a0]]       \n\t"   // a0  (remnant set)
        "EOR  r2, r0            \n\t"   
        "LDR  r2, [%[a1]]       \n\t"   // a1  (load-load remnant w/ first ldr)
        "LDR  r1, [%[b0]]       \n\t"
        "LDR  r3, [%[b1]]       \n\t"      \n\t"
        "EOR  r3, r0            \n\t"   
        "STR  r2, [%[c0]]       \n\t"
        "STR  r3, [%[c1]]       \n\t"

        "LDR  r0, [%[a0]]       \n\t"
        "LDR  r1, [%[b1]]       \n\t"
        "LDR  r2, [%[a1]]       \n\t"
        "LDR  r3, [%[b0]]       \n\t"
        "EORS r0, r1            \n\t"   // opA1 = a0
        "EORS r2, r3            \n\t"   // opA2 = a1

        "LDR  r0, [%[a0]]       \n\t"
        "LDR  r1, [%[b1]]       \n\t"
        "LDR  r2, [%[a1]]       \n\t"
        "LDR  r1, [%[rnd]]      \n\t"   // s
        "EORS r1, r0            \n\t"   // opB1 = a0
        "EORS r1, r2            \n\t"   // opA2 = a1

        "LDR  r2, [%[c0]]       \n\t"
        "LDR  r3, [%[c1]]       \n\t"
        "EOR  r1, r2        \n\t"
        "EOR  r0, r3        \n\t"
        :
        : [a0] "r" (data),      [a1] "r" (data + 4),
                      [b0] "r" (data + 8),  [b1] "r" (data + 12),
                      [c0] "r" (&scratch[0]), [c1] "r" (&scratch[1]),
                      [rnd] "r" (&scratch[2])
                      : "r0", "r1", "r2", "r3", "cc", "memory"
    );
    trigger_low();

    (void)scratch;
    return 0x00;
}

int main(void)
{
    platform_init();
    init_uart();
    trigger_setup();

    simpleserial_init();
    simpleserial_addcmd(0x01, 16, isw_gadget);
    while (1)
        simpleserial_get();
}
