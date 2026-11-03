"""Two classifiers for "does this image show the outdated persona?".

- baseline.py: cheap rules that look only at filenames and alt text, never at pixels.
- ai_review.py: merges an AI reviewer's per-batch judgments of the actual pictures.

Neither reads the answer key; only evaluate.py at the repo root may do that.
"""
