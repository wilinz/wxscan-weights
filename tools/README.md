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
| `convert.py` | The only entry point: creates the virtualenvs and runs the steps below in order |
| `steps/download.py` | Fetches the four Caffe files at the commit `opencv_contrib` pins, and checks their MD5 |
| `steps/reference.py` | Reference output from OpenCV 4.x's Caffe importer, saved as `ref_outputs.npz` |
| `steps/onnx.py` | Builds both ONNX graphs through `converters/caffe_to_onnx.py`, writes `onnx_out/`, prints the difference |
| `steps/tflite.py` | The same through `converters/caffe_to_tf.py`, into `tflite_out/` |
| `steps/install.py` | Copies the output into `../models/` and rewrites `checksums.txt` |
| `steps/compare_layers.py` | Intermediate-tensor diff against Caffe, on the TF side, for when a whole-model comparison fails |
| `converters/caffe_to_onnx.py` | The ONNX translation, layer by layer |
| `converters/caffe_to_tf.py` | The TFLite translation, as a Keras model |
| `converters/caffe.proto` | The Caffe schema; `convert.py` runs `protoc` over it to get `caffe_pb2.py`, which reads a `.caffemodel` |

## Running

`./convert.py all`, or one step at a time — the
[top-level README](../README.md#reproducing-the-conversion) has the details.
The three virtualenvs it creates are not optional: the reference and the two
conversions want pins that cannot coexist.

## Why ONNX is the simpler of the two

ONNX is NCHW, like Caffe, and its Conv/ConvTranspose take Caffe's weight
layout, groups, dilation and symmetric padding as they are; MaxPool has a
`ceil_mode` for Caffe's window clipping. So `caffe_to_onnx.py` is close to a
transcription. The TFLite path has to move every tensor to NHWC, expand
dilation into sparse kernels, and pad explicitly because TF's `same` is
asymmetric at stride 2 — which is why `caffe_to_tf.py` is three times the length
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
