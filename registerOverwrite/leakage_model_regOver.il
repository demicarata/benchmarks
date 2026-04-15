// Leakage model - defines the leakage semantics for the existing instructions

w32 opA;
w32 opB;

macro eors3_leak(w32 rd, w32 rs1, w32 rs2)
{
    leak xorCompResult(rs1 ^w32 rs2); // leaks the XOR result value
    leak xorTransition(rd, rs1 ^w32 rs2); // leaks the transition: the old rd value vs the new value
}

macro and3_leak(w32 rd, w32 rs1, w32 rs2)
{
    leak andCompResult(rs1 &w32 rs2); // idem
    leak andTransition(rd, rs1 &w32 rs2); // idem
}

macro str3_leak(w32 val, w32 adr, w32 ofs)
{
    // we assume stores do not leak
}

macro ldr3_leak(w32 dst, w32 adr, w32 ofs)
    w32 val
{
    val <- [w32 mem (int) (adr +w32 ofs)]; // val = the loaded word from the address + the offset. what load does basically
    leak loadTransition(dst, val); // leaks old dst vs loaded value
}
