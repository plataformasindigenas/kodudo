# Kodudo Documentation

**Version 0.1.0**

Kodudo ("to cook" in Bororo) is a minimal template rendering tool designed to work seamlessly with [aptoro](https://github.com/plataformasindigenas/aptoro). It takes validated data and "cooks" it into various document formats like HTML, Markdown, and plain text using Jinja2 templates.

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Data Format](#data-format)
6. [Templates](#templates)
7. [API Reference](#api-reference)
8. [License](#license)

---

## Philosophy

Kodudo follows the same core principles as aptoro:

1.  **Functional Core**: Pure functions where possible, immutability where practical.
2.  **Configuration over Code**: Complex rendering pipelines defined in simple YAML files.
3.  **Minimal Dependencies**: Relies only on `jinja2` and `pyyaml`.
4.  **Separation of Concerns**: Data preparation (aptoro) is separate from data presentation (kodudo).

---

## Installation

```bash
pip install kodudo
```

For development:

```bash
pip install kodudo[dev]
```

**Requirements**: Python 3.11+

---

## Quick Start

### 1. The CLI Way

Create a `config.yaml`:

```yaml
input: data.json
template: template.html.j2
output: output.html
context:
  title: "Hello World"
```

Run the command:

```bash
kodudo cook config.yaml
```

### 2. The Python Way

```python
import kodudo

# Cook using a config file
kodudo.cook("config.yaml")

# Cook programmatically
data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
output = kodudo.render(
    data=data,
    template="template.html.j2",
    context={"title": "User List"}
)
```

---

## Configuration

Kodudo is configured via YAML files.

```yaml
# Required
input: path/to/data.json
template: path/to/template.html.j2
output: path/to/output.html

# Optional
format: html  # html, markdown, or text (inferred from template if missing)
template_dirs:
  - shared/templates
  - other/templates
context_file: context.yaml  # Load extra variables from a file
context:                    # Inline extra variables
  site_name: "My Site"
  debug: true
```

---

## Data Format

Kodudo accepts JSON data in two formats:

1.  **Aptoro Format (Recommended)**:
    A JSON object with `meta` and `data` keys. The `meta` contains the schema definition.

    ```json
    {
      "meta": {
        "name": "users",
        "fields": {"name": "str", "age": "int"}
      },
      "data": [
        {"name": "Alice", "age": 30}
      ]
    }
    ```

2.  **Plain List**:
    A simple JSON array of objects.

    ```json
    [
      {"name": "Alice", "age": 30},
      {"name": "Bob", "age": 25}
    ]
    ```

3.  **Generic Wrapper**:
    An object with a known data key like `records`, `items`, `results`.

    ```json
    {
      "results": [ ... ]
    }
    ```

---

## Templates

Kodudo uses [Jinja2](https://jinja.palletsprojects.com/) for templating.

### Available Variables

Your templates have access to the following variables:

-   `data`: The list of data records.
-   `meta`: The metadata dictionary (from aptoro export).
-   `config`: The current configuration values (input, output, format).
-   `...context`: Any variables defined in `context` or `context_file`.

### Example Template

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ meta.description }}</h1>
    <ul>
    {% for item in data %}
        <li>{{ item.name }} ({{ item.age }})</li>
    {% endfor %}
    </ul>
</body>
</html>
```

---

## API Reference

### `kodudo.cook(config_path)`

Reads a configuration file and executes the rendering process.

-   **config_path**: Path to the YAML configuration file.

### `kodudo.render(data, template, *, meta=None, context=None, template_dirs=())`

Renders data to a string using a template.

-   **data**: List of dictionaries or objects.
-   **template**: Path to the template file.
-   **meta**: Optional metadata dictionary.
-   **context**: Optional dictionary of extra variables.
-   **template_dirs**: Tuple of additional directories to search for templates.

---

## License

GNU General Public License v3 (GPLv3)
