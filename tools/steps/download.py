"""Fetch the upstream Caffe models, at the commit opencv_contrib's CMakeLists references."""
import hashlib, sys, urllib.request
from pathlib import Path

COMMIT = 'a8b69ccc738421293254aec5ddb38bd523503252'
BASE = f'https://raw.githubusercontent.com/WeChatCV/opencv_3rdparty/{COMMIT}/'
# The MD5s recorded in opencv_contrib/modules/wechat_qrcode/CMakeLists.txt
MD5 = {
    'detect.caffemodel': '238e2b2d6f3c18d6c3a30de0c31e23cf',
    'detect.prototxt': '6fb4976b32695f9f5c6305c19f12537d',
    'sr.caffemodel': 'cbfcd60361a73beb8c583eea7e8e6664',
    'sr.prototxt': '69db99927a70df953b471daaba03fbef',
}

def main():
    out = Path(__file__).resolve().parent.parent / 'models'
    out.mkdir(exist_ok=True)
    for name, md5 in MD5.items():
        dst = out / name
        if dst.exists() and hashlib.md5(dst.read_bytes()).hexdigest() == md5:
            print(f'  {name} already here')
            continue
        print(f'  downloading {name}')
        data = urllib.request.urlopen(BASE + name).read()
        got = hashlib.md5(data).hexdigest()
        if got != md5:
            sys.exit(f'{name}: MD5 is {got}, expected {md5}')
        dst.write_bytes(data)

if __name__ == '__main__':
    main()
