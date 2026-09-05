# Command Chart and Practice title layouts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Command Chart and Practice title boxes.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase.

## Command Chart and Practice title boxes

The Command Chart and Practice command-title rows share the same boxed-fit
logic but not the same container geometry. NUN5 wrapper telemetry at caller
`0x003882D0` establishes these separate records:

- Command Chart titles: X `28`, Y `17/117/217`, width `288`, height `20`;
- Practice titles: X `32`, Y `14/114/214`, width `352`, height `20`;
- Practice explanations remain a separate caller family at X `40`, Y
  `42/142/242`, width `364`, height `48`, vertical alignment `1`.

The long-title right-edge difference was a fit-denominator error rather than a
container offset. NUN5 measures each raw byte-`0x40` quotation delimiter with
the 14-unit `@` metric, then renders the delimiter as a visible quotation mark.
NA2 does not implement that delimiter parser. Measuring a materialized ASCII
quotation mark with its ordinary 9-unit advance therefore does not reproduce
NUN5's two-stage markup semantics.

Move titles may also contain renderer-consumed color controls. Konohamaru's
exact moveset donor is
`<BLACK>Charge! Konohamaru <color0808C0>Ninja Squad<BLACK>!`. The native
renderer consumes `<BLACK>`, `<WHITE>`, `<RED>`, and six-digit
`<colorRRGGBB>` controls without drawing them, so they must not contribute to
the visible-width measurement.

Confidence is **high** for the denominators, caller guards, fit thresholds,
origins, and separation from the Practice explanation family.

- Practice runtime `0x00878A98`, BTL file `0x1C4B98`;
- Command Chart runtime `0x0087A928`, BTL file `0x1C6A28`.
