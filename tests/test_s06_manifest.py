import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import anvil_1710 as a
from collect_s06 import collect
from s03_codec import encode


class ManifestTests(unittest.TestCase):
    def make_world(self, directory):
        world = Path(directory) / 'world'
        (world / 'region').mkdir(parents=True)
        (world / 'level.dat').write_bytes(gzip.compress(encode('', {'Data': (10, {'version': (3, 19133), 'RandomSeed': (4, 123), 'Player': (10, {'private': (8, 'SECRET')})})})))
        (world / 'region' / 'r.0.-1.mca').write_bytes(a.write_region({a.chunk_index(*a.FIXTURE_POS): a.ChunkBlob(a.ZLIB, a.fixture_nbt())}))
        return world

    def test_stability_and_no_player_export(self):
        with tempfile.TemporaryDirectory() as d:
            world = self.make_world(d)
            before = {p: p.read_bytes() for p in world.rglob('*') if p.is_file()}
            first = collect('test', world)
            self.assertEqual(first, collect('test', world))
            self.assertEqual(first['errors'], [])
            self.assertEqual(first['dimensions'][0]['pass_chunks'], 1)
            self.assertNotIn('SECRET', json.dumps(first))
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_missing_and_corrupt(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(collect('missing', Path(d) / 'missing')['errors'])
            world = self.make_world(d)
            (world / 'region' / 'r.0.-1.mca').write_bytes(b'bad')
            self.assertTrue(collect('broken', world)['errors'])

    def test_cli_failure_and_output_guard(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'collect_s06.py'
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'report.json'
            run = subprocess.run([sys.executable, str(script), '--world', 'missing=' + str(Path(d) / 'missing'), '--out', str(out)], capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertTrue(out.is_file())
            world = self.make_world(d)
            run = subprocess.run([sys.executable, str(script), '--world', 'test=' + str(world), '--out', str(world / 'forbidden.json')], capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertFalse((world / 'forbidden.json').exists())


if __name__ == '__main__':
    unittest.main()
