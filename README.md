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

You do not need any of this to use the weights — the files in `models/` are
ready to use. This section is for checking that they really are the upstream
models and nothing else.

Everything lives in `tools/`. The scripts you run are numbered, and you run
them in that order. Anything without a number is not meant to be run: the
`converters/` folder holds the code that does the actual translation, and
`debug_compare_layers.py` is only useful when something has gone wrong.

| Script | What it does |
|---|---|
| `1_download_models.sh` | Downloads the four original Caffe files into `models/` and checks their MD5 |
| `2_dump_reference.py` | Runs those originals once and saves the output as `ref_outputs.npz` — the answer key |
| `3_export_onnx.py` | Rebuilds both models as ONNX, writes `onnx_out/`, and prints how far it landed from the answer key |
| `4_export_tflite.py` | The same again, as TFLite, into `tflite_out/` |

Each step gets its own virtualenv. Not for neatness: the answer key needs an
old OpenCV, ONNX needs its own packages and TensorFlow is a world of its own,
and the three cannot be installed together.

```sh
cd tools

# 1. the original Caffe models
./1_download_models.sh

# 2. the answer key. OpenCV 5 can no longer read Caffe, so this step alone
#    pins 4.x.
python3 -m venv .venv-ref && .venv-ref/bin/pip install -r requirements-ref.txt
.venv-ref/bin/python 2_dump_reference.py

# 3. ONNX
python3 -m venv .venv-onnx && .venv-onnx/bin/pip install -r requirements-onnx.txt
.venv-onnx/bin/python -m grpc_tools.protoc -I converters --python_out=converters converters/caffe.proto
.venv-onnx/bin/python 3_export_onnx.py

# 4. TFLite
python3 -m venv .venv-tf && .venv-tf/bin/pip install -r requirements-tf.txt
.venv-tf/bin/python 4_export_tflite.py
```

The `protoc` line writes `converters/caffe_pb2.py`, which is what lets Python
open a `.caffemodel` file at all. Steps 3 and 4 both need it, and it only has
to be generated once.

### What the printed number means

Steps 3 and 4 each end by printing the largest difference between the model
they just built and the answer key from step 2. Around `1e-6` means the two are
the same graph, and the gap is float32 arithmetic happening in a different
order. Much larger than that means the rebuilt graph is genuinely not the same
model — not that it is slightly less accurate — and
`debug_compare_layers.py` prints the same comparison layer by layer, so you can
see where the two stop agreeing.

Once the numbers look right, the new files replace the shipped ones:

```sh
cp onnx_out/*.onnx tflite_out/*.tflite ../models/
(cd .. && shasum -a 256 models/* > checksums.txt)
```

`tools/README.md` goes into what each converter has to do, and why the TFLite
path is three times the length of the ONNX one for the same two models.

Apache-2.0, as are the upstream models. See `NOTICE`.
