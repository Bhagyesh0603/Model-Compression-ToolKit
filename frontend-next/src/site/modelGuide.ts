/**
 * Plain-language copy for the model pages, written for a reader with no machine-learning background.
 * Facts only (what a model is, what a step does). Every measurement still comes from src/data.
 */

export interface ModelIntro {
  /** One sentence: what this model is. */
  what: string;
  /** A second sentence: why it is interesting to compress. */
  why: string;
  /** Short family tag shown as a chip. */
  family: string;
}

export const MODEL_INTRO: Record<string, ModelIntro> = {
  resnet20: {
    family: 'Small · 20 layers',
    what:
      'ResNet-20 is a small image-recognition model: it looks at a photo and says which of ten things is in it. It is built from 20 layers stacked one after another, each one picking out slightly more complex patterns than the last.',
    why: 'It is already small, so it is a hard test: there is little spare room to cut before it starts making mistakes.',
  },
  resnet56: {
    family: 'Medium · 56 layers',
    what:
      'ResNet-56 is the deeper sibling of ResNet-20: the same design, but with 56 layers instead of 20. The extra depth makes it more accurate and about three times bigger.',
    why: 'Deeper models usually carry more spare capacity, so they can lose more of their size for less accuracy.',
  },
  vgg16_bn: {
    family: 'Large · 16 layers, very wide',
    what:
      'VGG-16 is an older, much larger image-recognition model. It has only 16 layers, but each layer is very wide, so it holds far more numbers than the ResNets. "BN" means it uses batch normalization, a standard training aid.',
    why: 'Big, wide models like this are where compression pays off most: most of their width turns out not to be needed for a ten-category task. For this test the photos were enlarged to 224 × 224 pixels, the size VGG-16 was designed for, and accuracy was measured on a sample of the test photos.',
  },
};

export const DATASET_INTRO: Record<string, string> = {
  'CIFAR-10':
    'The models were trained and tested on CIFAR-10, a standard collection of small 32 × 32-pixel colour photos in ten categories: airplane, automobile, bird, cat, deer, dog, frog, horse, ship and truck. Accuracy is always measured on test photos the model never saw while learning.',
};

/** The three things the pipeline does, in order, with an everyday comparison. Keys match stage names. */
export const STEP_GUIDE: { key: string; title: string; plain: string; analogy: string; term: string }[] = [
  {
    key: '1_prune',
    title: 'Cut away the parts it barely uses',
    term: 'Pruning',
    plain:
      'Inside every layer are many small pattern detectors (called channels). Some do almost nothing. We remove the weakest ones, a little at a time, and after each cut we let the model practise again on training photos so it can relearn what was lost.',
    analogy: 'Like editing a long essay: remove the sentences that add nothing, then re-read and smooth the rest.',
  },
  {
    key: '2_recover',
    title: 'Re-tune its internal averages',
    term: 'Recovery (BatchNorm recalibration)',
    plain:
      'The model keeps running averages of what it normally sees inside each layer. After cutting, those averages are out of date. We recompute them from a few hundred photos. This takes seconds and needs no extra training.',
    analogy: 'Like re-zeroing a kitchen scale after you take the bowl off.',
  },
  {
    key: '3_quantize',
    title: 'Store its numbers with less precision',
    term: 'Quantization (FP32 to INT8)',
    plain:
      'A model is millions of numbers. Normally each one is stored with 32 bits of precision. We round every number to 8 bits, which makes the file about four times smaller and lets processors with the right instructions compute much faster.',
    analogy: 'Like rounding prices to whole rupees instead of writing every paisa: slightly less exact, much quicker to add up.',
  },
];

export const GLOSSARY: { term: string; plain: string }[] = [
  { term: 'Model', plain: 'A trained program that turns a photo into an answer ("this is a cat"). It is stored as a file full of numbers it learned.' },
  { term: 'Accuracy (top-1)', plain: 'Out of all the test photos, the share the model labels correctly on its first guess.' },
  { term: 'Accuracy points', plain: 'The plain difference between two accuracies. Going from 93 to 90 percent correct is a drop of 3 points.' },
  { term: 'Parameters', plain: 'The individual numbers the model learned. Fewer parameters means a smaller, cheaper model.' },
  { term: 'Layer / channel', plain: 'A model is a stack of layers. Each layer has many channels, small detectors that each respond to one kind of pattern.' },
  { term: 'Pruning', plain: 'Removing whole channels that contribute little, so the model has fewer parameters to store and compute.' },
  { term: 'Fine-tuning', plain: 'A short extra round of practice on training photos after a cut, so the model can relearn what it lost.' },
  { term: 'Distillation (DKD)', plain: 'During fine-tuning the original model acts as a teacher: the smaller model learns to copy its answers, not just the labels.' },
  { term: 'FP32 / INT8', plain: 'How precisely each number is stored: 32-bit decimals (FP32, the original) or 8-bit whole numbers (INT8, compressed).' },
  { term: 'Latency', plain: 'How long the model takes to answer for one photo, in milliseconds (ms). Lower is faster. It depends heavily on the computer.' },
  { term: 'Median / p95', plain: 'Latency is measured hundreds of times. The median is the typical time; p95 is the slow end (95 out of every 100 runs were faster).' },
  { term: 'Fast INT8', plain: 'Some processors have special instructions for 8-bit maths (Apple M-series, Intel chips with VNNI). Without them, INT8 is not faster.' },
  { term: 'ONNX', plain: 'A standard file format for models that many apps and devices can run. Every number on this site is measured on the exported ONNX file.' },
  { term: 'Test run', plain: 'One complete pass of the pipeline on one computer with one set of settings. The same model can be tested more than once.' },
];

/** "about 93 of every 100" from a 0..1 accuracy. */
export function outOf100(accuracy: number): number {
  return Math.round(accuracy * 100);
}
