import lzma, struct, subprocess, sys, zlib

src = open(sys.argv[1], 'rb').read()
size = struct.unpack_from('>I', src, 12)[0]
pos = src.find(b'\x5d\x00\x00\x00\x02', 64)

raw = bytearray(lzma.decompress(src[pos:pos + size], format=lzma.FORMAT_ALONE))
raw = raw.replace(b'::askfirst:-/bin/login', b'::askfirst:-/bin/sh   ', 1)

payload = subprocess.check_output(['xz', '--format=lzma', '-c', '--lzma1=preset=6,dict=32MiB,lc=3,lp=0,pb=2'], input=raw)
payload = payload[:5] + struct.pack('<Q', len(raw)) + payload[13:]

out = bytearray(src[:pos] + payload)
struct.pack_into('>I', out, 12, len(payload))
struct.pack_into('>I', out, 24, zlib.crc32(payload))
struct.pack_into('>I', out, 4, 0)
struct.pack_into('>I', out, 4, zlib.crc32(out[:64]))

open(sys.argv[2], 'wb').write(out)
