# CompressKit — presentation film

1920 × 1080 • 30 fps • English synthetic narration • burned-in captions

This film explains the implementation in this repository. Diagrams are conceptual; the results scene uses the recorded ResNet-56 / CIFAR-10 experiment from frontend-next/src/data/models.json. Latency belongs to the Intel i5-11320H run, not every target CPU.

## Scene-by-scene script

### 00:00 — Intelligence. With less weight.

An image classifier can carry millions of learned weights. But deployment asks a different question. Can we keep useful intelligence, while using less storage and less time? This is CompressKit.

### 00:12 — How an image becomes a prediction.

A convolutional neural network processes an image through layers. Early filters respond to simple patterns, such as edges. Deeper layers combine these patterns into features. A final classifier produces scores, and the highest score gives the prediction.

### 00:29 — Before changing anything, measure everything.

We load a trained model and preserve an untouched copy. We export the baseline to ONNX and measure accuracy, prediction latency, and file size. Training and calibration data stay separate from the test data used for evaluation.

### 00:44 — Smaller does not always mean faster.

The toolkit checks the CPU for low precision instruction support. Eight bit arithmetic can reduce storage, but speed depends on the hardware and runtime. We use the hardware probe to guide precision, then verify performance with actual timing.

### 01:00 — Remove channels. Reduce real computation.

Structured pruning removes entire feature channels. Unlike simply setting weights to zero, this changes the dimensions of the network. A dependency graph updates connected layers together, preserving compatible shapes, including around residual connections.

### 01:16 — Cut a little. Learn again.

Large cuts can damage accuracy. Gradual pruning alternates smaller cuts with fine tuning. Batch normalization recalibration updates activation statistics using calibration data. It requires forward passes, without gradient based weight training. Recovery can help, but does not guarantee the original accuracy.

### 01:36 — The original model becomes the teacher.

The original model teaches the compressed student. The student learns from correct labels and from the teacher’s output scores. These scores contain relationships between classes. Distillation can recover useful behavior lost during pruning. The teacher is not needed when the student is deployed.

### 01:54 — Fewer bits. A lighter model.

Quantization represents values using fewer bits. Moving from thirty two bit floats to eight bit integers reduces raw weight storage by about four times, for the same number of weights. Calibration determines suitable ranges. Total file reduction varies, and some operations may remain in floating point.

### 02:14 — Practice with rounding error.

When rounding damages accuracy, quantization aware training simulates reduced precision during training. The weights adapt before final quantization. In our pipeline, the final deployment quantization comes after structural changes and training.

### 02:30 — Give it a budget. Let measurements decide.

Automatic mode starts with quantization. If only accuracy fails, it can protect sensitive layers, then try quantization aware training and distillation. If size or latency fails, it explores pruning. Each candidate is measured. The search stops when the requirements are met, if a suitable configuration is found.

### 02:51 — A real trade-off. Measured, not assumed.

In our recorded ResNet fifty six run, model size fell from three point two eight to zero point five three megabytes. Latency improved by two point two five times. Accuracy changed from ninety three point one eight to ninety point five zero percent: a loss of two point six eight percentage points.

### 03:10 — Same task. Less to carry.

The final output is an ONNX model, accompanied by an HTML report and machine readable results. A new image passes through the compressed model to produce a prediction. CompressKit connects established techniques with hardware awareness, automatic decisions, and honest measurement.

## Files

- CompressKit-Presentation.mp4: presentation export.
- render.py: editable frame-by-frame animation and narration script.
- storyboard.json: exact scene timing and caption intervals.
- captions.srt: standalone captions (timing allocated approximately by word count).
- storyboard.jpg: scene overview.

## Re-render

Run `python3 presentation-video/render.py` from the repository root. Requires Pillow, FFmpeg, and the macOS Samantha voice. Existing scene MP4s are cached: remove the relevant scene file after editing. Narration uses cached WAV files; regenerate them when changing the script.

## Presentation note

Use the ResNet-56 figures as one measured example: 6.2× smaller, 2.25× faster, 2.68 percentage points of accuracy loss. The video is an explainer, not a live recording of compression or actual CNN activation tensors.