# wxscan-weights

Prebuilt weights for [wxscan](https://github.com/wilinz/wxscan-rs), and the
scripts that produce them.

Two networks, in two formats:

| File | Network | Format | Size |
|---|---|---|---|
| `models/detect.tflite` | SSD detector, locates candidate symbols | TFLite | 1.0 MB |
| `models/detect.onnx` | same | ONNX | 969 KB |
| `models/sr.tflite` | super resolution, upscales small crops | TFLite | 72 KB |
| `models/sr.onnx` | same | ONNX | 25 KB |

TFLite matches wxscan's default backend; ONNX matches the pure Rust `tract`
backend. The weights are identical, only the container differs.

## Why these are not in a crate

Weights are data, and data on a version-controlled binary is a poor fit for a
package registry: every published version carries another two megabytes that
most callers already have, or do not want because they supply their own. So no
wxscan crate embeds them and none downloads them at build time — a build script
that reaches the network breaks offline builds and docs.rs alike.

Point wxscan at whichever files you want instead:

```rust
let detect = std::fs::read("models/detect.tflite")?;
let sr = std::fs::read("models/sr.tflite")?;
let scanner = wxscan::WeChatQRCode::new(&detect, &sr)?;
```

Verify what you downloaded against `checksums.txt`:

```sh
shasum -a 256 -c checksums.txt
```

## Provenance

Converted, without retraining and without changing any weight, from the Caffe
models WeChatCV publishes at
[opencv_3rdparty](https://github.com/WeChatCV/opencv_3rdparty) (commit
`a8b69ccc738421293254aec5ddb38bd523503252`, the revision
`opencv_contrib/modules/wechat_qrcode/CMakeLists.txt` references).

## Reproducing the conversion

Four Caffe files go in, four weight files come out. Everything runs from
`tools/`, in the order below, because each step consumes what the one before it
produced.

Two of those Python files are not scripts. `caffe2onnx.py` and `caffe2tf.py`
are the converters themselves — one piece of code per Caffe layer, imported and
never executed. `export_onnx.py` and `export_tflite.py` are what you run: each
builds its two graphs through the matching converter, writes the files, and
prints how far the result drifted from the Caffe reference. So the ONNX path is
`export_onnx.py`, and `caffe2onnx.py` is where you look when its number comes
out wrong.

**1. The upstream weights.**

```sh
cd tools
./download_models.sh      # models/{detect,sr}.{caffemodel,prototxt}, MD5 checked
```

**2. The reference tensors.** OpenCV 5 dropped the Caffe importer, so this step
pins 4.x and gets a virtualenv to itself:

```sh
python3 -m venv .venv-ref && .venv-ref/bin/pip install -r requirements-ref.txt
.venv-ref/bin/python ref_dump.py          # writes ref_outputs.npz
```

Do not skip it. Both export scripts load `ref_outputs.npz`, and an export that
was never compared against the Caffe output is a guess.

**3. ONNX** — the lighter of the two paths, pure Python:

```sh
python3 -m venv .venv-onnx && .venv-onnx/bin/pip install -r requirements-onnx.txt
.venv-onnx/bin/python -m grpc_tools.protoc -I. --python_out=. caffe.proto
.venv-onnx/bin/python export_onnx.py      # writes onnx_out/{detect,sr}.onnx
```

The `protoc` line generates `caffe_pb2.py`, which is how both converters read a
`.caffemodel`; it is needed once, not once per path.

**4. TFLite** — the same models, through TensorFlow:

```sh
python3 -m venv .venv-tf && .venv-tf/bin/pip install -r requirements-tf.txt
.venv-tf/bin/python export_tflite.py      # writes tflite_out/{detect,sr}.tflite
```

Both exports print the maximum absolute difference against the reference. It
should land around 1e-6, which is float32 accumulating in a different order.
Anything larger means the graph is not equivalent — not that it is imprecise —
and `check_tf.py` then prints the same comparison layer by layer, to find where
the two graphs part company. Once the numbers hold, copy the files into
`models/` and refresh the checksums:

```sh
cp onnx_out/*.onnx tflite_out/*.tflite ../models/
(cd .. && shasum -a 256 models/* > checksums.txt)
```

`tools/README.md` covers what each converter has to do, and why the TFLite path
is three times the length of the ONNX one for the same two models.

Apache-2.0, as are the upstream models. See `NOTICE`.
