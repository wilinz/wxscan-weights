"""Copy the verified conversion output into models/ and refresh checksums.txt."""
import hashlib, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def main():
    tools, models = ROOT / 'tools', ROOT / 'models'
    found = sorted(tools.glob('onnx_out/*.onnx')) + sorted(tools.glob('tflite_out/*.tflite'))
    if not found:
        sys.exit('nothing to install: run the onnx and tflite steps first')
    for f in found:
        print(f'  {f.name}')
        shutil.copy2(f, models / f.name)
    lines = [f'{hashlib.sha256(f.read_bytes()).hexdigest()}  models/{f.name}\n'
             for f in sorted(models.iterdir()) if f.is_file()]
    (ROOT / 'checksums.txt').write_text(''.join(lines))
    print(f'  checksums.txt, {len(lines)} files')

if __name__ == '__main__':
    main()
