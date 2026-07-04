# Hypotheses Archive

Use this file for old patch candidates, failed experiments, unverified addresses, and leads that should not clutter active PNACH/build files.

## ETC Text Budget Tests

### Collection quit prompt padding

Status: active test, pending in-game check.

- File: `PRG/ETC.BIN`
- Offset: `0x24F50`
- Previous polished text: `Ｑｕｉｔ？`
- Test text: `Quit Collection Menu?`
- Reason: this slot is null-terminated and has zero padding through `0x24F97`, before the next visible string begins at `0x24F98`.
- Backups:
  - `work/text_polish/etc_bin/backups/ETC.BIN.loose.20260704-155734.bak`
  - `work/text_polish/etc_bin/backups/ETC.BIN.iso.20260704-155734.bak`


## PNACH Candidates

### Disable RPS (old)

Status: archived, replaced by current `[Disable RPS]` section in `cheats/C0659AD1.pnach`.

```ini
// [Disable RPS (old)]
// author=solid1353
// patch=1,EE,202457C8,extended,1000007A
```

### Disable extra hit (old)

Status: archived, replaced by current `[Disable extra hit with aura punishment]` section in `cheats/C0659AD1.pnach`.

```ini
// [Disable extra hit (old)]
// author=solid1353
// patch=1,EE,20241F40,extended,100000AA
```
