# PyXtream - A Python Xtream Loader

PyXtream loads the xtream IPTV content from a provider server. Groups, Channels, Series are all organized in dictionaries. Season and Episodes are retrieved as needed. It includes functions for searching streams and downloading.

This library was originally designed to work with Hypnotix at https://github.com/linuxmint/hypnotix

# Installing

Installing pyxtream is done using pip3.

```shell
pip3 install pyxtream
```

Optionally, to use the REST Api service, install also Flask via the following command or manually.

```shell
pip3 install pyxtream[REST_API]
```


# Quick Start

## Your own application

Integrating in your application is simple. Initialization and loading of IPTV channels and groups is done with the following code.

```python
from pyxtream import XTream
xt = XTream(servername, username, password, url)
if xt.authData != {}:
    xt.load_iptv()
else:
    print("Could not connect")
```

Once completed, all the data can be found in xTream.groups, xTream.channels, xTream.movies, xTream.series. Series do not contains the information for all the Seasons and Episodes. Those are loaded separately when needed by calling the following function using a Series object from xTream.series array of dictionaries.

```python
xt.get_series_info_by_id(series_obj)
```

At this point, the series_obj will have both Seasons and Episodes populated.

If you have installed Flask, the REST Api will be turned ON automatically. At this point, there is no method to turn it off. Maybe in a future version.

## Functional Test

Please modify the functional_test.py file with your provider information, then start the application.

```shell
python3 functional_test.py
```

The functional test will allow you to authenticate on startup, load and search streams. If Flask is installed, a simple website will be available at http://localhost:5000 to allow you to search and play streams.

## Interesting Work by somebody else 

- xtreamPOC - https://github.com/sght500/xtreamPOC - Project is a Proof of Concept (POC) that leverages pyxtream, MPV, and NiceGUI to demonstrate the use of Xtream Portal Codes.

So far there is no ready to use Transport Stream library for playing live stream.

- This is the library to convert TS to MP4
  - https://github.com/videojs/mux.js/

- More on above, but same problem. XMLHttpRequest waits until the whole TS file is completely loaded. It does not work for live video streams
  - https://developpaper.com/play-ts-video-directly-on-the-web/

- This below will allow me to process chunks of data
  - https://stackoverflow.com/questions/37402716/handle-xmlhttprequest-response-with-large-data


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
- Increment the MAJOR version when you make incompatible API changes.
- Increment the MINOR version when you add functionality in a backwards-compatible manner.
- Increment the PATCH version when you make backwards-compatible bug fixes.

# Change Log

| Date | Version | Description |
| ----------- | -----| ----------- |
| 2025-02-17 | 0.7.3 | - Added Initial PyTest|
| 2024-09-02 | 0.7.2 | - Added missing request package to setup.py<br>- Refactored the search stream function and now, it can search for a specific stream type<br>- Refactored the download stream function<br>- Refactored the _get_request function and removed the call to the sleep function<br>- Added functional test to get series json output from a series_id<br>- Added functional test to get EPG for a specific stream ID<br>- Added xtream account expiration date printed on the console during authentication<br>- Improved results with the Flask HTML page and differentiating between movies and series<br>- Improved code readability|
| 2024-05-21 | 0.7.1 | - Fixed missing jsonschema package<br>- Fixed provider name in functional_test<br>- Improved print out of connection attempts<br>- Added method to read latest changes in functional_test
| 2023-11-08 | 0.7.0 | - Added Schema Validator<br>- Added Channel Age<br>- Added list of movies added in the last 30 and 7 days<br>- Updated code based on PyLint<br>- Fixed Flask package to be optional [richard-de-vos](https://github.com/richard-de-vos)|
| 2023-02-06 | 0.6.0 | - Added methods to change connection header, to turn off reload timer, and to enable/disable Flask debug mode<br>- Added a loop when attempting to connect to the provider <br>- Cleaned up some print lines|
| 2021-08-19 | 0.5.0 | - Added method to gracefully handle connection errors<br>- Added setting to not load adult content<br>- Added sorting by stream name<br>- Changed the handling of special characters in streams<br>- Changed print formatting<br>- Changed index.html webpage to HTML5 and Bootstrap 5|
| 2021-06-19 | 0.4.0 | - Updated to follow PEP8<br>- Updated Docstrings |
| 2021-06-19 | 0.3.0 | - Added enhanced Home Page with Search Button and Player<br>- Added case insensitive search<br>- Improved handling of provider missing fields |
| 2021-06-11 | 0.2.1 | - Fixed bug in the way it reload from cache |
| 2021-06-08 | 0.2.0 | - Added searching<br>- Added video download<br>- Added REST Api<br>- Fixed cache-path issue |
| 2021-06-05 | 0.1.2 | - Fixed Server Name |
| 2021-06-04 | 0.1.1 | - Updated README.md |
| 2021-06-04 | 0.1.0 | - Initial Release |
