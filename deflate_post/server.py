import zlib
from flask import Flask, request, send_file


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return send_file('index.html')


@app.route('/', methods=['POST'])
def upload():
    return inflate(request.data)


def deflate(data, compresslevel=9):
    compress = zlib.compressobj(
        compresslevel,        # level: 0-9
        zlib.DEFLATED,        # method: must be DEFLATED
        -zlib.MAX_WBITS,      # window size in bits:
                              #   -15..-8: negate, suppress header
                              #   8..15: normal
                              #   16..30: subtract 16, gzip header
        zlib.DEF_MEM_LEVEL,   # mem level: 1..8/9
        0                     # strategy:
                              #   0 = Z_DEFAULT_STRATEGY
                              #   1 = Z_FILTERED
                              #   2 = Z_HUFFMAN_ONLY
                              #   3 = Z_RLE
                              #   4 = Z_FIXED
    )
    deflated = compress.compress(data)
    deflated += compress.flush()
    return deflated


def inflate(data):
    decompress = zlib.decompressobj(
        -zlib.MAX_WBITS  # see above
    )
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated


if '__main__' == __name__:
    app.run(debug=True)
