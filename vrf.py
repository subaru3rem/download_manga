import base64

class VrfGenerator:
    @staticmethod
    def atob(data: str) -> bytes:
        return base64.b64decode(data)

    @staticmethod
    def btoa(data: bytes) -> str:
        return base64.b64encode(data).decode()

    @staticmethod
    def rc4(key: bytes, data: bytes) -> bytes:
        s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + s[i] + key[i % len(key)]) & 0xFF
            s[i], s[j] = s[j], s[i]

        i = j = 0
        out = bytearray()
        for byte in data:
            i = (i + 1) & 0xFF
            j = (j + s[i]) & 0xFF
            s[i], s[j] = s[j], s[i]
            k = s[(s[i] + s[j]) & 0xFF]
            out.append(byte ^ k)
        return bytes(out)

    @staticmethod
    def transform(input_bytes, init_seed_bytes, prefix_key_bytes, prefix_len, schedule):
        out = bytearray()
        for i in range(len(input_bytes)):
            if i < prefix_len:
                out.append(prefix_key_bytes[i])
            transformed = schedule[i % 10](
                (input_bytes[i] ^ init_seed_bytes[i % 32]) & 0xFF
            ) & 0xFF
            out.append(transformed)
        return bytes(out)

    @staticmethod
    def reverse_transform(input_bytes, init_seed_bytes, prefix_key_bytes, prefix_len, schedule):
        out = bytearray()
        for i in range(len(input_bytes)):
            # pular bytes de prefixo
            if i < prefix_len:
                continue
            c = input_bytes[i]
            # tenta achar o valor original aplicando inversa
            for possible in range(256):
                # aplicar mesma transformação e ver se bate
                transformed = schedule[(i - prefix_len) % 10](
                    (possible ^ init_seed_bytes[(i - prefix_len) % 32]) & 0xFF
                ) & 0xFF
                if transformed == c:
                    out.append(possible)
                    break
        return bytes(out)

    # --- schedules ---
    scheduleC = [
        lambda c: (c - 48 + 256) & 0xFF,
        lambda c: (c - 19 + 256) & 0xFF,
        lambda c: (c ^ 241) & 0xFF,
        lambda c: (c - 19 + 256) & 0xFF,
        lambda c: (c + 223) & 0xFF,
        lambda c: (c - 19 + 256) & 0xFF,
        lambda c: (c - 170 + 256) & 0xFF,
        lambda c: (c - 19 + 256) & 0xFF,
        lambda c: (c - 48 + 256) & 0xFF,
        lambda c: (c ^ 8) & 0xFF,
    ]
    scheduleY = [
        lambda c: ((c << 4) | (c >> 4)) & 0xFF,
        lambda c: (c + 223) & 0xFF,
        lambda c: ((c << 4) | (c >> 4)) & 0xFF,
        lambda c: (c ^ 163) & 0xFF,
        lambda c: (c - 48 + 256) & 0xFF,
        lambda c: (c + 82) & 0xFF,
        lambda c: (c + 223) & 0xFF,
        lambda c: (c - 48 + 256) & 0xFF,
        lambda c: (c ^ 83) & 0xFF,
        lambda c: ((c << 4) | (c >> 4)) & 0xFF,
    ]
    scheduleB = [
        lambda c: (c - 19 + 256) & 0xFF,
        lambda c: (c + 82) & 0xFF,
        lambda c: (c - 48 + 256) & 0xFF,
        lambda c: (c - 170 + 256) & 0xFF,
        lambda c: ((c << 4) | (c >> 4)) & 0xFF,
        lambda c: (c - 48 + 256) & 0xFF,
        lambda c: (c - 170 + 256) & 0xFF,
        lambda c: (c ^ 8) & 0xFF,
        lambda c: (c + 82) & 0xFF,
        lambda c: (c ^ 163) & 0xFF,
    ]
    scheduleJ = [
        lambda c: (c + 223) & 0xFF,
        lambda c: ((c << 4) | (c >> 4)) & 0xFF,
        lambda c: (c + 223) & 0xFF,
        lambda c: (c ^ 83) & 0xFF,
        lambda c: (c - 19 + 256) & 0xFF,
        lambda c: (c + 223) & 0xFF,
        lambda c: (c - 170 + 256) & 0xFF,
        lambda c: (c + 223) & 0xFF,
        lambda c: (c - 170 + 256) & 0xFF,
        lambda c: (c ^ 83) & 0xFF,
    ]
    scheduleE = [
        lambda c: (c + 82) & 0xFF,
        lambda c: (c ^ 83) & 0xFF,
        lambda c: (c ^ 163) & 0xFF,
        lambda c: (c + 82) & 0xFF,
        lambda c: (c - 170 + 256) & 0xFF,
        lambda c: (c ^ 8) & 0xFF,
        lambda c: (c ^ 241) & 0xFF,
        lambda c: (c + 82) & 0xFF,
        lambda c: (c + 176) & 0xFF,
        lambda c: ((c << 4) | (c >> 4)) & 0xFF,
    ]

    rc4Keys = {
        "l": "u8cBwTi1CM4XE3BkwG5Ble3AxWgnhKiXD9Cr279yNW0=",
        "g": "t00NOJ/Fl3wZtez1xU6/YvcWDoXzjrDHJLL2r/IWgcY=",
        "B": "S7I+968ZY4Fo3sLVNH/ExCNq7gjuOHjSRgSqh6SsPJc=",
        "m": "7D4Q8i8dApRj6UWxXbIBEa1UqvjI+8W0UvPH9talJK8=",
        "F": "0JsmfWZA1kwZeWLk5gfV5g41lwLL72wHbam5ZPfnOVE=",
    }
    seeds32 = {
        "A": "pGjzSCtS4izckNAOhrY5unJnO2E1VbrU+tXRYG24vTo=",
        "V": "dFcKX9Qpu7mt/AD6mb1QF4w+KqHTKmdiqp7penubAKI=",
        "N": "owp1QIY/kBiRWrRn9TLN2CdZsLeejzHhfJwdiQMjg3w=",
        "P": "H1XbRvXOvZAhyyPaO68vgIUgdAHn68Y6mrwkpIpEue8=",
        "k": "2Nmobf/mpQ7+Dxq1/olPSDj3xV8PZkPbKaucJvVckL0=",
    }
    prefixKeys = {
        "O": "Rowe+rg/0g==",
        "v": "8cULcnOMJVY8AA==",
        "L": "n2+Og2Gth8Hh",
        "p": "aRpvzH+yoA==",
        "W": "ZB4oBi0=",
    }

    @classmethod
    def generate(cls, input_str: str) -> str:
        b = input_str.encode()

        b = cls.rc4(cls.atob(cls.rc4Keys["l"]), b)
        b = cls.transform(b, cls.atob(cls.seeds32["A"]), cls.atob(cls.prefixKeys["O"]), 7, cls.scheduleC)
        b = cls.rc4(cls.atob(cls.rc4Keys["g"]), b)
        b = cls.transform(b, cls.atob(cls.seeds32["V"]), cls.atob(cls.prefixKeys["v"]), 10, cls.scheduleY)
        b = cls.rc4(cls.atob(cls.rc4Keys["B"]), b)
        b = cls.transform(b, cls.atob(cls.seeds32["N"]), cls.atob(cls.prefixKeys["L"]), 9, cls.scheduleB)
        b = cls.rc4(cls.atob(cls.rc4Keys["m"]), b)
        b = cls.transform(b, cls.atob(cls.seeds32["P"]), cls.atob(cls.prefixKeys["p"]), 7, cls.scheduleJ)
        b = cls.rc4(cls.atob(cls.rc4Keys["F"]), b)
        b = cls.transform(b, cls.atob(cls.seeds32["k"]), cls.atob(cls.prefixKeys["W"]), 5, cls.scheduleE)

        out = cls.btoa(b)
        out = out.replace("+", "-").replace("/", "_").replace("=", "")
        return out

    @classmethod
    def reverse_generate(cls, vrf: str) -> str:
        # Base64URL decode
        vrf = vrf.replace("-", "+").replace("_", "/")
        padding = len(vrf) % 4
        if padding:
            vrf += "=" * (4 - padding)
        b = base64.b64decode(vrf)

        # inverter a sequência
        b = cls.reverse_transform(b, cls.atob(cls.seeds32["k"]), cls.atob(cls.prefixKeys["W"]), 5, cls.scheduleE)
        b = cls.rc4(cls.atob(cls.rc4Keys["F"]), b)
        b = cls.reverse_transform(b, cls.atob(cls.seeds32["P"]), cls.atob(cls.prefixKeys["p"]), 7, cls.scheduleJ)
        b = cls.rc4(cls.atob(cls.rc4Keys["m"]), b)
        b = cls.reverse_transform(b, cls.atob(cls.seeds32["N"]), cls.atob(cls.prefixKeys["L"]), 9, cls.scheduleB)
        b = cls.rc4(cls.atob(cls.rc4Keys["B"]), b)
        b = cls.reverse_transform(b, cls.atob(cls.seeds32["V"]), cls.atob(cls.prefixKeys["v"]), 10, cls.scheduleY)
        b = cls.rc4(cls.atob(cls.rc4Keys["g"]), b)
        b = cls.reverse_transform(b, cls.atob(cls.seeds32["A"]), cls.atob(cls.prefixKeys["O"]), 7, cls.scheduleC)
        b = cls.rc4(cls.atob(cls.rc4Keys["l"]), b)

        return b.decode(errors="ignore")

# Exemplo:
if __name__ == "__main__":
    # gen = VrfGenerator.generate("hello world")
    # print("VRF:", gen)
    rev = VrfGenerator.reverse_generate('5fcaUfZo7rW1-Z3vTEvXO5sJBfP2YeTM2NIVmftCuGhY5i8cron2eqsc')
    print("Reverso:", rev)
