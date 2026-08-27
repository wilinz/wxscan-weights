#!/usr/bin/env python3
"""Rebuild the wxscan weights from the upstream Caffe models.

    ./convert.py all          every step, in order
    ./convert.py onnx         one step
    ./convert.py --list       what the steps are

Each step that needs one gets its own virtualenv, created here the first time
it runs: the OpenCV that still reads Caffe, ONNX and TensorFlow cannot be
installed side by side. Nothing else about the machine is touched.
"""
import argparse, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# step -> (virtualenv it needs, what it does)
STEPS = {
    'download':  (None,   'fetch the four upstream Caffe files into models/'),
    'reference': ('ref',  'run them once under OpenCV 4.x, saving ref_outputs.npz — the answer key'),
    'onnx':      ('onnx', 'rebuild both models as ONNX into onnx_out/, scored against the answer key'),
    'tflite':    ('tf',   'the same as TFLite, into tflite_out/'),
    'install':   (None,   'copy the output into ../models and refresh checksums.txt'),
    'compare-layers': ('tf', 'layer-by-layer diff, for when a step reports a large difference'),
}
ALL = ['download', 'reference', 'onnx', 'tflite', 'install']


def interpreter(env):
    """The python of the .venv-<env> virtualenv, creating and filling it if needed."""
    if env is None:
        return sys.executable
    root = HERE / f'.venv-{env}'
    py = root / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not py.exists():
        print(f'creating {root.name}', flush=True)
        subprocess.check_call([sys.executable, '-m', 'venv', str(root)])
        slow = ' — tensorflow is a large download' if env == 'tf' else ''
        print(f'installing requirements-{env}.txt{slow}', flush=True)
        subprocess.check_call([str(py), '-m', 'pip', 'install', '-q',
                               '--disable-pip-version-check',
                               '-r', str(HERE / f'requirements-{env}.txt')])
    return str(py)


def caffe_pb2(py):
    """converters/caffe_pb2.py, generated from caffe.proto. Both converters read it."""
    if (HERE / 'converters/caffe_pb2.py').exists():
        return
    print('generating converters/caffe_pb2.py', flush=True)
    subprocess.check_call([py, '-m', 'grpc_tools.protoc', '-I', 'converters',
                           '--python_out', 'converters', 'converters/caffe.proto'], cwd=HERE)


def run(step):
    env, what = STEPS[step]
    print(f'\n== {step}: {what}', flush=True)
    py = interpreter(env)
    if step in ('onnx', 'tflite', 'compare-layers'):
        caffe_pb2(py)
    subprocess.check_call([py, '-m', 'steps.' + step.replace('-', '_')], cwd=HERE)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('step', nargs='?', choices=['all'] + list(STEPS), default='all')
    p.add_argument('--list', action='store_true', help='print the steps and exit')
    a = p.parse_args()
    if a.list:
        for s, (env, what) in STEPS.items():
            print(f'  {s:15s} {what}')
        return
    for step in (ALL if a.step == 'all' else [a.step]):
        run(step)


if __name__ == '__main__':
    main()
