@micropython.asm_thumb
def reverse(r0, r1):               # bytearray, len(bytearray)
    add(r4, r0, r1)
    sub(r4, 1) # end address
    label(LOOP)
    ldrb(r5, [r0, 0])
    ldrb(r6, [r4, 0])
    strb(r6, [r0, 0])
    strb(r5, [r4, 0])
    add(r0, 1)
    sub(r4, 1)
    cmp(r4, r0)
    bpl(LOOP)
   
def test():
    a = bytearray([0, 1, 2, 3]) # even length
    reverse(a, len(a))
    print(a)
    a = bytearray([0, 1, 2, 3, 4]) # odd length
    reverse(a, len(a))
    print(a)
    

