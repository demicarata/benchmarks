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

// Adjacent instructions
macro pipOpA1xOpA2(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(A1 ^w32 A2);
}

macro pipOpA1xOpB2(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(A1 ^w32 B2);
}

macro pipOpB1xOpA2(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 A2);
}

macro pipOpB1xOpB2(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 B2);
}

// Deeper stage
macro pipOpA1xOpA3(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(A1 ^w32 A3);
}

macro pipOpA1xOpB3(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(A1 ^w32 B3);
}

macro pipOpB1xOpA3(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 A3);
}

macro pipOpB1xOpB3(w32 dst, w32 src) {
    advance_pipeline(dst, src);
    leak pip(B1 ^w32 B3);
}

macro eors2_leak(w32 dst, w32 src){
    pipOpA1xOpA2(dst, src);
}