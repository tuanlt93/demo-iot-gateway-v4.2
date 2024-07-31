import struct

def parse_register_data(c,id1,id2):
        """
        Parse modbus data 2 thanh ghi INT 16 => 32 bit
        """
        a = c[id1]
        b = c[id2]
        s = struct.pack(">l", (b<<16)|a)
        return struct.unpack(">l", s)[0]