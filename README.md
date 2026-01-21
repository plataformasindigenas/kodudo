# Kodudo

Kodudo is a Bororo word for "to cook".

A minimal, functional Python tool that cooks your data into documents using Jinja2 templates.

## Installation

```bash
pip install kodudo
```

## Quick Start

```python
import kodudo

# Cook from a config file
kodudo.cook("config.yaml")

# Or programmatically
result = kodudo.render(
    data=[{"name": "Item 1"}, {"name": "Item 2"}],
    template="templates/list.html.j2",
)
```

## Configuration

Define your cooking process in a YAML configuration file:

```yaml
# config.yaml
input: data/records.json       # Path to data (JSON with aptoro metadata or plain list)
template: templates/page.html.j2 # Path to Jinja2 template
output: output/page.html       # Where to write the result
format: html                   # Optional: html, markdown, or text
context:                       # Optional extra variables
  title: "My Documents"
```

## License

GNU General Public License v3 (GPLv3)
