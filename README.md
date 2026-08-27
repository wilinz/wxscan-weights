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

You do not need this to use the weights — the files in `models/` are ready to
use. This is for checking that they really are the upstream models and nothing
else.

```sh
cd tools
./convert.py all
```

That is the whole thing. It downloads the original Caffe models, runs them once
to get an answer key, rebuilds both networks as ONNX and as TFLite, prints how
far each rebuild landed from the answer key, and copies the results into
`models/`. Expect it to take a few minutes the first time, most of it spent
downloading TensorFlow.

It also creates three virtualenvs under `tools/` as it goes, and uses nothing
outside them. Three rather than one because the OpenCV that still reads Caffe,
ONNX and TensorFlow cannot be installed together — a detail you only have to
care about if you go looking for it.

Any single step can be run on its own, and `./convert.py --list` prints them:

| `./convert.py …` | |
|---|---|
| `download` | the four original Caffe files, into `tools/models/` |
| `reference` | runs them once under OpenCV 4.x and saves the output as the answer key |
| `onnx` | rebuilds both networks as ONNX, and scores the result |
| `tflite` | the same as TFLite |
| `install` | copies the output into `models/` and refreshes `checksums.txt` |
| `compare-layers` | see below |

### What the printed score means

`onnx` and `tflite` each end by printing the largest difference between the
network they just built and the answer key. Around `1e-6` means the two are the
same network, and the gap is float32 arithmetic happening in a different order.
Much larger means the rebuild is genuinely not the same network — not that it
is slightly less accurate. `./convert.py compare-layers` then prints the same
comparison layer by layer, so you can see where the two stop agreeing.

The conversion is deterministic: a rebuild on another machine produces files
with the same SHA-256 as the ones committed here.

`tools/README.md` goes into what each converter has to do, and why the TFLite
path is three times the length of the ONNX one for the same two networks.

Apache-2.0, as are the upstream models. See `NOTICE`.
