# Font heap stability

This determinism suite reuses the `font/main` recording. It compares a
test-only payload-padding build with the normal Screenshot Test build and fails
if any raw replay PNG differs. It does not own or publish capture baselines.
