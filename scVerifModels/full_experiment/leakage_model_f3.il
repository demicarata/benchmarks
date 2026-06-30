// scVerif leakage model — device: stm32f0
w32 lastLoad;
macro ldr3_leak(w32 dst, w32 adr, w32 ofs)
    w32 val
{
    val <- [w32 mem (int) (adr +w32 ofs)];

    // leak the xor between the last loaded value and the current loaded value
    // for load-load memory remnant effect
    leak loadRemnant(lastLoad ^w32 val);

    lastLoad <- val;
    val <- [w32 mem (int) (adr +w32 ofs)];
    
    leak ldrTransition (dst, val);
}

macro mov2_leak(w32 dst, w32 src)
{
  leak movTransition (dst ^w32 src);
}

// ── pip_reg_overwrite ──
w32 A1;
w32 B1;
w32 A2;
w32 B2;
w32 A3;
w32 B3;

// Shift everything one stage
macro advance_pipeline(w32 newA, w32 newB)
{
    A3 <- A2;
    B3 <- B2;
    A2 <- A1;
    B2 <- B1;
    A1 <- newA;
    B1 <- newB;
}

macro pip_opA1xopA2(w32 dst, w32 src)
{
    advance_pipeline(dst, src);
    leak pip(A1 ^w32 A2);
}

macro pip_opB1xopA2(w32 dst, w32 src)
{
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 A2);
}

macro pip_opB1xopB2(w32 dst, w32 src)
{
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 B2);
}

macro pip_opB1xopA3(w32 dst, w32 src)
{
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 A3);
}

macro pip_opB1xopB3(w32 dst, w32 src)
{
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 B3);
}

macro eors2_leak(w32 dst, w32 src)
{
    pip_opA1xopA2(dst, src);
    pip_opB1xopA2(dst, src);
    pip_opB1xopB2(dst, src);
    pip_opB1xopA3(dst, src);
    pip_opB1xopB3(dst, src);
}

// Effects skipped (no leakage detected or template missing):
// pip_reg_overwrite/opA1xopB2
// pip_reg_overwrite/opA1xopA3
// pip_reg_overwrite/opA1xopB3