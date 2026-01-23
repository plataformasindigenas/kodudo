# Kodudo

[![PyPI version](https://img.shields.io/pypi/v/kodudo.svg)](https://pypi.org/project/kodudo/)
[![Python versions](https://img.shields.io/pypi/pyversions/kodudo.svg)](https://pypi.org/project/kodudo/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Kodudo** is a Bororo word for *"to cook"*.

It is a minimal, functional Python tool that cooks your data into documents using Jinja2 templates. Designed to work seamlessly with [aptoro](https://github.com/plataformasindigenas/aptoro), it separates data preparation from presentation, allowing you to transform validated data into HTML, Markdown, or any other text format.

## Features

- **Data Agnostic:** Works natively with Aptoro exports, plain JSON lists, or generic wrappers.
- **Jinja2 Powered:** Leverage the full power of Jinja2 templates, inheritance, and macros.
- **Configuration over Code:** Define complex rendering pipelines in simple YAML files.
- **Context Aware:** Automatically injects metadata, configuration, and custom context into templates.
- **Multi-Format:** Output to HTML, Markdown, text, or any text-based format.

## Installation

```bash
pip install kodudo
```

## CLI Usage

Kodudo provides a command-line interface for "cooking" documents from configuration files.

```bash
# Cook a single configuration file
kodudo cook config.yaml

# Cook multiple files at once
kodudo cook config1.yaml config2.yaml

# Use shell expansion
kodudo cook configs/*.yaml
```

## Quick Start

```python
import kodudo

# Cook using a config file (same as CLI)
kodudo.cook("config.yaml")

# Or programmatically
data = [
    {"name": "Alice", "role": "Admin"},
    {"name": "Bob", "role": "User"}
]

# Render directly to a string
html = kodudo.render(
    data=data,
    template="templates/users.html.j2",
    context={"title": "User List"}
)
```

## Documentation

For full details on configuration options, template variables, and data formats, see the [Documentation](DOCS.md).

## Configuration

Define your rendering process in a YAML configuration file:

```yaml
# config.yaml
input: data/records.json       # Path to data (JSON with aptoro metadata or plain list)
template: templates/page.html.j2 # Path to Jinja2 template
output: output/page.html       # Where to write the result

# Optional settings
format: html                   # html, markdown, or text (inferred if missing)
context_file: context.yaml     # Load extra variables from a file
context:                       # Inline extra variables
  title: "My Documents"
  author: "Tiago"
```

## Supported Formats

**Input Data (JSON):**
- **Aptoro Format:** `{ "meta": {...}, "data": [...] }`
- **Plain List:** `[ {...}, {...} ]`
- **Generic Wrapper:** `{ "results": [...] }`

**Output:**
- **HTML**
- **Markdown**
- **Text**
- **Any text-based format**

## License

GNU General Public License v3 (GPLv3)
