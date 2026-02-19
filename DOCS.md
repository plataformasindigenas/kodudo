# Kodudo Documentation

**Version 0.2.0**

Kodudo ("to cook" in Bororo) renders validated data into documents using Jinja2 templates. Designed as the presentation layer for [aptoro](https://github.com/plataformasindigenas/aptoro).

---

## Architecture

```
config.yaml ──► load_config() ──► BatchConfig
                                      │
                                      ├── .config: Config (frozen dataclass)
                                      └── .outputs: tuple[OutputSpec, ...] | None
                                              │
cook() or cook_from_config() ────────────────►│
                                              ▼
                                    expand_config() ──► list[Config]
                                              │
                                    for each Config:
                                      load data ──► render template ──► write file
                                              │
                                              ▼
                                          list[Path]
```

Key invariant: `Config` is always a single-output frozen dataclass. Multi-output is handled by expanding into multiple `Config` instances before rendering. The renderer and data loader are never touched by expansion logic.

### Module Layout

```
src/kodudo/
├── __init__.py              # Public API: cook(), cook_from_config(), render()
├── __main__.py              # CLI entry point
├── errors.py                # KodudoError, ConfigError, DataError, RenderError
├── config/
│   ├── types.py             # Config frozen dataclass
│   ├── loader.py            # YAML parsing, validation, returns BatchConfig
│   └── expander.py          # OutputSpec, BatchConfig, expand_config(), interpolate_path()
├── data/
│   └── loader.py            # JSON loading, aptoro format support
└── rendering/
    ├── engine.py            # Jinja2 Environment factory
    └── renderer.py          # Template rendering with data/meta/config/context injection
```

---

## Configuration

### Single Output (Basic)

```yaml
input: data.json
template: template.html.j2
output: output.html

# Optional
format: html                    # html | markdown | text (inferred from template if omitted)
template_dirs:
  - shared/templates
context_file: variables.yaml    # External context loaded first
context:                        # Inline context merged on top (wins over context_file)
  site_name: "My Site"
```

Required fields: `input`, `template`, and either `output` or `outputs`.

### Multi-Output

Use `outputs` instead of `output`. Each entry must have `output`; all other fields are optional overrides of the base config.

```yaml
input: data.json
template: page.html.j2
outputs:
  - output: en/index.html
    context: { lang: en }
  - output: pt/index.html
    context: { lang: pt }
```

`output` and `outputs` are **mutually exclusive** — using both raises `ConfigError`.

Each `OutputSpec` can override: `output`, `input`, `template`, `format`, `template_dirs`, `context_file`, `context`. Context is shallow-merged (base config context + spec context, spec wins).

### Per-Record Rendering (foreach)

Renders one output file per data record. The output path supports `{var.field}` interpolation.

```yaml
input: articles.json
template: article.html.j2
output: articles/{article.slug}.html
foreach: article
```

The `foreach` variable name is injected into the template context. In the template above, `{{ article.title }}` accesses the current record's title field.

`foreach` cannot use reserved names: `data`, `meta`, `config`.

### Cartesian Product (outputs x foreach)

`outputs` and `foreach` compose as a Cartesian product:

```yaml
input: articles.json
template: article.html.j2
foreach: article
outputs:
  - output: en/{article.slug}.html
    context: { lang: en }
  - output: pt/{article.slug}.html
    context: { lang: pt }
```

With 169 articles and 2 locales, this produces 338 files from a single config.

### Validation Rules

| Rule | Error |
|------|-------|
| `output` and `outputs` both present | `ConfigError`: mutually exclusive |
| Neither `output` nor `outputs` | `ConfigError`: one is required |
| `outputs` entry missing `output` key | `ConfigError` |
| `foreach` is not a string | `ConfigError` |
| `foreach` uses reserved name | `ConfigError` |
| `format` not in `html`, `markdown`, `text` | `ConfigError` |

---

## Data Format

Kodudo accepts JSON in three formats:

1. **Aptoro format**: `{ "meta": { ... }, "data": [ ... ] }` — `meta` available as template variable
2. **Plain array**: `[ { ... }, { ... } ]`
3. **Generic wrapper**: object with `data`, `records`, `items`, or `results` key containing an array

---

## Templates

Jinja2 templates with autoescape enabled for `.html` and `.xml` extensions.

### Template Variables

| Variable | Type | Source |
|----------|------|--------|
| `data` | `list[dict]` | All records from the JSON input |
| `meta` | `dict` | Schema metadata (empty `{}` if no aptoro metadata) |
| `config` | `dict` | `{"input": str, "output": str, "format": str}` |
| `...context` | any | Flattened into template namespace from context_file + context + foreach |

Context variables are **not** nested under a `context` key — they're injected directly into the template namespace. A context of `{"lang": "en"}` means `{{ lang }}` in the template, not `{{ context.lang }}`.

### Pre-rendered HTML

Autoescape is on by default for HTML templates (`select_autoescape(["html", "xml"])`). For fields containing pre-rendered/trusted HTML (e.g., article bodies already converted from markdown), use Jinja2's built-in `|safe` filter:

```html
<div class="body">{{ article.body|safe }}</div>
```

Do **not** disable autoescape globally. The `|safe` filter is a per-field opt-in that keeps the default secure.

### Format Inference

If `format` is omitted, it's inferred from the template filename stem:
- `*.html.j2` → `html`
- `*.md.j2` → `markdown`
- Everything else → `text`

---

## Python API

### `cook(config_path) -> list[Path]`

Load a config file and render all outputs.

```python
import kodudo

paths = kodudo.cook("config.yaml")
# paths: [Path("en/index.html"), Path("pt/index.html")]
```

### `cook_from_config(config, *, outputs, context, output) -> list[Path]`

Render using a `Config` object with optional runtime overrides. This is the primary API for Python callers who need to vary context or output path at call time.

```python
import kodudo

batch = kodudo.load_config("config/fauna.yaml")

for locale in ("pt", "en"):
    translations = load_translations(locale)
    kodudo.cook_from_config(
        batch.config,
        context={"t": translations, "locale": locale},
        output=f"docs/{locale}/fauna.html",
    )
```

Parameters:
- `config`: `Config` — base configuration (get from `load_config(...).config`)
- `outputs`: `tuple[OutputSpec, ...] | None` — multi-output specs (normally passed internally by `cook()`)
- `context`: `dict[str, Any] | None` — merged on top of config's context (override wins)
- `output`: `str | Path | None` — replaces the config's output path

The `context` override is shallow-merged: `{**config.context, **override_context}`. The original `Config` is not mutated (frozen dataclass; `dataclasses.replace` is used internally).

### `render(data, template, *, meta, context, template_dirs) -> str`

Pure render-to-string. No file I/O. Unaffected by batch/foreach features.

```python
html = kodudo.render(
    data=[{"name": "Alice"}],
    template="templates/users.html.j2",
    context={"title": "Users"},
)
```

### `load_config(path) -> BatchConfig`

Parse and validate a YAML config file.

```python
batch = kodudo.load_config("config.yaml")
batch.config   # Config (frozen dataclass)
batch.outputs  # tuple[OutputSpec, ...] | None
```

### `expand_config(config, outputs, data) -> list[Config]`

Low-level expansion. Turns a base `Config` + optional `outputs` + optional `data` into a list of concrete single-output `Config` instances. Useful if you need to inspect the expansion without rendering.

```python
from kodudo import load_config, expand_config, load_data

batch = load_config("config.yaml")
loaded = load_data(batch.config.resolved_input)
configs = expand_config(batch.config, outputs=batch.outputs, data=loaded.raw)
# configs: list of concrete Config, one per output file
```

### Context Layering

Context is merged in this order (later wins):

1. `context_file` — YAML file loaded into a dict
2. `context` — inline dict from config YAML
3. `cook_from_config(context=...)` — runtime override from Python caller
4. `foreach` variable — injected per-record during expansion

Each layer shallow-merges on top of the previous. This is intentional — one context file per config is sufficient; Python callers who need multiple sources can merge dicts themselves before passing to `cook_from_config(context=...)`.

---

## CLI

```bash
kodudo cook config.yaml                    # Single config
kodudo cook config1.yaml config2.yaml      # Multiple configs
kodudo cook configs/*.yaml                 # Shell glob
```

Each output file is printed to stdout as `Cooked: <path>`. Errors are printed to stderr; processing continues for remaining configs. Exit code is `1` if any config failed, `0` otherwise.

---

## Types Reference

### `Config` (frozen dataclass)

```
Config(
    input: Path,
    template: Path,
    output: Path,
    format: str | None = None,
    template_dirs: tuple[Path, ...] = (),
    context_file: Path | None = None,
    context: dict[str, Any] | None = None,
    base_path: Path | None = None,
    foreach: str | None = None,
)
```

Path resolution: all paths are stored as-is from the config. Use `config.resolved_input`, `config.resolved_template`, `config.resolved_output`, `config.resolved_context_file`, `config.resolved_template_dirs` to get paths resolved relative to `base_path`.

### `BatchConfig` (frozen dataclass)

```
BatchConfig(
    config: Config,
    outputs: tuple[OutputSpec, ...] | None = None,
)
```

### `OutputSpec` (frozen dataclass)

```
OutputSpec(
    output: str,
    input: str | None = None,
    template: str | None = None,
    format: str | None = None,
    template_dirs: tuple[str, ...] | None = None,
    context_file: str | None = None,
    context: dict[str, Any] | None = None,
)
```

### Error Hierarchy

```
KodudoError (base)
├── ConfigError    # Invalid config YAML, missing fields, validation failures
├── DataError      # JSON load/parse failures, invalid data structure
└── RenderError    # Template not found, syntax error, undefined variable
```

---

## Design Decisions

### Why `outputs` instead of extending `output` to accept a list

`Config` remains a single-output frozen dataclass. Multi-output is handled entirely by expansion into multiple `Config` instances. This means the renderer, data loader, and all existing code paths are untouched. The complexity lives in one place (`expander.py`) and is fully testable in isolation.

### Why not `context_files` (plural)

The 3-layer context chain (`context_file` → `context` → `cook_from_config(context=...)`) already covers multi-source context merging. Python callers can load and merge multiple YAML files trivially before passing to `cook_from_config(context=...)`. Adding `context_files` would increase API surface for minimal gain.

### Why not a configurable `autoescape` option

Autoescape is on by default for HTML/XML templates. Disabling it globally is a security risk. The correct pattern for pre-rendered HTML is `{{ field|safe }}` — a per-field opt-in. This is standard Jinja2 and doesn't require kodudo-level configuration.

---

## License

GNU General Public License v3 (GPLv3)
