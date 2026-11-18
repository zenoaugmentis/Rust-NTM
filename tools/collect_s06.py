"""Read-only S06 manifest for trusted, stopped local 1.7.10 worlds.

Uses the repository's S03 scanner/codec. Does not export raw NBT or player data.
Exit: 0 valid nonempty collections, 1 validation error, 2 CLI error.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from check_s03 import inspect_region
from s03_codec import decode


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def collect(label, world):
    result = {'id': label, 'errors': [], 'level': {}, 'dimensions': []}
    if not world.is_dir():
        result['errors'].append('World directory missing')
        return result
    level_path = world / 'level.dat'
    try:
        before = digest(level_path)
        _, root = decode(gzip.decompress(level_path.read_bytes()))
        if root.get('Data', (None,))[0] != 10:
            raise ValueError('Data must be Compound')
        data = root['Data'][1]
        result['level'] = {'sha256': before, 'size': level_path.stat().st_size,
                           'root_tags': sorted(root), 'metadata': {}}
        for key in ('version', 'RandomSeed', 'generatorName', 'generatorVersion', 'generatorOptions', 'MapFeatures'):
            if key in data:
                result['level']['metadata'][key] = {'type': data[key][0], 'value': data[key][1]}
        if data.get('version') != (3, 19133):
            result['errors'].append('Data.version is not Int(19133)')
        if digest(level_path) != before:
            result['errors'].append('level.dat changed while reading')
    except Exception as exc:
        result['errors'].append('level.dat: ' + type(exc).__name__ + ': ' + str(exc))
    for relative in ('region', 'DIM-1/region', 'DIM1/region'):
        directory = world / relative
        files = sorted(directory.glob('r.*.*.mca'))
        dimension = {'directory': relative, 'status': 'ABSENT', 'regions': [], 'pass_chunks': 0}
        if directory.exists() and not files:
            dimension['status'] = 'EMPTY'
        for path in files:
            try:
                report = inspect_region(path)
                if digest(path) != report['sha256']:
                    report['errors'].append('Region changed while reading')
                if report['pass_chunks'] == 0:
                    report['errors'].append('No validated populated chunks')
                dimension['regions'].append(report)
                dimension['pass_chunks'] += report['pass_chunks']
                if report['errors']:
                    result['errors'].append(relative + '/' + path.name + ': validation failed')
            except Exception as exc:
                result['errors'].append(relative + '/' + path.name + ': ' + type(exc).__name__)
        if files:
            dimension['status'] = 'SCANNED'
        result['dimensions'].append(dimension)
    if not result['dimensions'][0]['pass_chunks']:
        result['errors'].append('Overworld has no validated chunks')
    result['other_dimensions'] = sorted(p.name for p in world.glob('DIM*') if p.is_dir() and p.name not in ('DIM-1', 'DIM1'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', action='append', required=True, metavar='ID=PATH')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    worlds = []
    labels = set()
    for entry in args.world:
        label, sep, path = entry.partition('=')
        if not sep or not label or not path or label in labels:
            parser.error('Each --world must have a unique nonempty ID=PATH')
        labels.add(label)
        worlds.append((label, Path(path)))
    for _, world in worlds:
        if args.out.resolve().is_relative_to(world.resolve()):
            parser.error('--out must be outside every source world')
    output = {'schema': 'horizon-s06-v1', 'worlds': [collect(label, path) for label, path in worlds]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=True, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    failed = False
    for world in output['worlds']:
        count = sum(d['pass_chunks'] for d in world['dimensions'])
        failed |= bool(world['errors'])
        print(world['id'] + ': ' + ('FAIL' if world['errors'] else 'PASS') + f', chunks={count}, errors={len(world["errors"])}')
    print('Manifest: ' + str(args.out))
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
