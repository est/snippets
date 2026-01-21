#!/usr/env/bin python3

import ctypes
from ctypes.util import find_library

# Load libc
libc_path = find_library("c")
libc = ctypes.CDLL(libc_path)

# Declare res_query signature:
# int res_query(const char *dname, int class, int type, unsigned char *answer, int anslen);
libc.res_query.argtypes = [
    ctypes.c_char_p,  # dname
    ctypes.c_int,     # class (C_IN)
    ctypes.c_int,     # type (T_TXT, T_SRV, etc.)
    ctypes.POINTER(ctypes.c_ubyte),  # answer buffer
    ctypes.c_int      # buffer length
]
libc.res_query.restype = ctypes.c_int

# DNS constants
C_IN = 1      # Internet class
T_TXT = 16    # TXT record
T_SRV = 33    # SRV record
T_A = 1       # A record
T_AAAA = 28   # AAAA record

# Allocate buffer
BUF_SIZE = 512
answer = (ctypes.c_ubyte * BUF_SIZE)()

# Query example.com TXT record
domain = b"example.com"
ret = libc.res_query(domain, C_IN, T_A, answer, BUF_SIZE)

if ret < 0:
    # errno = ctypes.get_errno()
    raise OSError(ret, "res_query failed")

# 'answer' now contains raw DNS packet of length ret bytes
raw_packet = bytes(answer[:ret])
print(f"Raw DNS packet ({ret} bytes): {raw_packet.hex()}")
