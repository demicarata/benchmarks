#include "hal.h" // HAL function definitions
#include "simpleserial.h" // include simpleserial
#include <stdint.h>
#include <stdlib.h>

// the shares are gonna be transmitted in the data field
uint8_t mem_remnant_bench(uint8_t cmd, uint8_t scmd, uint8_t dlen, uint8_t *data){
    if (dlen != 8) return 0x04; // SS_ERR_LEN

    trigger_high();
    __asm__ volatile (
        ".syntax unified          \n\t"
        "LDR r1, [%[p0], #0]  \n\t"   // load share x0
        "EORS r5, r5           \n\t"   // pipeline separator
        "LDR r2, [%[p1], #0]  \n\t"   // load share x1 (may interact with x0 remnant)
        :
        : [p0] "r" (data),        // point to x0 directly. trying to load volatile data messes with the structure of the assembly code
          [p1] "r" (data + 4)
        : "r1", "r2", "r5", "cc"
    );
    trigger_low();

    return 0x00;
}

int main(void){
    platform_init();
    init_uart();
    trigger_setup();
    simpleserial_init();
    simpleserial_addcmd(0x01, 8, mem_remnant_bench);
    while(1)
        simpleserial_get();
}
