// value that was last written on the memory data path
w32 lastLoad;

macro ldr3_leak(w32 dst, w32 adr, w32 ofs)
    w32 val
{
    val <- [w32 mem (int) (adr +w32 ofs)];

    // leak the xor between the last loaded value and the current loaded value
    // for load-load memory remnant effect
    leak loadRemnant(lastLoad ^w32 val);

    lastLoad <- val;
}

