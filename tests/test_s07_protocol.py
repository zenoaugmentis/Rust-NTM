"""Synthetic regression vectors for the S07 play packet decoders."""

import hashlib
import io
import struct
import unittest
import zlib

from tools import probe_s07 as probe


class PlayPacketTests(unittest.TestCase):
    def test_position_uses_absolute_doubles_floats_and_grounded_byte(self):
        payload = bytes.fromhex(
            "bf f8 00 00 00 00 00 00 40 50 00 00 00 00 00 00"
            " 40 00 00 00 00 00 00 00 42 b4 00 00 c1 70 00 00 01"
        )
        self.assertEqual(probe.read_position(io.BytesIO(payload)),
                         dict(x=-1.5, y=64.0, z=2.0, yaw=90.0, pitch=-15.0,
                              on_ground=True))
        for bad in (payload[:-1] + b"\x02", payload + b"\x00",
                    bytes.fromhex("7f f8 00 00 00 00 00 00") + payload[8:]):
            with self.subTest(payload=bad), self.assertRaises(ValueError):
                probe.read_position(io.BytesIO(bad))

    def test_bulk_slices_columns_using_sky_and_add_masks(self):
        # These sizes come from fixed vector layout constants, separate from the decoder.
        first = b"A" * (2 * 10240 + 2048 + 256)
        second = b"B" * (10240 + 256)
        compressed = zlib.compress(first + second)
        header = struct.pack(">hiB", 2, len(compressed), 1)
        columns = struct.pack(">iiHHiiHH", -2, 5, 0x8001, 0x8000, 1, -1, 2, 0)
        report = probe.read_bulk(io.BytesIO(header + compressed + columns))
        self.assertEqual(report["expanded_bytes"], 33280)
        self.assertEqual(report["columns"], [
            dict(x=-2, z=5, primary_bitmap=0x8001, add_bitmap=0x8000,
                 expanded_bytes=22784, sha256=hashlib.sha256(first).hexdigest()),
            dict(x=1, z=-1, primary_bitmap=2, add_bitmap=0, expanded_bytes=10496,
                 sha256=hashlib.sha256(second).hexdigest()),
        ])

    def test_bulk_rejects_invalid_bitmap_and_zlib_boundary(self):
        compressed = zlib.compress(bytes(8448))
        for stream, add in ((compressed, 2), (compressed + b"\0", 0),
                            (compressed[:-1], 0), (zlib.compress(bytes(8449)), 0)):
            with self.subTest(stream=stream, add=add), self.assertRaises(ValueError):
                packet = (struct.pack(">hiB", 1, len(stream), 0) + stream
                          + struct.pack(">iiHH", 0, 0, 1, add))
                probe.read_bulk(io.BytesIO(packet))

    def test_single_partial_and_unload(self):
        for ground_up, primary, data in ((0, 1, bytes(8192)), (1, 0, b"")):
            with self.subTest(ground_up=ground_up, primary=primary):
                compressed = zlib.compress(data)
                packet = struct.pack(">iiBHHi", -1, 2, ground_up, primary, 0,
                                     len(compressed)) + compressed
                report = probe.read_chunk(io.BytesIO(packet), sky=False)
                self.assertEqual(report["expanded_bytes"], len(data))
                self.assertEqual(report["unload"], bool(ground_up))
                self.assertEqual(report["x"], -1)


if __name__ == "__main__":
    unittest.main()
