# Font hypotheses

## Selective palette refinement

**Status:** unresolved static hypothesis; no palette bytes or raster indices
have been changed or runtime-tested.

Clean NA2's primary GF4 raster and the accepted secondary raster both use
palette indices 13 and 14 zero times. Those two GF4C entries may therefore be
candidates for exact NUN5 white-alpha levels without changing any currently
referenced primary pixel. This is the next bounded asset hypothesis only if a
matched review still finds a halfwidth-Latin weight difference.

Any experiment must start from the accepted native package and remain a
small, call-local or asset-local, script-generated change. A full NUN5 text
renderer transplant remains outside this hypothesis.
