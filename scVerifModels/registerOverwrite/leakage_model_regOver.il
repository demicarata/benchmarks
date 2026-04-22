macro mov2_leak (w32 dst, w32 src)
{
  leak movTransition (dst ^w32 src);
}

macro ldr3_leak (w32 dst, w32 adr, w32 ofs)
  w32 val
{
  val <- [w32 mem (int) (adr +w32 ofs)];
  
  leak ldrTransition (dst, val);
}