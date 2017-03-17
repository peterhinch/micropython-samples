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


# Bit reverse an 8 bit value
def rbit8(v):
    v = (v & 0x0f) << 4 | (v & 0xf0) >> 4
    v = (v & 0x33) << 2 | (v & 0xcc) >> 2
    return (v & 0x55) << 1 | (v & 0xaa) >> 1

# Bit reverse a 16 bit value
def rbit16(v):
    v = (v & 0x00ff) << 8 | (v & 0xff00) >> 8
    v = (v & 0x0f0f) << 4 | (v & 0xf0f0) >> 4
    v = (v & 0x3333) << 2 | (v & 0xcccc) >> 2
    return (v & 0x5555) << 1 | (v & 0xaaaa) >> 1

# Bit reverse a 32 bit value
def rbit32(v):
    v = (v & 0x0000ffff) << 16 | (v & 0xffff0000) >> 16
    v = (v & 0x00ff00ff) << 8 | (v & 0xff00ff00) >> 8
    v = (v & 0x0f0f0f0f) << 4 | (v & 0xf0f0f0f0) >> 4
    v = (v & 0x33333333) << 2 | (v & 0xcccccccc) >> 2
    return (v & 0x55555555) << 1 | (v & 0xaaaaaaaa) >> 1
