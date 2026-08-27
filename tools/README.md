# Model conversion

The upstream models are Caffe. This directory rebuilds them, layer by layer,
in the two formats the Rust backends run: TFLite for `wxscan-tflite`, ONNX for
tract. Neither path retrains or alters a weight; both are checked against the
Caffe output before being copied into `../models/`.

There is no generic Caffe importer here, only the layers these two models use.
That is a deliberate limit: it keeps each converter short enough to read against
the prototxt, which is what makes the "did the conversion change anything"
question answerable.

| File | Role |
|---|---|
| `download_models.sh` | Fetches the four Caffe files at the commit `opencv_contrib` pins, and checks the MD5 |
| `ref_dump.py` | Reference output from OpenCV 4.x's Caffe importer, saved as `ref_outputs.npz` |
| `caffe2tf.py` | The TFLite converter, layer by layer, as a Keras model — a library, not a script |
| `export_tflite.py` | Runs that converter, writes `tflite_out/`, prints the difference against the reference |
| `caffe2onnx.py` | The ONNX converter, building the graph directly — likewise a library |
| `export_onnx.py` | Runs it, writes `onnx_out/`, prints the difference |
| `check_tf.py` | Intermediate-tensor diff against Caffe, on the TF side, for when a whole-model comparison fails |

## Running

The runbook is in the [top-level README](../README.md#reproducing-the-conversion):
fetch the Caffe models, dump the reference tensors under OpenCV 4.x, then run
`export_onnx.py` and `export_tflite.py`, each in its own virtualenv. Three
environments, because the reference and the two conversions want pins that
cannot coexist.

## Why ONNX is the simpler of the two

ONNX is NCHW, like Caffe, and its Conv/ConvTranspose take Caffe's weight
layout, groups, dilation and symmetric padding as they are; MaxPool has a
`ceil_mode` for Caffe's window clipping. So `caffe2onnx.py` is close to a
transcription. The TFLite path has to move every tensor to NHWC, expand
dilation into sparse kernels, and pad explicitly because TF's `same` is
asymmetric at stride 2 — which is why `caffe2tf.py` is three times the length
for the same models.

Two things are left to the Rust side in both formats, as upstream's own
`cv::dnn` graph does them in layers this port implements itself: `PriorBox` and
`DetectionOutput`. The exported graphs end at `mbox_loc` and
`mbox_conf_flatten`.

## Shapes

Height and width stay symbolic. Super resolution runs on crops of whatever size
the pipeline produces, and the detector's input follows the frame. The ONNX
export deliberately skips `shape_inference`: recording every intermediate shape
in terms of the symbols H and W only gives a runtime that pins them to a
concrete size more facts to reconcile, and tract fails to unify them.
