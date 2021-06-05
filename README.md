# PyXtream - A Python Xtream Loader

## Summary

PyXtream loads the xtream IPTV content from a provider server. Groups, Channels, Series are all organized in dictionaries. Season and Episodes are retireved as needed.

## Installing

```shell
pip3 install pyxtream
```

## Example

```python
from pyxtream import XTream
xt = XTream(servername, username, password, url)
if xt.authData != {}:
    xt.load_iptv()
else:
    print("Could not connect")
```

## API

XTream.Groups

XTream.Movies

XTream.Channels

XTream.Series

XTream.getSeriesInfoByID(series_id)
