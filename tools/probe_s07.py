"""Capture checked protocol-5 fields from a local vanilla 1.7.10 server."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import socket
import struct
import time
import uuid
import zlib

if __package__:
    from . import probe_s04 as wire
else:
    import probe_s04 as wire


HOST = "127.0.0.1"
PLAYER = "S07Probe"
PING = bytes.fromhex("01 02 03 04 05 06 07 08")
TIMEOUT = 30
MAX_EXPANDED_BYTES = 32 * 1024 * 1024  # Capture tool limit.
POSITION = struct.Struct(">dddffB")
COLUMN = struct.Struct(">iiHH")
# Block IDs, metadata, block light, optionally sky light, then Add and biomes.
SECTION_BYTES = 4096 + 2048 + 2048


def read_fields(body, fmt):
    layout = struct.Struct(fmt)
    return layout.unpack(wire.exact(body, layout.size))


def read_position(body):
    x, y, z, yaw, pitch, on_ground = POSITION.unpack(wire.exact(body, POSITION.size))
    wire.finish(body)
    wire.check(all(map(math.isfinite, (x, y, z, yaw, pitch))), "Nonfinite position")
    wire.check(on_ground in (0, 1), "Invalid on-ground flag")
    return dict(x=x, y=y, z=z, yaw=yaw, pitch=pitch, on_ground=bool(on_ground))


def column_size(primary, add, sky, ground_up):
    wire.check(add & ~primary == 0, "Add bitmap contains absent sections")
    return (primary.bit_count() * (SECTION_BYTES + (2048 if sky else 0))
            + add.bit_count() * 2048 + (256 if ground_up else 0))


def inflate_chunk(compressed, expected):
    wire.check(expected <= MAX_EXPANDED_BYTES, "Chunk data exceeds capture limit")
    decoder = zlib.decompressobj()
    data = decoder.decompress(compressed, expected + 1)
    wire.check(len(data) == expected and decoder.eof and not decoder.unused_data,
               "Chunk zlib stream or expanded length mismatch")
    return data


def read_bulk(body):
    count, compressed_size, sky = read_fields(body, ">hiB")
    wire.check(count > 0 and compressed_size > 0, "Invalid bulk lengths")
    wire.check(sky in (0, 1), "Invalid skylight flag")
    compressed = wire.exact(body, compressed_size)
    columns = [COLUMN.unpack(wire.exact(body, COLUMN.size)) for _ in range(count)]
    wire.finish(body)
    wire.check(len({(x, z) for x, z, _, _ in columns}) == count,
               "Duplicate bulk column coordinates")
    sizes = [column_size(primary, add, sky, True) for _, _, primary, add in columns]
    data = inflate_chunk(compressed, sum(sizes))
    result = []
    offset = 0
    for (x, z, primary, add), size in zip(columns, sizes):
        result.append(dict(x=x, z=z, primary_bitmap=primary, add_bitmap=add,
                           expanded_bytes=size,
                           sha256=hashlib.sha256(data[offset:offset + size]).hexdigest()))
        offset += size
    return dict(columns=result, sky_light=bool(sky), compressed_bytes=compressed_size,
                expanded_bytes=len(data))


def read_chunk(body, sky):
    x, z, ground_up, primary, add, compressed_size = read_fields(body, ">iiBHHi")
    wire.check(ground_up in (0, 1) and compressed_size > 0, "Invalid chunk header")
    compressed = wire.exact(body, compressed_size)
    wire.finish(body)
    # An unload uses ground-up with no sections and an empty inflated payload.
    unload = bool(ground_up and primary == 0)
    size = column_size(primary, add, sky, ground_up and not unload)
    data = inflate_chunk(compressed, size)
    return dict(x=x, z=z, ground_up=bool(ground_up), unload=unload,
                primary_bitmap=primary, add_bitmap=add, compressed_bytes=compressed_size,
                expanded_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def receive_expected(stream, expected, description):
    packet_id, body = wire.receive(stream)
    wire.check(packet_id == expected, f"Expected {description} 0x{expected:02x}")
    return body


def handshake(sock, port, next_state):
    payload = wire.handshake(HOST, port, next_state)
    wire.send(sock, 0, payload)
    return dict(protocol=5, host=HOST, port=port, next_state=next_state,
                frame_hex=wire.frame(0, payload).hex())


def status_exchange(sock, stream, port):
    sent = handshake(sock, port, 1)
    wire.send(sock, 0)
    body = receive_expected(stream, 0, "Status Response")
    status = json.loads(wire.read_string(body))
    wire.finish(body)
    wire.check(status["version"] == {"name": "1.7.10", "protocol": 5},
               "Expected Minecraft 1.7.10 protocol 5")
    players = status["players"]
    wire.check(type(players["online"]) is int and type(players["max"]) is int
               and 0 <= players["online"] <= players["max"], "Invalid player counts")
    wire.send(sock, 1, PING)
    body = receive_expected(stream, 1, "Pong")
    wire.check(wire.exact(body, 8) == PING, "Pong mismatch")
    wire.finish(body)
    return dict(handshake=sent, version=status["version"], online=players["online"],
                max_players=players["max"], pong_hex=PING.hex())


def login_exchange(sock, stream, port):
    sent = handshake(sock, port, 2)
    wire.send(sock, 0, wire.string(PLAYER))
    body = receive_expected(stream, 2, "offline Login Success")
    raw_uuid, player = wire.read_string(body), wire.read_string(body)
    wire.finish(body)
    expected = uuid.UUID(
        bytes=hashlib.md5(f"OfflinePlayer:{PLAYER}".encode(), usedforsecurity=False).digest(),
        version=3,
    )
    wire.check(raw_uuid == str(expected) and player == PLAYER, "Unexpected offline identity")
    body = receive_expected(stream, 1, "Join Game")
    join = wire.join_game(body)
    wire.check(join["dimension"] == 0, "Expected an Overworld reference server")

    position = None
    bulk = None
    single = None
    deadline = time.monotonic() + TIMEOUT
    while position is None or bulk is None:
        remaining = deadline - time.monotonic()
        wire.check(remaining > 0, "Timed out waiting for position and a bulk chunk")
        sock.settimeout(remaining)
        packet_id, body = wire.receive(stream)
        if packet_id == 0x00:
            token = wire.exact(body, 4)
            wire.finish(body)
            wire.send(sock, 0, token)
        elif packet_id == 0x08 and position is None:
            position = read_position(body)
        elif packet_id == 0x21 and single is None:
            single = read_chunk(body, sky=True)
        elif packet_id == 0x26:
            candidate = read_bulk(body)
            wire.check(candidate["sky_light"], "Expected skylight in Overworld bulk")
            wire.check(any(column["primary_bitmap"] for column in candidate["columns"]),
                       "Expected at least one nonempty chunk column")
            bulk = candidate if bulk is None else bulk
        elif packet_id == 0x40:
            raise ValueError("Server disconnected during play")

    return dict(handshake=sent, login_name=PLAYER, offline_uuid_matches=True,
                join_game=join, position=position, chunk_bulk=bulk, chunk_single=single)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=25565, type=int)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    try:
        report = {}
        for key, exchange in (("status", status_exchange), ("login_play", login_exchange)):
            with socket.create_connection((HOST, args.port), timeout=TIMEOUT) as sock:
                with sock.makefile("rb") as stream:
                    report[key] = exchange(sock, stream, args.port)
        with args.report.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2, allow_nan=False)
            output.write("\n")
        print("PASS: protocol 5 status/pong, offline login, position and bulk chunks")
    except (OSError, EOFError, ValueError, LookupError, TypeError, struct.error, zlib.error) as exc:
        parser.exit(1, f"FAIL: {exc}\n")


if __name__ == "__main__":
    main()
