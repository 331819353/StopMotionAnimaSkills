#!/usr/bin/env python3
"""Validate and render discrete replacement/cutout stop-motion PNG layers.

No interpolation, audio, image generation, network, or input mutation.
Requires Python 3.9+ and Pillow. Timeline contract: references/timeline-format.md.
"""

import argparse
import bisect
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile


class PlanError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PlanError(message)


def exact_keys(obj, keys, label):
    require(isinstance(obj, dict), f'{label}: expected an object')
    expected = set(keys.split())
    missing = expected - obj.keys()
    extra = obj.keys() - expected
    require(not missing and not extra,
            f'{label}: missing {sorted(missing)}, unknown {sorted(extra)}')


def integer(value, label, minimum=None):
    require(type(value) is int, f'{label}: expected integer')
    if minimum is not None:
        require(value >= minimum, f'{label}: must be >= {minimum}')


def number(value, label):
    require(type(value) in (int, float) and math.isfinite(value),
            f'{label}: expected finite number')


def pair(value, label, integers=False):
    require(isinstance(value, list) and len(value) == 2,
            f'{label}: expected two values')
    for item in value:
        if integers:
            integer(item, label, 1)
        else:
            number(item, label)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_plan(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'),
                          object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PlanError(f'cannot read timeline: {exc}') from exc


def load_and_check(path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise PlanError('Pillow is required; select a Python runtime with Pillow') from exc

    plan = read_plan(path)
    exact_keys(plan, 'schema_version canvas fps frame_count assets tracks', 'timeline')
    integer(plan['schema_version'], 'schema_version', 1)
    require(plan['schema_version'] == 1, 'only schema_version 1 is supported')
    exact_keys(plan['canvas'], 'width height background', 'canvas')
    for dim in ('width', 'height'):
        integer(plan['canvas'][dim], f'canvas.{dim}', 1)
    bg = plan['canvas']['background']
    require(isinstance(bg, list) and len(bg) == 4, 'background: expected RGBA array')
    for channel in bg:
        integer(channel, 'background channel', 0)
        require(channel <= 255, 'background channels must be <= 255')
    integer(plan['fps'], 'fps', 1)
    integer(plan['frame_count'], 'frame_count', 1)
    assets = plan['assets']
    require(isinstance(assets, dict) and bool(assets), 'assets: expected nonempty object')
    loaded = {}
    for asset_id, spec in assets.items():
        require(isinstance(asset_id, str) and bool(asset_id), 'asset id must be nonempty')
        label = f'asset {asset_id}'
        exact_keys(spec, 'path expected_size pivot alpha_required', label)
        require(isinstance(spec['path'], str) and bool(spec['path']), f'{label}: invalid path')
        require('://' not in spec['path'], f'{label}: only local PNG paths supported')
        pair(spec['expected_size'], f'{label}.expected_size', integers=True)
        pair(spec['pivot'], f'{label}.pivot')
        require(type(spec['alpha_required']) is bool, f'{label}.alpha_required: expected bool')
        asset_path = Path(spec['path']).expanduser()
        if not asset_path.is_absolute():
            asset_path = path.parent / asset_path
        asset_path = asset_path.resolve()
        require(asset_path.is_file(), f'{label}: missing file {asset_path}')
        try:
            # Hash the exact bytes decoded, so provenance matches the loaded input.
            import io
            data = asset_path.read_bytes()
            with Image.open(io.BytesIO(data)) as source:
                require(source.format == 'PNG', f'{label}: expected PNG file')
                require(not getattr(source, 'is_animated', False),
                        f'{label}: animated PNG not supported; use explicit pose files')
                require(list(source.size) == spec['expected_size'],
                        f'{label}: image size {source.size} differs from expected_size')
                source.load()
                rgba = source.convert('RGBA')
            if spec['alpha_required']:
                require(rgba.getchannel('A').getextrema()[0] < 255,
                        f'{label}: expected genuine transparency, got fully opaque image')
        except PlanError:
            raise
        except Exception as exc:
            raise PlanError(f'{label}: cannot decode image: {exc}') from exc
        loaded[asset_id] = {'image': rgba, 'pivot': spec['pivot'],
                            'path': str(asset_path),
                            'sha256': hashlib.sha256(data).hexdigest()}

    tracks = plan['tracks']
    require(isinstance(tracks, list) and bool(tracks), 'tracks: expected nonempty array')
    ids = set()
    referenced = set()
    for ti, track in enumerate(tracks):
        label = f'track {ti}'
        exact_keys(track, 'id z gap_policy states', label)
        require(isinstance(track['id'], str) and bool(track['id']), f'{label}: invalid id')
        require(track['id'] not in ids, f'duplicate track id {track["id"]}')
        ids.add(track['id'])
        integer(track['z'], f'{label}.z')
        require(track['gap_policy'] == 'invisible', f'{label}: gap_policy must be invisible')
        require(isinstance(track['states'], list) and bool(track['states']),
                f'{label}: states must be a nonempty array')
        previous_end = 0
        for si, state in enumerate(track['states']):
            where = f'{label} state {si}'
            exact_keys(state, 'start end asset x y scale rotation opacity', where)
            integer(state['start'], f'{where}.start', 0)
            integer(state['end'], f'{where}.end', 1)
            require(state['start'] < state['end'] <= plan['frame_count'],
                    f'{where}: invalid interval or exceeds frame_count')
            require(state['start'] >= previous_end,
                    f'{where}: states must be ordered and not overlap')
            previous_end = state['end']
            require(isinstance(state['asset'], str) and state['asset'] in loaded,
                    f'{where}: unknown asset reference')
            referenced.add(state['asset'])
            for field in ('x', 'y', 'scale', 'rotation', 'opacity'):
                number(state[field], f'{where}.{field}')
            require(state['scale'] > 0, f'{where}: scale must be positive')
            require(0 <= state['opacity'] <= 1, f'{where}: opacity must be in [0,1]')
    warnings = [f'unused asset: {key}' for key in sorted(loaded.keys() - referenced)]
    return plan, loaded, warnings


def transformed_layer(asset, state, size):
    from PIL import Image
    image = asset['image']
    angle = math.radians(state['rotation'] % 360)
    cosine = math.cos(angle) / state['scale']
    sine = math.sin(angle) / state['scale']
    pivot_x, pivot_y = asset['pivot']
    x, y = state['x'], state['y']
    # Inverse affine: canvas point -> source; positive rotation is screen CCW.
    affine = (cosine, -sine, pivot_x - cosine*x + sine*y,
              sine, cosine, pivot_y - sine*x - cosine*y)
    resampling = getattr(Image, 'Resampling', Image)
    transform = getattr(Image, 'Transform', Image)
    layer = image.transform(size, transform.AFFINE, affine,
                            resample=resampling.NEAREST, fillcolor=(0, 0, 0, 0))
    if state['opacity'] != 1:
        alpha_lut = [round(value * state['opacity']) for value in range(256)]
        layer.putalpha(layer.getchannel('A').point(alpha_lut))
    return layer


def sample_indices(plan):
    count = plan['frame_count']
    candidates = {0, count - 1}
    if count > 1:
        candidates.update(round(i * (count - 1) / 5) for i in range(6))
    for track in plan['tracks']:
        for state in track['states']:
            for frame in (state['start'] - 1, state['start'], state['end'] - 1, state['end']):
                if 0 <= frame < count:
                    candidates.add(frame)
    indices = sorted(candidates)
    if len(indices) > 12:
        indices = [indices[round(i*(len(indices)-1)/11)] for i in range(12)]
    return indices


def make_contact_sheet(images, path):
    from PIL import Image, ImageDraw
    thumb_width, thumb_height = 256, 160
    columns = min(4, len(images))
    rows = math.ceil(len(images) / columns)
    sheet = Image.new('RGB', (columns * thumb_width, rows * (thumb_height + 24)), 'white')
    draw = ImageDraw.Draw(sheet)
    resampling = getattr(Image, 'Resampling', Image)
    for index, (frame, image) in enumerate(images):
        thumb = image.copy()
        thumb.thumbnail((thumb_width, thumb_height), resampling.NEAREST)
        x = (index % columns) * thumb_width
        y = (index // columns) * (thumb_height + 24)
        background = Image.new('RGBA', thumb.size, (225, 225, 225, 255))
        background.alpha_composite(thumb)
        sheet.paste(background.convert('RGB'), (x, y))
        draw.text((x + 4, y + thumb_height + 4), f'frame {frame}', fill='black')
    sheet.save(path)


def render(plan, loaded, plan_path, plan_hash, out):
    from PIL import Image
    require(not out.exists(), f'output already exists: {out}; choose a new directory')
    # Never put generated files inside a source image path or overwrite the plan.
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f'.{out.name}.tmp-', dir=str(out.parent)))
    try:
        frames_dir = temp / 'frames'
        frames_dir.mkdir()
        size = (plan['canvas']['width'], plan['canvas']['height'])
        tracks = sorted(plan['tracks'], key=lambda track: track['z'])
        starts = [[s['start'] for s in track['states']] for track in tracks]
        cache = {}
        samples = set(sample_indices(plan))
        sample_images = []
        for frame in range(plan['frame_count']):
            canvas = Image.new('RGBA', size, tuple(plan['canvas']['background']))
            for ti, track in enumerate(tracks):
                si = bisect.bisect_right(starts[ti], frame) - 1
                if si < 0:
                    continue
                state = track['states'][si]
                if frame >= state['end']:
                    continue
                if ti not in cache or cache[ti][0] != si:
                    cache[ti] = (si, transformed_layer(loaded[state['asset']], state, size))
                canvas.alpha_composite(cache[ti][1])
            canvas.save(frames_dir / f'frame_{frame:06d}.png')
            if frame in samples:
                sample_images.append((frame, canvas.copy()))
        make_contact_sheet(sample_images, temp / 'contact_sheet.png')
        report = {
            'schema_version': 1,
            'timeline_path': str(plan_path),
            'timeline_sha256': plan_hash,
            'canvas': plan['canvas'], 'fps': plan['fps'],
            'frame_count': plan['frame_count'],
            'duration_seconds': plan['frame_count'] / plan['fps'],
            'frame_pattern': 'frames/frame_%06d.png',
            'contact_frames': sorted(samples),
            'assets': {key: {'path': value['path'], 'sha256': value['sha256']}
                       for key, value in loaded.items()},
            'audio': False, 'video_encoded': False,
            'render_method': 'discrete holds; nearest-neighbor affine RGBA layers',
        }
        (temp / 'render.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                                          encoding='utf-8')
        # Recheck before publish. Do not replace an existing user's result.
        require(not out.exists(), f'output appeared during render: {out}')
        os.rename(temp, out)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'render'))
    parser.add_argument('timeline', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.command == 'render' and args.out is None:
        parser.error('render requires --out')
    if args.command == 'check' and args.out is not None:
        parser.error('--out is only valid for render')
    path = args.timeline.expanduser().resolve()
    try:
        # Capture provenance before validation and reject concurrent plan edits.
        before = path.read_bytes()
        plan, loaded, warnings = load_and_check(path)
        require(path.read_bytes() == before, 'timeline changed during validation; retry')
        if args.command == 'render':
            report = render(plan, loaded, path, hashlib.sha256(before).hexdigest(),
                            args.out.expanduser().resolve())
            result = {'ok': True, 'output': str(args.out.expanduser().resolve()),
                      'frame_count': report['frame_count'], 'warnings': warnings}
        else:
            result = {'ok': True, 'frame_count': plan['frame_count'],
                      'asset_count': len(loaded), 'warnings': warnings}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (PlanError, OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
