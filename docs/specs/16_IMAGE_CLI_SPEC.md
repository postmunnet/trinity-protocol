# Spec 16 — `image-cli` sibling

**Status:** Draft v0.1 (pending review)
**Owner:** yai
**Created:** 2026-05-04
**Decision-rule class:** Tier 6-A clear sibling

## 1. Purpose

Single-purpose image processing CLI — convert / batch / optimize / info.
Generic (NOT WordPress-specific). Designed to compose with `wordpress-cli`
or any other Trinity sibling via TOOL_CONTRACT v1 envelope + audit chain.

Closes the pre-upload gap exposed during wordpress-cli L2 dogfood: operator
shouldn't push 5MB JPEGs through XML-RPC base64 — convert to WebP first,
then upload.

## 2. Architecture invariant

> Sibling = stateless image processor. Reads files from disk, writes
> processed outputs. Emits TOOL_CONTRACT envelope. NO network I/O,
> NO secrets, NO API integration.
>
> Composes with other siblings via filesystem paths or stdin/stdout.

## 3. Layout

```
image-cli/
├── index.js              # entry, --cmd dispatcher, --health flag
├── package.json          # Node 20+, dep: sharp ^0.33
├── README.md
├── TOOL_CONTRACT.json
├── lib/
│   ├── envelope.js       # TOOL_CONTRACT v1 envelope
│   ├── audit.js          # hash-chained ops.ndjson
│   ├── exec.js           # shared verb exec wrapper
│   └── verbs/
│       ├── convert.js    # single-file conversion
│       ├── batch.js      # directory walk + parallel convert
│       ├── info.js       # metadata extract (no mutation)
│       └── optimize.js   # lossless re-encode same format
└── tests/
    ├── test_convert.test.js
    ├── test_batch.test.js
    ├── test_info.test.js
    ├── test_optimize.test.js
    └── fixtures/
        ├── sample.jpg, sample.png, sample.webp
```

Binary path: `<workspace-root>/image-cli/index.js` (Node 20+).

## 4. Dependencies

- `sharp` (^0.33) — Node native (libvips-backed) — single npm dep
  - Trade-off: ~60MB install size for cross-format reliability
  - Alternative considered: shell-out to `cwebp` (lighter but external dep,
    worse cross-format coverage). Sharp picked: deterministic, fast,
    handles JPEG/PNG/WebP/AVIF/TIFF/GIF in one library.

NO other npm deps. NO native system tools required at runtime.

## 5. Verbs

### 5.1 `convert` — single file

```
image-cli --cmd 'convert <input> --to=webp [options]'

Required:
  <input>                  source file path

Options:
  --to=<format>           webp (default) | jpeg | png | avif | jxl
  --q=<n>                  quality 1-100 (default 80 for webp/jpeg, lossless for png)
  --max-w=<n>              max width (proportional resize if exceeded)
  --max-h=<n>              max height (proportional resize if exceeded)
  --strip-exif             remove EXIF/metadata
  --strip-icc              remove ICC color profile
  -o, --out=<path>         output path (default: <input-basename>.<format> in same dir)
  --overwrite              overwrite existing output (default: refuse if exists)
```

### 5.2 `batch` — directory walk

```
image-cli --cmd 'batch <dir> --to=webp [options]'

Required:
  <dir>                    source directory

Options (all from `convert` apply, plus):
  --recursive              walk subdirectories
  --pattern=<glob>         filename pattern (default: *.jpg *.jpeg *.png)
  --out-dir=<path>         output directory (default: same as input, with new ext)
  --parallel=<n>           concurrent conversions (default: CPU count, max 8)
  --dry-run                list files that would be processed, don't convert
  --skip-existing          skip if output already exists (vs --overwrite)
```

### 5.3 `info` — read-only metadata

```
image-cli --cmd 'info <file>'

Returns JSON:
{
  "format": "jpeg",
  "width": 1920,
  "height": 1080,
  "channels": 3,
  "has_alpha": false,
  "size_bytes": 4321567,
  "exif_present": true,
  "icc_present": true,
  "orientation": 1,
  "color_space": "srgb"
}
```

### 5.4 `optimize` — lossless re-encode

```
image-cli --cmd 'optimize <input> [options]'

Re-encodes same format losslessly (zlib level + mozjpeg-style optimization).
Typical reduction: 5-15% size, no quality loss.

Options:
  -o, --out=<path>         output path (default: in-place with .opt suffix)
  --in-place               overwrite original (require explicit flag)
```

## 6. TOOL_CONTRACT v1 envelope

```json
{
  "tool": "image-cli",
  "tool_version": "0.1.0-beta",
  "schema_version": "1.0",
  "command": "convert",
  "action": "image.convert",
  "data": {
    "input": "/path/to/sample.jpg",
    "output": "/path/to/sample.webp",
    "format_in": "jpeg",
    "format_out": "webp",
    "size_in": 4321567,
    "size_out": 287654,
    "ratio": 0.0666,
    "dimensions_in": "1920x1080",
    "dimensions_out": "1920x1080",
    "duration_ms": 234,
    "stripped": ["exif", "icc"]
  },
  "decided_by": "ai" | "human",
  "audit_event_id": "ulid",
  "ts": "<ISO 8601 UTC>"
}
```

For `batch`, `data.results` = array of per-file envelopes (or summary
counts if `--summary` flag).

## 7. Security model

### 7.1 Path safety

- Input/output paths validated against `..` traversal
- Refuse paths in `/`, `/etc/`, `/usr/`, `/System/` (macOS), `~/.ssh/`
- `--in-place` for `optimize` requires explicit flag (not default)
- `--overwrite` similarly explicit

### 7.2 Resource caps

- Max file size: 100 MB (configurable via `--max-file-size=<n>`)
- Max image dimensions: 16384 × 16384 (sharp default; libvips guard)
- Memory: sharp uses streaming where possible; OOM-safe for typical photos

### 7.3 No secrets, no network

By design — sibling does not handle creds, does not make network calls.
Composes with other siblings that do (e.g., wordpress-cli) via filesystem.

## 8. Acceptance criteria

| # | criterion |
|---|-----------|
| A1 | `convert sample.jpg --to=webp` produces sample.webp, size < input |
| A2 | `batch ./photos --to=webp` produces N webp files matching N inputs |
| A3 | `info sample.jpg` returns parseable JSON with format/width/height |
| A4 | `optimize sample.jpg` produces smaller file, format unchanged |
| A5 | `--strip-exif` removes EXIF (verify via `info` after) |
| A6 | `--max-w=1920` produces width <= 1920 (proportional resize) |
| A7 | TOOL_CONTRACT v1 Platinum 14/14 |
| A8 | Registered in `TRINITY_LEGACY/.ai/tools.yaml` with engines.node |
| A9 | `convert` refuses paths with `..` traversal |
| A10 | `batch --dry-run` lists without converting (verify output count = 0) |

## 9. Phased rollout

| Phase | Scope | Effort |
|-------|-------|--------|
| 1 | Scaffold + envelope/audit/exec helpers + tests skeleton | 30 min |
| 2 | `convert` verb (sharp wrapper, format detection, resize, strip) | 90 min |
| 3 | `batch` verb (walk + parallel + pattern filter + dry-run) | 60 min |
| 4 | `info` verb (metadata + JSON output) | 30 min |
| 5 | `optimize` verb (lossless same-format) | 45 min |
| 6 | Platinum 14/14 + register tools.yaml | 30 min |

**Total: ~½ day build.**

## 10. Out of scope (defer)

- AVIF / JXL output formats (sharp supports but not in v0.1 acceptance)
- Watermarking
- Cropping (rectangular crop, smart crop)
- OCR / text extraction
- Vision LLM (alt text, content classification — that's seo-genie-cli's job)
- Server-side image regen plugin integration (WP-specific — wp-cli's job)
- Animated WebP / APNG
- HDR / wide-gamut workflows
- Batch progress streaming via TG bot (could add later via notify-cli pipe)

## 11. Risks

| risk | mitigation |
|------|-----------|
| sharp install size (60 MB) | one-time cost, accept; alternative cwebp shell-out adds external dep complexity |
| sharp version drift across Node versions | pin via package-lock.json; engines.node >= 20 |
| OOM on huge images | resource caps (§7.2) + streaming where sharp allows |
| Output overwrites user data | `--overwrite` and `--in-place` explicit flags only |
| ColorSpace incorrect on output | sharp respects ICC by default; `--strip-icc` is opt-in |
| Path traversal | refuse `..` + sandbox to expanded absolute paths |
| Format detection mistakes | sharp's `metadata()` is authoritative; refuse if format detection fails |

## 12. Composition examples

### A. Pre-upload to WordPress (the immediate use case)
```bash
image-cli --cmd 'batch ./photos --to=webp --q=80 --max-w=1920 --strip-exif --out-dir=/tmp/optimized/'
wordpress-cli --cmd 'media bulk-upload --site=amprohealth --dir=/tmp/optimized/ --decided-by=human'
```

### B. One-off conversion for blog post
```bash
image-cli --cmd 'convert ~/Pictures/screenshot.png --to=webp --q=85 -o /tmp/post-image.webp'
wordpress-cli --cmd 'media upload --site=amprohealth --file=/tmp/post-image.webp --decided-by=human'
```

### C. Audit fleet image sizes
```bash
for site in $(wordpress-cli --cmd 'sites list --json' | jq -r '.[].alias'); do
  wordpress-cli --cmd "media $site list --number=200" \
    | jq -r '.media[].source' \
    | xargs -I{} curl -sI {} \
    | grep Content-Length
done | awk '{sum+=$2} END {print sum/1024/1024 " MB total"}'
```

### D. Static asset prep
```bash
image-cli --cmd 'batch ./hero-images --to=webp --q=85 --max-w=1920'
image-cli --cmd 'batch ./icons --to=webp --q=90 --max-w=512'
```

## 13. Dependencies

- Node 20+ runtime
- `sharp` (^0.33) — single npm dep
- `node:fs`, `node:path`, `node:os` (stdlib)
- `node:sqlite` (stdlib, for audit chain)

NO `wp` binary required. NO `ssh`. NO external system tools.

## 14. Future verbs (defer to v0.2+)

```
crop <file> --rect=x,y,w,h           # rectangular crop
smart-crop <file> --aspect=16:9       # entropy-based crop
watermark <file> --logo=<path>        # overlay
diff <a> <b>                          # perceptual difference (SSIM)
montage <dir>                         # combine into grid
extract-frames <video>                # animated -> stills
```

---

*End of spec 16 v0.1*
