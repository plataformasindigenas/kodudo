# Roadmap

## Core Philosophy: "Trust but Verify"

Kodudo is designed to be the "viewer" companion to the "model" defined by `aptoro`.

### The Relationship

1.  **Aptoro (The Model)**: Responsible for defining schemas, validating data integrity, and ensuring that data meets strict structural requirements. It produces "trusted" data.
2.  **Kodudo (The View)**: Responsible for taking that *trusted* data and rendering it into human-readable formats (HTML, Markdown, etc.).

### Validation Strategy

*   **Current State**: Kodudo assumes the input data is valid. It loads the `meta` information to make it available to templates, but it does **not** re-validate the data payload against the schema during the rendering process. This keeps rendering fast and simple.
*   **Future Goal**: Implement an optional "verification" step.
    *   **Goal**: Allow users to flag a render process to perform a double-check validation.
    *   **Mechanism**: If `aptoro` is installed, use it to validate the data against the embedded `meta` schema before rendering.
    *   **Fallback**: If `aptoro` is not present, warn the user but proceed with rendering (maintaining the "trust" assumption).

## Future Features

*   **Optional Aptoro Integration**: Add `aptoro` as an optional dependency (`pip install kodudo[validate]`) to enable the verification step described above.
*   **Template Inheritance Paths**: Better support for resolving complex template inheritance chains across multiple directories.
*   **Custom Filters**: Allow users to register custom Jinja2 filters via the configuration file or a Python plugin system.
