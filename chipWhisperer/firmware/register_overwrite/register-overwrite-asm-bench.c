#include "hal.h" // HAL function definitions
#include "simpleserial.h" // include simpleserial
#include <stdint.h>
#include <stdlib.h>


uint8_t register_overwrite_bench(uint8_t cmd, uint8_t scmd, uint8_t dlen, uint8_t *data){
    if (dlen != 12) return 0x04; // SS_ERR_LEN

    trigger_high();
    __asm__ volatile (
        "LDR r1, [%[p0], #0]  \n\t"   // load x0 into r1
        "LDR r5, [%[pd], #0]  \n\t"   // load dummy into r5 — pipeline separator
        "LDR r1, [%[p1], #0]  \n\t"   // load x1 into r1 — register overwrite, potential remnant of x0
        :
        : [p0] "r" (data),             // x0
          [pd] "r" (data + 8),         // dummy
          [p1] "r" (data + 4)          // x1
        : "r1", "r5"
    );
    trigger_low();

    return 0x00;
}

int main(void){
    platform_init();
    init_uart();
    trigger_setup();
    simpleserial_init();
    simpleserial_addcmd(0x01, 12, register_overwrite_bench);
    while(1)
        simpleserial_get();
}

