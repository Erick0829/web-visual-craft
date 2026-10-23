"""压缩 GLB：重编码内嵌贴图为较小的 JPEG，重建 BIN chunk。

用法: python scripts/optimize-glb.py <输入目录> <输出目录> [max_size] [quality]
"""
import io
import json
import os
import struct
import sys

from PIL import Image


def read_glb(path):
    with open(path, "rb") as fh:
        data = fh.read()
    magic, version, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "not a glb"
    off = 12
    js, bin_chunk = None, b""
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bin_chunk = chunk
        off += 8 + clen
    return js, bin_chunk


def reencode(raw, max_size, quality):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    scale = min(1.0, max_size / max(w, h))
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True, progressive=False)
    return buf.getvalue()


def build(js, bin_chunk, max_size, quality):
    views = js.get("bufferViews", [])
    img_view_ids = {im["bufferView"] for im in js.get("images", []) if "bufferView" in im}

    # 解码所有需要替换的贴图
    new_bytes = {}
    for vid in img_view_ids:
        v = views[vid]
        start = v.get("byteOffset", 0)
        new_bytes[vid] = reencode(bin_chunk[start:start + v["byteLength"]], max_size, quality)

    out = bytearray()
    for i, v in enumerate(views):
        if i in new_bytes:
            payload = new_bytes[i]
            mime_target = "image/jpeg"
        else:
            start = v.get("byteOffset", 0)
            payload = bin_chunk[start:start + v["byteLength"]]
            mime_target = None
        while len(out) % 4:
            out.append(0)
        v["byteOffset"] = len(out)
        v["byteLength"] = len(payload)
        out.extend(payload)
        if mime_target:
            for im in js.get("images", []):
                if im.get("bufferView") == i:
                    im["mimeType"] = mime_target
    while len(out) % 4:
        out.append(0)

    if js.get("buffers"):
        js["buffers"][0]["byteLength"] = len(out)

    json_bytes = json.dumps(js, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4:
        json_bytes += b" "

    total = 12 + 8 + len(json_bytes) + 8 + len(out)
    header = struct.pack("<III", 0x46546C67, 2, total)
    chunk1 = struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes
    chunk2 = struct.pack("<II", len(out), 0x004E4942) + bytes(out)
    return header + chunk1 + chunk2


def main():
    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]
    max_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    quality = int(sys.argv[4]) if len(sys.argv) > 4 else 82
    os.makedirs(dst_dir, exist_ok=True)
    total_in = total_out = 0
    for name in sorted(os.listdir(src_dir)):
        if not name.endswith(".glb"):
            continue
        path = os.path.join(src_dir, name)
        js, bin_chunk = read_glb(path)
        data = build(js, bin_chunk, max_size, quality)
        with open(os.path.join(dst_dir, name), "wb") as fh:
            fh.write(data)
        total_in += os.path.getsize(path)
        total_out += len(data)
        print("%-24s %6.2fMB -> %6.2fMB" % (name, os.path.getsize(path) / 1048576, len(data) / 1048576))
    print("TOTAL %.2fMB -> %.2fMB" % (total_in / 1048576, total_out / 1048576))


if __name__ == "__main__":
    main()
