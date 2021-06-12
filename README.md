# PyXtream - A Python Xtream Loader

## Summary

PyXtream loads the xtream IPTV content from a provider server. Groups, Channels, Series are all organized in dictionaries. Season and Episodes are retrieved as needed. It includes functions for searching streams and downloading. In this latest version 0.2.0, an optional primitive REST Api allows to search and initiate downloads from a browser.

This library was originally designed to work with Hypnotix at https://github.com/linuxmint/hypnotix

## Installing

Installing pyxtream is done using pip3.

```shell
pip3 install pyxtream
```

Optionally, to use the REST Api service, install also Flask via the following command or manually.

```shell
pip3 install pyxtream[REST_API]
```


## Quick Start

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
xt.getSeriesInfoByID(series_obj)
```

At this point, the series_obj will have both Seasons and Episodes populated.

If you have installed Flask, the REST Api will be turned ON automatically. At this point, there is no method to turn it off. Maybe in a future version.

## API

### Classes:

Below are the classes used in the module. They are heavily influenced by the application Hypnotix.

XTream.Groups

XTream.Channels

XTream.Series

XTream.Season

XTream.Episode

### Dictionaries (Array of dictionaries):

xTream.groups[{},{},...]

xTream.channels[{},{},...]

xTream.series[{},{},...]

xTream.movies[{},{},...]

### Functions:

XTream.getSeriesInfoByID

xTream.search_stream

xTream.download_video

xTream.download_video_impl

xTream.authenticate

xTream.load_iptv

# Change Log

| Date | Version | Description |
| ----------- | -----| ----------- |
| 2021-06-11 | 0.2.1 | Fixed bug in the way it reload from cache |
| 2021-06-08 | 0.2.0 | Added searching and download, Added REST Api, Fixed cache-path issue |
| 2021-06-05 | 0.1.2 | Fixed Server Name |
| 2021-06-04 | 0.1.1 | Updated README.md |
| 2021-06-04 | 0.1.0 | Initial Release |
