#!/usr/bin/python3

"""
MD2 Message Digest Algorithm.
Implemented by Cameron Lonsdale to the spec of RFC 1319.
"""

import binascii

# Permutation of 0..255 constructed from the digits of pi.
# It gives a "random" nonlinear byte substitution operation.
#
# Cameron's Notes:
# ~~~~~~~~~~~~~~~~
# S-box (substitution-box). Attempting to obscure the relationship between the input and the output.
# This aids in providing the diffusion property. Also known as the Avalance effect.
#
# The table was generated using the digits from the fractional part of Pi.
# Numbers used as cryptographic constants are called nothing up my sleeve numbers.
# If the numbers can be generated from a well known method or mathematical property,
# its likely that the designer has nothing up their sleeve and the constants were not nefariously chosen.
# If the constants seem arbitrary and with no explanation of how they came about, its possible that they were
# chosen to create a backdoor to the algorithm.
Sbox = [
    41, 46, 67, 201, 162, 216, 124, 1, 61, 54, 84, 161, 236, 240, 6,
    19, 98, 167, 5, 243, 192, 199, 115, 140, 152, 147, 43, 217, 188,
    76, 130, 202, 30, 155, 87, 60, 253, 212, 224, 22, 103, 66, 111, 24,
    138, 23, 229, 18, 190, 78, 196, 214, 218, 158, 222, 73, 160, 251,
    245, 142, 187, 47, 238, 122, 169, 104, 121, 145, 21, 178, 7, 63,
    148, 194, 16, 137, 11, 34, 95, 33, 128, 127, 93, 154, 90, 144, 50,
    39, 53, 62, 204, 231, 191, 247, 151, 3, 255, 25, 48, 179, 72, 165,
    181, 209, 215, 94, 146, 42, 172, 86, 170, 198, 79, 184, 56, 210,
    150, 164, 125, 182, 118, 252, 107, 226, 156, 116, 4, 241, 69, 157,
    112, 89, 100, 113, 135, 32, 134, 91, 207, 101, 230, 45, 168, 2, 27,
    96, 37, 173, 174, 176, 185, 246, 28, 70, 97, 105, 52, 64, 126, 15,
    85, 71, 163, 35, 221, 81, 175, 58, 195, 92, 249, 206, 186, 197,
    234, 38, 44, 83, 13, 110, 133, 40, 132, 9, 211, 223, 205, 244, 65,
    129, 77, 82, 106, 220, 55, 200, 108, 193, 171, 250, 36, 225, 123,
    8, 12, 189, 177, 74, 120, 136, 149, 139, 227, 99, 232, 109, 233,
    203, 213, 254, 59, 0, 29, 57, 242, 239, 183, 14, 102, 88, 208, 228,
    166, 119, 114, 248, 235, 117, 75, 10, 49, 68, 80, 180, 143, 237,
    31, 26, 219, 153, 141, 51, 159, 17, 131, 20
]

block_size = 16  # 16 bytes or 128 bits

message = input()
message_bytes = bytearray(message, 'utf-8')

# Step 1: Append Padding Bytes
# ============================
# Even if the length is a multiple of 16, 16 bytes are still appended.
# i bytes of value i are appended.
padding = block_size - (len(message_bytes) % block_size)
message_bytes += bytearray(padding for _ in range(padding))

# Cameron's Note:
# ~~~~~~~~~~~~~~
# Padding is understandable as the further functions rely on a certain block size,
# so its essential that the sizes of blocks match.
# I'm unsure why the padding values are the same value as the padding length.
# If the padding was a fixed value would one of the hash properties be weakened?
#
# A partial answer to this question is that there are multiple different types of padding (cause why not)
# The specific padding used in MD2 is called PKCS7. see: https://en.wikipedia.org/wiki/Padding_(cryptography)
# From the expanation given, it seems necessary for certain encryption schemes, but for hashing its unclear.
# My intuition is telling me that another padding scheme could be used without damaging any cryptographic properties.
#
# Actually it can be. For MD to work effectively, MD-compliant padding MUST be used. Which must have the following properties
# - M is a prefix of Pad(M)
# - If |M_1| = |M_2| (length) then |Pad(M_1)| = |Pad(M_2)|
# - If |M_1| != |M_2| then the last block of Pad(M_1) is different to the last block of Pad(M_2)
#
# With these conditions, Zero padding still holds, so unless something else is coming into play, choosing a MD-compliant padding
# is all that is required.


# Step 2: Append Checksum
# =======================
# 16 byte checksum is appended to message_bytes
previous_checkbyte = 0  # Used as an Initialisation Vector (IV)
checksum = bytearray(0 for _ in range(block_size))

# Process each 16-word block (16 bytes per block)
for i in range(len(message_bytes) // block_size):
    # Calculate checksum of block using each byte of the block
    for j in range(block_size):
        byte = message_bytes[i * block_size + j]
        previous_checkbyte = checksum[j] = Sbox[byte ^ previous_checkbyte]

message_bytes += checksum

# Cameron's Note:
# ~~~~~~~~~~~~~~
# I'm thinking about why the Sbox is used here. Does the checksum also need to add to diffusion?
# If you remove it, how does it affect the overall hash?

# Interestingly, the checksum does not take into account the entire message other than through the previous_checkbyte.
# You can have a checksum match between messages if the last block is the same AND the previous_checkbyte of the previous block
# is the same. Because padding is included, we can get a checksum collision with just a single block.
# The blocks
# b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00"
# and
# b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xaa"
# Both have checksum values of cc3b183d1701a7099359c295711936e0
# With complete hash values of 9aac6a2bb4bbd9f70d192e01dbdfb0be and 366683424c1157b3e4df675dbc10103d respectively.
#
# Here is the snippet to generate collisions:
# block_size = 16
# matches = {}

# for block in range(0, 2**(block_size * 8)):
#     message = bytearray.fromhex('{:032x}'.format(block))
#     checksum = md2_checksum(message)

#     if checksum in matches:
#         print("Found a collision")
#         print(message)
#         print(checksum)
#         print(matches[checksum])
#         exit()
#     else:
#         matches[checksum] = message


# Step 3: Initialise message digest buffer
# ========================================
buffer_size = 48
digest = bytearray([0 for _ in range(buffer_size)])


# Step 4: Process message in 16-byte blocks
# =========================================
n_rounds = 18

for i in range(len(message_bytes) // block_size):
    # Copy block i into the middle section of the array
    # The last section in the array is then filled with front section XOR middle section
    for j in range(block_size):
        digest[block_size + j] = message_bytes[i * block_size + j]
        digest[2 * block_size + j] = digest[block_size + j] ^ digest[j]

    # Rounds of encryption over the entire array. Current byte XOR'd with the previous (substituted) byte.
    previous_hashbyte = 0
    for j in range(n_rounds):
        for k in range(buffer_size):
            digest[k] = previous_hashbyte = digest[k] ^ Sbox[previous_hashbyte]

        previous_hashbyte = (previous_hashbyte + j) % len(Sbox)


# Cameron's Note
# ~~~~~~~~~~~~~~
# This is also known as the compresison function. This type of compression function is known as
# Merkle-Damgard. The nice property about this is that if the compression function f is collision resistant, then so is
# the entire hash function!
#
# The 48 bytes are split up into the following sections
# [digest | message_block_i | digest XOR message_block_i]
# With each section being 16 bytes long.
#
# At the beginning the array will look like this, because the initial values in the digest is 0.
# [0 | message_block_i | message_block_i]
#
# Then the entire array is "encrypted" 18 times. The value of the previous byte is (first substituted using Sbox then)
# XOR'd with the current block. This chaining flows over the entire array.


# Step 5: Output
# ==============
print(binascii.hexlify(digest[:16]).decode('utf-8'))


# Fun Facts!
# MD doesnt (just?) stand for Message Digest, it refers to Merkle-Damgard Construction. A technique
# for building collision resistant one way compression functions.


# Further Reading
# ===============
# https://en.wikipedia.org/wiki/Padding_(cryptography)
# https://en.wikipedia.org/wiki/Merkle%E2%80%93Damg%C3%A5rd_construction
# https://en.wikipedia.org/wiki/MD2_(cryptography)
# https://tools.ietf.org/html/rfc1319
# https://en.wikipedia.org/wiki/One-way_compression_function
# https://www.ssi.gouv.fr/archive/fr/sciences/fichiers/lcr/mu04c.pdf
# https://crypto.stackexchange.com/questions/11935/how-is-the-md2-hash-function-s-table-constructed-from-pi
# http://networkdls.com/Articles/bulletn4.pdf