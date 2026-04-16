w32 dst0;
w32 OpA0;
w32 OpB0;
w32 dst1;
w32 OpA1;
w32 OpB1;

macro leak_pipeline(w32 dstNew, w32 OpANew, w32 OpBNew)
{
   // shift pipeline stage variables
   OpA1 <- OpA0;
   OpB1 <- OpB0;
   dst1 <- dst0;

   // insert new values into first stage of pipeline
   OpA0 <- OpANew;
   OpB0 <- OpBNew;
   dst0 <- dstNew;

   // leak stages 0, 1
   leak pip (OpA0 ^w32 OpA1);
   leak pip (OpB0 ^w32 OpB1);
   leak pip (dst0 ^w32 dst1);

   // leak stages 0, 1 cross op op
   leak pip (OpA0 ^w32 OpB1);
   leak pip (OpB0 ^w32 OpA1);

   // leak stages 0, 1 cross op target
   leak pip (dst0 ^w32 OpB1);
   leak pip (dst0 ^w32 OpA1);
   leak pip (dst1 ^w32 OpB0);
   leak pip (dst1 ^w32 OpA0);
}

macro eors2_leak(w32 dst, w32 src) {
    leak_pipeline(dst, src, (w32) 0);
}