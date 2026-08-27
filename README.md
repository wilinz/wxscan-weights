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

```sh
cd tools
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./download_models.sh          # fetches the upstream Caffe weights
.venv/bin/python caffe2onnx.py
.venv/bin/python export_onnx.py
.venv/bin/python caffe2tf.py
.venv/bin/python export_tflite.py
```

`ref_dump.py` and `check_tf.py` compare the converted graphs against reference
tensors from the OpenCV Caffe importer, which is what makes the conversion
checkable rather than merely plausible. See `tools/README.md`.

Apache-2.0, as are the upstream models. See `NOTICE`.
