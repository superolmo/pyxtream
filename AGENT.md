# 🤖 PyXtream Agent Instructions

This document guides an LLM or automated agent in maintaining and extending the `pyxtream` codebase.

## 🎯 Project Core Principles
1.  **Isolation**: The `XTream` class must remain fully stateful at the instance level. Avoid global variables.
2.  **Compatibility**: Primary compatibility must be maintained with **Hypnotix**. Do not change attributes in `Channel`, `Serie`, or `Episode` that are marked with `# Required by Hypnotix`.
3.  **Data Integrity**: Use `pyxtream/schemaValidator.py` for all new provider API interactions.
4.  **Resilience**: Network requests must handle timeouts and connection errors gracefully. Use `_handle_request_exception` and ensure the `_fallback_to_offline` mechanism is preserved.
5.  **Documentation**: API documentation is auto-generated using `pdoc`. Focus on keeping docstrings accurate and concise.

## 📂 Technical Architecture
-   `pyxtream.py`: Contains the core domain logic and data models.
-   `constants.py`: Centralized configuration (timeouts, retry attempts, time thresholds).
-   `rest_api.py`: Implements a multi-threaded Flask wrapper.
-   `api.py`: Centralized URL builder for the Xtream Codes API.
-   `schemaValidator.py`: Wrapper for `jsonschema` validation.

## 🛠️ Development Standards
-   **Type Hinting**: All new functions must include Python type hints.
-   **Logging**: Use `self.printx` for instance-aware logging.
-   **Docstrings**: Use very descriptive **Google-style** docstrings. Include detailed sections for `Args`, `Returns`, and optionally `Raises` or `Notes`. This provides high-quality technical context for both humans and automated agents.
-   **Testing**: 
    -   Unit tests reside in `test/test_pyxtream.py`.
    -   Mocks should be used for all network calls (using `patch('requests.get')`).
    -   Always verify isolation when adding features that modify the internal state.

## 📋 Task Specific Instructions

### Adding a New API Action
1.  Update `pyxtream/api.py` with a new URL builder function.
2.  Add a corresponding method in `XTream` class in `pyxtream.py`.
3.  If the action returns a new data type, define a schema in `schemaValidator.py`.
4.  Expose the action in `pyxtream/rest_api.py` within the `handlers` dictionary.
5.  Regenerate the documentation using the `pdoc` command to ensure the new method is visible.

### Modifying the Web Viewer
-   The Web Viewer is a single-file SPA located at `pyxtream/html/index.html`.
-   It uses Bootstrap 5 and Video.js.
-   Ensure any new API endpoints are reflected in the `API_BASE_URL` logic within the JavaScript section.

## 🚀 Release Process
-   Version is tracked in `pyxtream/version.py`.
-   Follow Semantic Versioning.
-   Update `CHANGELOG.md` and rebuild documentation using `pdoc`.

## ⚠️ Common Pitfalls
-   **Blocking Calls**: The REST API runs in a separate thread, but many `XTream` methods are blocking. Avoid long-running operations that don't update `download_progress`.
-   **Cache Path**: Always validate that `cache_path` is a directory before writing.
-   **Xtream Quirks**: Some providers return `created_live` instead of `live`. The `Channel` constructor handles these normalization steps; maintain this logic.

---
*This file is intended for machine consumption but should be kept human-readable.*