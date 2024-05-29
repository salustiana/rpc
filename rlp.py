def to_binary(x: int) -> str:
    if x == 0:
        return ""
    return to_binary(int(x / 256)) + chr(x % 256)

def encode_length(l: int, offset: int) -> str:
    if l < 56:
        return chr(l + offset)
    if l < 2**64:
        bl = to_binary(l)
        return chr(len(bl) + offset + 55) + bl
    raise Exception(f"object too long")

def rlp_encode(obj) -> str:
    if type(obj) == int:
        if obj < 0x80:
            return chr(obj)
        # convert to string and fallthrough
        obj = str(obj)

    if type(obj) == str:
        if len(obj) == 1 and ord(obj) < 0x80:
            return obj
        return encode_length(len(obj), 0x80) + obj

    if type(obj) == list:
        output = "".join(rlp_encode(o) for o in obj)
        return encode_length(len(output), 0xc0) + output
    raise Exception("invalid type")

def to_int(bs: str) -> int:
    l = len(bs)
    if l == 0:
        raise Exception("null input")
    if l == 1:
        return ord(bs)
    return ord(bs[-1]) + to_int(bs[:-1]) * 256

def decode_length(bs: str) -> tuple[int, int, type]:
    l = len(bs)
    if l == 0:
        raise Exception("null input")

    p = ord(bs[0])

    if p < 0x80:
        return (0, 1, str)
    if p < 0xb8:
        slen = p - 0x80
        if l < slen:
            raise Exception(f"string of length {slen} specified, but {l} bytes left")
        return (1, slen, str)
    if p < 0xc0:
        slenlen = p - 0xb7
        if l < slenlen:
            raise Exception(f"string length of length {slenlen} specified, but {l} bytes left")
        slen = to_int(bs[1:slenlen+1])
        if l - slenlen < slen:
            raise Exception(f"string of length {slen} specified, but {l} bytes left")
        return (1 + slenlen, slen, str)
    if p < 0xf8:
        llen = p - 0xc0
        if l < llen:
            raise Exception("less bytes than specified")
        return (1, llen, list)
    if p < 256:
        llenlen = p - 0xf7
        if l < llenlen:
            raise Exception(f"list length of length {llenlen} specified, but {l} bytes left")
        llen = to_int(bs[1:llenlen+1])
        if l - llenlen < llen:
            raise Exception(f"list of length {llen} specified, but {l} bytes left")
        return (1 + llenlen, llen, list)
    raise Exception("not a byte")


def rlp_decode(bs: str) -> list:
    if len(bs) == 0:
        return []

    out = []
    (offset, olen, t) = decode_length(bs)

    if t == str:
        out.append(bs[offset:offset+olen])

    elif t == list:
        out.append(rlp_decode(bs[offset:offset+olen]))

    if (dec := rlp_decode(bs[offset+olen:])):
        out.extend(dec)
    return out

if __name__ == "__main__":
    enc = "".join(rlp_encode(o) for o in
        ["hola", [3, ["a", 45]], "Lorem ipsum dolor sit amet, consectetur adipisicing elit", 3, 1]
    )
    print(rlp_decode(enc))
