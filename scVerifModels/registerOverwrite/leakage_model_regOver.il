macro mov2_leak (w32 dst, w32 src)
{
  leak movTransition (dst ^w32 src);
}