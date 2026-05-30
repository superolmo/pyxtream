# 📺 PyXtream

[![PyPI version](https://img.shields.io/pypi/v/pyxtream.svg)](https://pypi.org/project/pyxtream/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**PyXtream** is a high-performance, asynchronous-friendly Python library designed to interface with Xtream Codes IPTV panels. It handles authentication, data ingestion, caching, and stream management with a focus on precision and reliability.

Originally engineered to power [Hypnotix](https://github.com/linuxmint/hypnotix), PyXtream is optimized for applications requiring structured access to Live TV, VOD, and Series content.

---

## ✨ Key Features

-   **🚀 Industrial Grade Ingestion**: Efficiently loads thousands of channels and groups into structured Python objects.
-   **🔒 Full Instance Isolation**: Built for multi-provider environments. Every instance maintains its own groups, channels, and state without global side effects.
-   **📁 Smart Caching**: Integrated file-based caching with configurable TTL (Time-to-Live) to reduce provider server load and startup times.
-   **🛡️ Schema Validation**: Uses `jsonschema` to validate provider responses, ensuring data integrity against non-standard API implementations.
-   **🔍 Advanced Search**: Regex-powered searching across Live, VOD, and Series collections.
-   **📥 Stream Downloader**: Robust video downloading with built-in **resume support** (HTTP Range headers).
-   **🌐 REST API & Web UI**: Optional Flask-based microservice and a modern Bootstrap 5 viewer included.
-   **📅 EPG Support**: Full access to XMLTV data and short-term EPG for live channels.

---

## 📦 Installation

Install the core library:

```shell
pip install pyxtream
```

Optionally, to use the REST Api service, install also Flask via the following command or manually.

```shell
pip install pyxtream[REST_API]
```


# Quick Start

## Your own application

Integrating in your application is simple. Initialization and loading of IPTV channels and groups is done with the following code.

```python
from pyxtream import XTream
xt = XTream(servername, username, password, url)
if xt.auth_data != {}:
    xt.load_iptv()
else:
    print("Could not connect")
```

Once completed, all the data can be found in `xTream.groups`, `xTream.channels`, `xTream.movies`, `xTream.series`. Series do not contains the information for all the Seasons and Episodes. Those are loaded separately when needed by calling the following function using a Series object from `xTream.series` array of dictionaries.

```python
xt.get_series_info_by_id(series_obj)
```

At this point, the `series_obj` will have both Seasons and Episodes populated.

## Functional Test

To run the functional test, you can create a `.env` file in the project root with your provider credentials:

```env
PROVIDER_NAME="My Provider"
PROVIDER_URL="http://example.com:8080"
PROVIDER_USERNAME="your_username"
PROVIDER_PASSWORD="your_password"
```
Alternatively, you can modify the variables directly in `functional_test.py`. Start the application with:

```shell
python3 functional_test.py
```

The functional test will allow you to authenticate on startup, load and search streams. If Flask is installed, a simple website will be available at http://localhost:5000 to allow you to search and play streams.

## 🧪 Testing

To run unit tests and generate an interactive HTML coverage report:

```shell
python3 -m pytest --cov=pyxtream --cov-report=html test/test_pyxtream.py
```

The report will be generated in the `htmlcov/` directory. Open `htmlcov/index.html` in your web browser to view the detailed results.

## Applications using PyXtream

Applications using PyXtream PYPI package

- xtreamPOC - https://github.com/sght500/xtreamPOC - Project is a Proof of Concept (POC) that leverages pyxtream, MPV, and NiceGUI to demonstrate the use of Xtream Portal Codes.

Applications using PyXtream files

- Hypnotix - https://github.com/linuxmint/hypnotix - Hypnotix is an IPTV streaming application with support for live TV, movies and series.

# API

## Classes:

Below are the classes used in the module. They are heavily influenced by the application Hypnotix.

- XTream.Channels
- XTream.Groups
- XTream.Episode
- XTream.Series
- XTream.Season

## Dictionaries (Array of dictionaries):

xTream.groups[{},{},...]

xTream.channels[{},{},...]

xTream.series[{},{},...]

xTream.movies[{},{},...]

## Functions:

- xTream.authenticate()
- xTream.load_iptv()
- XTream.get_series_info_by_id(get_series: dict)
- xTream.search_stream(keyword: str, ignore_case: bool = True, return_type: str = "LIST")
- xTream.download_video(stream_id: int)
- xTream.vodInfoByID(vod_id)
- xTream.liveEpgByStream(stream_id)
- xTream.liveEpgByStreamAndLimit(stream_id, limit)
- xTream.allLiveEpgByStream(stream_id)
- xTream.allEpg()

# Versioning
Follows the Semantic Versioning from https://semver.org/
- Increment the MAJOR version when you make incompatible API changes.
- Increment the MINOR version when you add functionality in a backwards-compatible manner.
- Increment the PATCH version when you make backwards-compatible bug fixes.

Detailed history of changes can be found in the [CHANGELOG.md](CHANGELOG.md) file.

## Interesting content that could be used for future development

So far there is no ready to use Transport Stream library for playing live stream.

- This is the library to convert TS to MP4
  - https://github.com/videojs/mux.js/

- More on above, but same problem. XMLHttpRequest waits until the whole TS file is completely loaded. It does not work for live video streams
  - https://developpaper.com/play-ts-video-directly-on-the-web/

- This below will allow me to process chunks of data
  - https://stackoverflow.com/questions/37402716/handle-xmlhttprequest-response-with-large-data
