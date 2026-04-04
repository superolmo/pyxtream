#!/usr/bin/python3
"""
pyxtream

Module handles downloading xtream data.

Part of this content comes from
- https://github.com/chazlarson/py-xtream-codes/blob/master/xtream.py
- https://github.com/linuxmint/hypnotix

> _Author_: Claudio Olmi
> _Github_: superolmo


> _Note_: It does not support M3U
"""

import json
# used for URL validation
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from os import makedirs
from os import path as osp
# Timing xtream json downloads
from timeit import default_timer as timer
from typing import Optional, Tuple

import requests

from pyxtream import api
from pyxtream.schemaValidator import SchemaType, schemaValidator

try:
    from pyxtream.rest_api import FlaskWrap
    USE_FLASK = True
except ImportError:
    USE_FLASK = False

SSL_FIRST = True


class Channel:
    # Required by Hypnotix
    info = ""
    id = ""
    name = ""  # What is the difference between the below name and title?
    logo = ""
    logo_path = ""
    group_title = ""
    title = ""
    url = ""

    # XTream
    stream_type: str = ""
    group_id: str = ""
    is_adult: int = 0
    added: int = 0
    epg_channel_id: str = ""
    age_days_from_added: int = 0
    date_now: datetime

    # This contains the raw JSON data
    raw: dict = {}

    def __init__(self, xtream: object, group_title, stream_info):
        self.date_now = datetime.now(timezone.utc)

        stream_type = stream_info["stream_type"]
        # Adjust the odd "created_live" type
        if stream_type in ("created_live", "radio_streams"):
            stream_type = "live"

        if stream_type not in ("live", "movie"):
            print(f"Error the channel has unknown stream type "
                  f"`{stream_type}`\n`{stream_info}`")
        else:
            # Raw JSON Channel
            self.raw = stream_info

            stream_name = stream_info["name"]

            # Required by Hypnotix
            self.id = stream_info["stream_id"]
            self.name = stream_name
            self.logo = stream_info["stream_icon"]
            self.logo_path = xtream._get_logo_local_path(self.logo)
            self.group_title = group_title
            self.title = stream_name

            # Check if category_id key is available
            if "category_id" in stream_info.keys():
                self.group_id = int(stream_info["category_id"])

            stream_extension = ""

            if stream_type == "live":
                stream_extension = "ts"

                # Check if epg_channel_id key is available
                if "epg_channel_id" in stream_info.keys():
                    self.epg_channel_id = stream_info["epg_channel_id"]

            elif stream_type == "movie":
                stream_extension = stream_info["container_extension"]

            # Default to 0
            self.is_adult = 0
            # Check if is_adult key is available
            if "is_adult" in stream_info.keys():
                self.is_adult = int(stream_info["is_adult"])

            self.added = int(stream_info["added"])
            self.age_days_from_added = abs(
                datetime.fromtimestamp(self.added, timezone.utc) - self.date_now
                ).days

            # Required by Hypnotix
            self.url = f"{xtream.server}/{stream_type}/{xtream.authorization['username']}/" \
                       f"{xtream.authorization['password']}/{stream_info['stream_id']}.{stream_extension}"

            # Check that the constructed URL is valid
            if not xtream._validate_url(self.url):
                print(f"{self.name} - Bad URL? `{self.url}`")

    def export_json(self):
        jsondata = {}

        jsondata["url"] = self.url
        jsondata.update(self.raw)
        jsondata["logo_path"] = self.logo_path

        return jsondata


class Group:
    # Required by Hypnotix
    name = ""
    group_type = ""

    # XTream
    group_id = ""

    # This contains the raw JSON data
    raw: dict = {}

    def convert_region_shortname_to_fullname(self, shortname):

        if shortname == "AR":
            return "Arab"
        if shortname == "AM":
            return "America"
        if shortname == "AS":
            return "Asia"
        if shortname == "AF":
            return "Africa"
        if shortname == "EU":
            return "Europe"

        return ""

    def __init__(self, group_info: dict, stream_type: str):
        # Raw JSON Group
        self.raw = group_info

        self.channels = []
        self.series = []

        TV_GROUP, MOVIES_GROUP, SERIES_GROUP = range(3)

        if "VOD" == stream_type:
            self.group_type = MOVIES_GROUP
        elif "Series" == stream_type:
            self.group_type = SERIES_GROUP
        elif "Live" == stream_type:
            self.group_type = TV_GROUP
        else:
            print(f"Unrecognized stream type "
                  f"`{stream_type}` for `{group_info}`")

        self.name = group_info["category_name"]
        split_name = self.name.split('|')
        self.region_shortname = ""
        self.region_longname = ""
        if len(split_name) > 1:
            self.region_shortname = split_name[0].strip()
            self.region_longname = self.convert_region_shortname_to_fullname(self.region_shortname)

        # Check if category_id key is available
        if "category_id" in group_info.keys():
            self.group_id = int(group_info["category_id"])


class Episode:
    # Required by Hypnotix
    title = ""
    name = ""
    info = ""

    # XTream

    # This contains the raw JSON data
    raw: dict = {}

    def __init__(self, xtream: object, series_info, group_title, episode_info) -> None:
        # Raw JSON Episode
        self.raw = episode_info

        self.title = episode_info["title"]
        self.name = self.title
        self.group_title = group_title
        self.id = episode_info["id"]
        self.container_extension = episode_info["container_extension"]
        self.episode_number = episode_info["episode_num"]
        self.av_info = episode_info["info"]

        self.logo = series_info["cover"]
        self.logo_path = xtream._get_logo_local_path(self.logo)

        self.url = f"{xtream.server}/series/" \
                   f"{xtream.authorization['username']}/" \
                   f"{xtream.authorization['password']}/{self.id}.{self.container_extension}"

        # Check that the constructed URL is valid
        if not xtream._validate_url(self.url):
            print(f"{self.name} - Bad URL? `{self.url}`")


class Serie:
    # Required by Hypnotix
    name = ""
    logo = ""
    logo_path = ""

    # XTream
    series_id = ""
    plot = ""
    youtube_trailer = ""
    genre = ""

    # This contains the raw JSON data
    raw: dict = {}

    def __init__(self, xtream: object, series_info):

        series_info["added"] = series_info["last_modified"]

        # Raw JSON Series
        self.raw = series_info
        self.xtream = xtream

        # Required by Hypnotix
        self.name = series_info["name"]
        self.logo = series_info["cover"]
        self.logo_path = xtream._get_logo_local_path(self.logo)

        self.seasons = {}
        self.episodes = {}

        # Check if category_id key is available
        if "series_id" in series_info.keys():
            self.series_id = int(series_info["series_id"])

        # Check if plot key is available
        if "plot" in series_info.keys():
            self.plot = series_info["plot"]

        # Check if youtube_trailer key is available
        if "youtube_trailer" in series_info.keys():
            self.youtube_trailer = series_info["youtube_trailer"]

        # Check if genre key is available
        if "genre" in series_info.keys():
            self.genre = series_info["genre"]

        self.url = f"{xtream.server}/series/" \
                   f"{xtream.authorization['username']}/" \
                   f"{xtream.authorization['password']}/{self.series_id}/"

    def export_json(self):
        jsondata = {}

        jsondata.update(self.raw)
        jsondata['logo_path'] = self.logo_path

        return jsondata


class Season:
    # Required by Hypnotix
    name = ""

    def __init__(self, name):
        self.name = name
        self.episodes = {}


class XTream:

    name = ""
    server = ""
    secure_server = ""
    username = ""
    password = ""
    base_url = ""
    base_url_ssl = ""

    cache_path = ""

    account_expiration: timedelta

    live_type = "Live"
    vod_type = "VOD"
    series_type = "Series"

    hide_adult_content = False

    live_catch_all_group = Group(
        {"category_id": "9999", "category_name": "xEverythingElse", "parent_id": 0}, live_type
    )
    vod_catch_all_group = Group(
        {"category_id": "9999", "category_name": "xEverythingElse", "parent_id": 0}, vod_type
    )
    series_catch_all_group = Group(
        {"category_id": "9999", "category_name": "xEverythingElse", "parent_id": 0}, series_type
    )
    # If the cached JSON file is older than threshold_time_sec then load a new
    # JSON dictionary from the provider
    threshold_time_sec = -1

    validate_json: bool = True

    def __init__(
        self,
        provider_name: str,
        provider_username: str,
        provider_password: str,
        provider_url: str,
        headers: dict = None,
        hide_adult_content: bool = False,
        cache_path: str = "",
        reload_time_sec: int = 60*60*8,
        validate_json: bool = False,
        enable_flask: bool = False,
        debug_flask: bool = True,
        flask_port: int = 5000
            ):
        """Initialize Xtream Class

        Args:
            provider_name     (str):            Name of the IPTV provider
            provider_username (str):            User name of the IPTV provider
            provider_password (str):            Password of the IPTV provider
            provider_url      (str):            URL of the IPTV provider
            headers           (dict):           Requests Headers
            hide_adult_content(bool, optional): When `True` hide stream that are marked for adult
            cache_path        (str, optional):  Location where to save loaded files.
                                                Defaults to empty string.
            reload_time_sec   (int, optional):  Number of seconds before automatic reloading
                                                (-1 to turn it OFF)
            validate_json     (bool, optional): Check Xtream API provided JSON for validity
            enable_flask      (bool, optional): Enable Flask
            debug_flask       (bool, optional): Enable the debug mode in Flask
            flask_port        (int, optional):  Flask Port Number

        Returns: XTream Class Instance

        - Note 1: If it fails to authorize with provided username and password,
                auth_data will be an empty dictionary.
        - Note 2: The JSON validation option will take considerable amount of time and it should be
                    used only as a debug tool. The Xtream API JSON from the provider passes through a
                    schema that represent the best available understanding of how the Xtream API
                    works.
        """
        self.server = provider_url
        self.username = provider_username
        self.password = provider_password
        self.name = provider_name
        self.cache_path = cache_path
        self.hide_adult_content = hide_adult_content
        self.threshold_time_sec = reload_time_sec
        self.validate_json = validate_json

        self.auth_data = {}
        self.authorization = {'username': '', 'password': ''}

        self.groups = []
        self.channels = []
        self.series = []
        self.movies = []
        self.movies_30days = []
        self.movies_7days = []

        self.connection_headers = {}

        self.state = {'authenticated': False, 'loaded': False}

        # Used by REST API to get download progress
        self.download_progress: dict = {'StreamId': 0, 'Total': 0, 'Progress': 0}

        # get the pyxtream local path
        self.app_fullpath = osp.dirname(osp.realpath(__file__))

        # prepare location of local html template
        self.html_template_folder = osp.join(self.app_fullpath, "html")

        # if the cache_path is specified, test that it is a directory
        if self.cache_path != "":
            # If the cache_path is not a directory, clear it
            if not osp.isdir(self.cache_path):
                self.printx(" - Cache Path is not a directory, using default '~/.xtream-cache/'")
                self.cache_path = ""

        # If the cache_path is still empty, use default
        if self.cache_path == "":
            self.cache_path = osp.expanduser("~/.xtream-cache/")
            if not osp.isdir(self.cache_path):
                makedirs(self.cache_path, exist_ok=True)
            self.printx(f"pyxtream cache path located at {self.cache_path}")

        if headers is not None:
            self.connection_headers = headers
        else:
            self.connection_headers = {'User-Agent': "Mozilla/5.0"}

        self.authenticate()

        if self.state['authenticated']:
            # Show message about Reload Timer configuration
            if self.threshold_time_sec > 0:
                self.printx(f"Reload timer is ON and set to {self.threshold_time_sec} seconds")
            else:
                self.printx("Reload timer is OFF")
            # Start Flask Web Interface if enabled
            if USE_FLASK and enable_flask:
                self.printx("Starting Web Interface")
                self.flaskapp = FlaskWrap(
                    self.name, self, self.html_template_folder,
                    debug=debug_flask, port=flask_port
                    )
                self.flaskapp.start()
            else:
                self.printx("Web interface not running")

    def printx(self, msg: str, end="\n", flush=True):
        print(f"{self.name}: {msg}", end=end, flush=flush)

    def get_download_progress(self, stream_id: int = None):
        # TODO: Add check for stream specific ID
        return json.dumps(self.download_progress)

    def get_last_7days(self):
        return json.dumps(self.movies_7days, default=lambda x: x.export_json())

    def get_last_30days(self):
        return json.dumps(self.movies_30days, default=lambda x: x.export_json())

    def search_stream(self, keyword: str,
                      ignore_case: bool = True,
                      return_type: str = "LIST",
                      stream_type: list = ("series", "movies", "channels"),
                      added_after: datetime = None) -> list:
        """Search for streams

        Args:
            keyword (str): Keyword to search for. Supports REGEX
            ignore_case (bool, optional): True to ignore case during search. Defaults to "True".
            return_type (str, optional): Output format, 'LIST' or 'JSON'. Defaults to "LIST".
            stream_type (list, optional): Search within specific stream type.
            added_after (datetime, optional): Search for items that have been added after a certain date.

        Returns:
            list: List with all the results, it could be empty.
        """

        search_result = []
        regex_flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(keyword, regex_flags)

        stream_collections = {
            "movies": self.movies,
            "channels": self.channels,
            "series": self.series
        }

        for stream_type_name in stream_type:
            if stream_type_name in stream_collections:
                collection = stream_collections[stream_type_name]
                self.printx(f"Checking {len(collection)} {stream_type_name}")
                for stream in collection:
                    if stream.name and regex.match(stream.name) is not None:
                        if added_after is None:
                            # Add all matches
                            search_result.append(stream.export_json())
                        else:
                            # Only add if it is more recent
                            pass
            else:
                self.printx(f"`{stream_type_name}` not found in collection")

        if return_type == "JSON":
            self.printx(f"Found {len(search_result)} results `{keyword}`")
            return json.dumps(search_result, ensure_ascii=False)

        return search_result

    def download_video(self, stream_type: str, stream_id: int) -> str:
        """Download Video from Stream ID

        Args:
            stream_id (int): String identifying the stream ID

        Returns:
            str: Absolute Path Filename where the file was saved. Empty string if could not download
        """
        url = ""
        filename = ""
        if stream_type == "series":
            for series_stream in self.series:
                if series_stream.series_id == stream_id:
                    episode_object: Episode = series_stream.episodes["1"]
                    url = f"{series_stream.url}/{episode_object.id}."\
                        f"{episode_object.container_extension}"

        if stream_type == "movie":
            for stream in self.movies:
                if stream.id == stream_id:
                    url = stream.url
                    fn = f"{self._slugify(stream.name)}.{stream.raw['container_extension']}"
                    filename = osp.join(self.cache_path, fn)

        # If the url was correctly built and file does not exists, start downloading
        if url == "":
            return ""

        for attempt in range(10):
            if self._download_video_impl(url, filename):
                return filename

        return ""

    def _download_video_impl(self, url: str, fullpath_filename: str) -> bool:
        """Download a stream

        Args:
            url (str): Complete URL of the stream
            fullpath_filename (str): Complete File path where to save the stream

        Returns:
            bool: True if successful, False if error
        """
        ret_code = False
        mb_size = 1024*1024
        headers = self.connection_headers.copy()
        try:
            self.printx(f"Downloading from URL `{url}` and saving at `{fullpath_filename}`")

            # Check if the file already exists
            if osp.exists(fullpath_filename):
                # If the file exists, resume the download from where it left off
                file_size = osp.getsize(fullpath_filename)
                headers['Range'] = f'bytes={file_size}-'
                mode = 'ab'  # Append to the existing file
                self.printx(f"Resuming from {file_size:_} bytes")
            else:
                # If the file does not exist, start a new download
                mode = 'wb'  # Write a new file

            # Make the request to download
            response = requests.get(
                url, timeout=(10),
                stream=True,
                allow_redirects=True,
                headers=headers
                )
            # If there is an answer from the remote server
            if response.status_code in (200, 206):
                # Get content type Binary or Text
                content_type = response.headers.get('content-type', None)

                # Get total playlist byte size
                total_content_size = int(response.headers.get('content-length', None))
                total_content_size_mb = total_content_size/mb_size

                # Set downloaded size
                downloaded_bytes = 0
                self.download_progress['Total'] = total_content_size
                self.download_progress['Progress'] = 0

                # Set stream blocks
                block_bytes = int(4*mb_size)     # 4 MB

                self.printx(f"Ready to download {total_content_size_mb:.1f} "
                            f"MB file ({total_content_size})"
                            )
                if content_type.split('/')[0] != "text":
                    with open(fullpath_filename, mode) as file:

                        # Grab data by block_bytes
                        for data in response.iter_content(block_bytes, decode_unicode=False):
                            downloaded_bytes += block_bytes
                            self.download_progress['Progress'] = downloaded_bytes
                            file.write(data)

                    ret_code = True
                else:
                    self.printx(f"URL has a file with unexpected content-type {content_type}")
            else:
                self.printx(f"HTTP error {response.status_code} while retrieving from {url}")
        except requests.exceptions.ReadTimeout:
            self.printx("Read Timeout, try again")
        except Exception as e:
            self.printx("Unknown error")
            self.printx(e)

        return ret_code

    def _slugify(self, string: str) -> str:
        """Normalize string

        Normalizes string, converts to lowercase, removes non-alpha characters,
        and converts spaces to hyphens.

        Args:
            string (str): String to be normalized

        Returns:
            str: Normalized String
        """
        return "".join(x.lower() for x in string if x.isprintable())

    def _validate_url(self, url: str) -> bool:
        regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        return re.match(regex, url) is not None

    def _get_logo_local_path(self, logo_url: str) -> str:
        """Convert the Logo URL to a local Logo Path

        Args:
            logoURL (str): The Logo URL

        Returns:
            [type]: The logo path as a string or None
        """
        local_logo_path = None
        if logo_url is not None:
            if not self._validate_url(logo_url):
                logo_url = None
            else:
                local_logo_path = osp.join(
                    self.cache_path,
                    f"{self._slugify(self.name)}-{self._slugify(osp.split(logo_url)[-1])}"
                )
        return local_logo_path

    def authenticate(self):
        """Login to provider"""
        # If we have not yet successfully authenticated, attempt authentication
        if self.state["authenticated"] is False:
            # Erase any previous data
            self.auth_data = {}
            # Loop through 30 seconds
            i = 0
            r = None
            # Prepare the authentication url
            url = f"{self.server}/player_api.php?username={self.username}&password={self.password}"
            self.printx("Attempting connection... ", end='')
            while i < 30:
                try:
                    # Request authentication, wait 4 seconds maximum
                    r = requests.get(url, timeout=(4), headers=self.connection_headers)
                    i = 31
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                    time.sleep(1)
                    print(f"{i} ", end='', flush=True)
                    i += 1

            if r is not None:
                # If the answer is ok, process data and change state
                if r.ok:
                    print("Connected")
                    self.auth_data = r.json()
                    self.authorization = {
                        "username": self.auth_data["user_info"]["username"],
                        "password": self.auth_data["user_info"]["password"]
                    }
                    # Account expiration date
                    self.account_expiration = timedelta(
                        seconds=(
                            int(self.auth_data["user_info"]["exp_date"])-datetime.now(timezone.utc).timestamp()
                        )
                    )
                    # Mark connection authorized
                    self.state["authenticated"] = True
                    # Construct the base url for all requests
                    self.base_url = f"{self.server}/player_api.php?username={self.username}&password={self.password}"
                    # If there is a secure server connection, construct the base url SSL for all requests
                    if "https_port" in self.auth_data["server_info"]:
                        self.base_url_ssl = f"https://{self.auth_data['server_info']['url']}:{self.auth_data['server_info']['https_port']}" \
                                            f"/player_api.php?username={self.username}&password={self.password}"
                    self.printx(f"Account expires in {str(self.account_expiration)}")
                else:
                    print("")
                    self.printx(f"Provider `{self.name}` could not be loaded. Reason: `{r.status_code} {r.reason}`")
            else:
                self.printx(f"\n{self.name}: Provider refused the connection")

    def _load_from_file(self, filename) -> dict:
        """Try to load the dictionary from file

        Args:
            filename ([type]): File name containing the data

        Returns:
            dict: Dictionary if found and no errors, None if file does not exists
        """
        # Build the full path
        full_filename = osp.join(self.cache_path, f"{self._slugify(self.name)}-{filename}")

        # If the cached file exists, attempt to load it
        if osp.isfile(full_filename):

            my_data = None

            # Get the elapsed seconds since last file update
            file_age_sec = time.time() - osp.getmtime(full_filename)
            # If the file was updated less than the threshold time,
            # it means that the file is still fresh, we can load it.
            # Otherwise skip and return None to force a re-download
            if self.threshold_time_sec > file_age_sec:
                # Load the JSON data
                try:
                    with open(full_filename, mode="r", encoding="utf-8") as myfile:
                        my_data = json.load(myfile)
                        if len(my_data) == 0:
                            my_data = None
                except Exception as e:
                    self.printx(f" - Could not load from file `{full_filename}`: e=`{e}`")
            return my_data

        return None

    def _save_to_file(self, data_list: dict, filename: str) -> bool:
        """Save a dictionary to file

        This function will overwrite the file if already exists

        Args:
            data_list (dict): Dictionary to save
            filename (str): Name of the file

        Returns:
            bool: True if successful, False if error
        """
        if data_list is None:
            return False

        full_filename = osp.join(self.cache_path, f"{self._slugify(self.name)}-{filename}")
        try:
            with open(full_filename, mode="wt", encoding="utf-8") as file:
                json.dump(data_list, file, ensure_ascii=False)
            return True
        except Exception as e:
            self.printx(f" - Could not save to file `{full_filename}`: e=`{e}`")
            return False

    def load_iptv(self) -> bool:
        """Load XTream IPTV

        - Add all Live TV to XTream.channels
        - Add all VOD to XTream.movies
        - Add all Series to XTream.series
          Series contains Seasons and Episodes. Those are not automatically
          retrieved from the server to reduce the loading time.
        - Add all groups to XTream.groups
          Groups are for all three channel types, Live TV, VOD, and Series

        Returns:
            bool: True if successful, False if error
        """
        # If pyxtream has not authenticated the connection, return empty
        if self.state["authenticated"] is False:
            self.printx("Warning, cannot load steams since authorization failed")
            return False

        # If pyxtream has already loaded the data, skip and return success
        if self.state["loaded"] is True:
            self.printx("Warning, data has already been loaded.")
            return True

        # Delete skipped channels from cache
        full_filename = osp.join(self.cache_path, "skipped_streams.json")
        try:
            with open(full_filename, mode="r+", encoding="utf-8") as f:
                f.truncate(0)
                f.close()
        except FileNotFoundError:
            pass

        for loading_stream_type in (self.live_type, self.vod_type, self.series_type):
            # Get GROUPS

            # Try loading local file
            dt = 0
            start = timer()
            all_cat = self._load_from_file(f"all_groups_{loading_stream_type}.json")
            # If file empty or does not exists, download it from remote
            if all_cat is None:
                # Load all Groups and save file locally
                all_cat = self._load_categories_from_provider(loading_stream_type)
                if all_cat is not None:
                    self._save_to_file(all_cat, f"all_groups_{loading_stream_type}.json")
            dt = timer() - start

            # If we got the GROUPS data, show the statistics and load GROUPS
            if all_cat is not None:
                self.printx(f"Loaded {len(all_cat)} {loading_stream_type} Groups in {dt:.3f} seconds")
                # Add GROUPS to dictionaries

                # Add the catch-all-errors group
                if loading_stream_type == self.live_type:
                    self.groups.append(self.live_catch_all_group)
                elif loading_stream_type == self.vod_type:
                    self.groups.append(self.vod_catch_all_group)
                elif loading_stream_type == self.series_type:
                    self.groups.append(self.series_catch_all_group)

                for cat_obj in all_cat:
                    if schemaValidator(cat_obj, SchemaType.GROUP):
                        # Create Group (Category)
                        new_group = Group(cat_obj, loading_stream_type)
                        #  Add to xtream class
                        self.groups.append(new_group)
                    else:
                        # Save what did not pass schema validation
                        print(cat_obj)

                # Sort Categories
                self.groups.sort(key=lambda x: x.name)
            else:
                self.printx(f" - Could not load {loading_stream_type} Groups")
                break

            # Get Streams

            # Try loading local file
            dt = 0
            start = timer()
            all_streams = self._load_from_file(f"all_stream_{loading_stream_type}.json")
            # If file empty or does not exists, download it from remote
            if all_streams is None:
                # Load all Streams and save file locally
                all_streams = self._load_streams_from_provider(loading_stream_type)
                self._save_to_file(all_streams, f"all_stream_{loading_stream_type}.json")
            dt = timer() - start

            # If we got the STREAMS data, show the statistics and load Streams
            if all_streams is not None:
                self.printx(f"Loaded {len(all_streams)} {loading_stream_type} Streams in {dt:.3f} seconds")
                # Add Streams to dictionaries

                skipped_adult_content = 0
                skipped_no_name_content = 0

                self.printx(f"Processing {loading_stream_type} Streams...")

                start = timer()
                for stream_channel in all_streams:
                    skip_stream = False

                    # Validate JSON scheme
                    if self.validate_json:
                        if loading_stream_type == self.series_type:
                            if not schemaValidator(stream_channel, SchemaType.SERIES_INFO):
                                self.printx(stream_channel)
                        elif loading_stream_type == self.live_type:
                            if not schemaValidator(stream_channel, SchemaType.LIVE):
                                self.printx(stream_channel)
                        else:
                            # vod_type
                            if not schemaValidator(stream_channel, SchemaType.VOD):
                                self.printx(stream_channel)

                    # Skip if the name of the stream is empty
                    if stream_channel["name"] == "":
                        skip_stream = True
                        skipped_no_name_content = skipped_no_name_content + 1
                        self._save_to_file_skipped_streams(stream_channel)

                    # Skip if the user chose to hide adult streams
                    if self.hide_adult_content and loading_stream_type == self.live_type:
                        if "is_adult" in stream_channel:
                            if stream_channel["is_adult"] == "1":
                                skip_stream = True
                                skipped_adult_content = skipped_adult_content + 1
                                self._save_to_file_skipped_streams(stream_channel)

                    if not skip_stream:
                        # Some channels have no group,
                        # so let's add them to the catch all group
                        if not stream_channel["category_id"]:
                            stream_channel["category_id"] = "9999"
                        elif stream_channel["category_id"] != "1":
                            pass

                        # Find the first occurrence of the group that the
                        # Channel or Stream is pointing to
                        the_group = next(
                            (x for x in self.groups if x.group_id == int(stream_channel["category_id"])),
                            None
                        )

                        # Set group title
                        if the_group is not None:
                            group_title = the_group.name
                        else:
                            if loading_stream_type == self.live_type:
                                group_title = self.live_catch_all_group.name
                                the_group = self.live_catch_all_group
                            elif loading_stream_type == self.vod_type:
                                group_title = self.vod_catch_all_group.name
                                the_group = self.vod_catch_all_group
                            elif loading_stream_type == self.series_type:
                                group_title = self.series_catch_all_group.name
                                the_group = self.series_catch_all_group

                        if loading_stream_type == self.series_type:
                            # Load all Series
                            new_series = Serie(self, stream_channel)
                            # To get all the Episodes for every Season of each
                            # Series is very time consuming, we will only
                            # populate the Series once the user click on the
                            # Series, the Seasons and Episodes will be loaded
                            # using x.getSeriesInfoByID() function

                        else:
                            new_channel = Channel(
                                self,
                                group_title,
                                stream_channel
                            )

                        # Save the new channel to the local list of channels
                        if loading_stream_type == self.live_type:
                            if new_channel.group_id == "9999":
                                self.printx(f" - xEverythingElse Channel -> {new_channel.name} - {new_channel.stream_type}")
                            self.channels.append(new_channel)
                        elif loading_stream_type == self.vod_type:
                            if new_channel.group_id == "9999":
                                self.printx(f" - xEverythingElse Channel -> {new_channel.name} - {new_channel.stream_type}")
                            self.movies.append(new_channel)
                            if new_channel.age_days_from_added < 31:
                                self.movies_30days.append(new_channel)
                            if new_channel.age_days_from_added < 7:
                                self.movies_7days.append(new_channel)
                        else:
                            self.series.append(new_series)

                        # Add stream to the specific Group
                        if the_group is not None:
                            if loading_stream_type != self.series_type:
                                the_group.channels.append(new_channel)
                            else:
                                the_group.series.append(new_series)
                        else:
                            self.printx(f" - Group not found `{stream_channel['name']}`")
                print("\n")
                # Print information of which streams have been skipped
                if self.hide_adult_content:
                    self.printx(f" - Skipped {skipped_adult_content} adult {loading_stream_type} streams")
                if skipped_no_name_content > 0:
                    self.printx(f" - Skipped {skipped_no_name_content} "
                                f"unprintable {loading_stream_type} streams")
            else:
                self.printx(f" - Could not load {loading_stream_type} Streams")

            self.state["loaded"] = True
        return True

    def _save_to_file_skipped_streams(self, stream_channel: Channel):

        # Build the full path
        full_filename = osp.join(self.cache_path, "skipped_streams.json")

        # If the path makes sense, save the file
        json_data = json.dumps(stream_channel, ensure_ascii=False)
        try:
            with open(full_filename, mode="a", encoding="utf-8") as myfile:
                myfile.writelines(json_data)
                myfile.write('\n')
            return True
        except Exception as e:
            self.printx(f" - Could not save to skipped stream file `{full_filename}`: e=`{e}`")
        return False

    def get_series_info_by_id(self, get_series: dict):
        """Get Seasons and Episodes for a Series

        Args:
            get_series (dict): Series dictionary
        """

        series_seasons = self._load_series_info_by_id_from_provider(get_series.series_id)

        if series_seasons["seasons"] is None:
            series_seasons["seasons"] = [
                {"name": "Season 1", "cover": series_seasons["info"]["cover"]}
                ]

        for series_info in series_seasons["seasons"]:
            season_name = series_info["name"]
            season = Season(season_name)
            get_series.seasons[season_name] = season
            if "episodes" in series_seasons.keys():
                for series_season in series_seasons["episodes"].keys():
                    for episode_info in series_seasons["episodes"][str(series_season)]:
                        new_episode_channel = Episode(
                            self, series_info, "Testing", episode_info
                        )
                        season.episodes[episode_info["title"]] = new_episode_channel

    def _handle_request_exception(self, exception: requests.exceptions.RequestException):
        """Handle different types of request exceptions."""
        if isinstance(exception, requests.exceptions.ConnectionError):
            self.printx(" - Connection Error: Possible network problem \
                  (e.g. DNS failure, refused connection, etc)")
        elif isinstance(exception, requests.exceptions.HTTPError):
            self.printx(" - HTTP Error")
        elif isinstance(exception, requests.exceptions.TooManyRedirects):
            self.printx(" - TooManyRedirects")
        elif isinstance(exception, requests.exceptions.ReadTimeout):
            self.printx(" - Timeout while loading data")
        else:
            self.printx(f" - An unexpected error occurred: {exception}")

    def _get_request(self, url: str, timeout: Tuple[int, int] = (2, 15)) -> Optional[dict]:
        """Generic GET Request with Error handling

        Args:
            URL (str): The URL where to GET content
            timeout (Tuple[int, int], optional): Connection and Downloading Timeout.
                                                 Defaults to (2,15).

        Returns:
            Optional[dict]: JSON dictionary of the loaded data, or None
        """

        kb_size = 1024
        all_data = []
        down_stats = {"bytes": 0, "kbytes": 0, "mbytes": 0, "start": 0.0, "delta_sec": 0.0}

        response = None
        for attempt in range(10):
            try:
                response = requests.get(
                    url,
                    stream=True,
                    timeout=timeout,
                    headers=self.connection_headers
                    )
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
                break
            except requests.exceptions.RequestException as e:
                self._handle_request_exception(e)
                return None

        # If there is an answer from the remote server
        if response is not None and response.status_code in (200, 206):
            down_stats["start"] = time.perf_counter()

            # Set downloaded size
            down_stats["bytes"] = 0

            # Set stream blocks
            block_bytes = int(1*kb_size*kb_size)     # 1 MB

            # Grab data by block_bytes
            for data in response.iter_content(block_bytes, decode_unicode=False):
                down_stats["bytes"] += len(data)
                down_stats["kbytes"] = down_stats["bytes"]/kb_size
                down_stats["mbytes"] = down_stats["bytes"]/kb_size/kb_size
                down_stats["delta_sec"] = time.perf_counter() - down_stats["start"]
                if down_stats["delta_sec"] > 0:
                    download_speed_average = down_stats["kbytes"] // down_stats["delta_sec"]
                else:
                    download_speed_average = 0
                # Show progress
                msg = f'Downloading {down_stats["kbytes"]:.1f} kB at {download_speed_average:.0f} kB/s'
                sys.stdout.write("\r" + msg)
                sys.stdout.flush()
                all_data.append(data)
            sys.stdout.write(" - Done\n")
            sys.stdout.flush()
            full_content = b''.join(all_data)
            return json.loads(full_content)

        self.printx(f"HTTP error {response.status_code} while retrieving from {url}")

        return None

    # GET Stream Categories
    def _load_categories_from_provider(self, stream_type: str):
        """Get from provider all category for specific stream type from provider

        Args:
            stream_type (str): Stream type can be Live, VOD, Series

        Returns:
            [type]: JSON if successful, otherwise None
        """
        url = ""
        if stream_type == self.live_type:
            url = api.get_live_categories_URL(self.base_url)
        elif stream_type == self.vod_type:
            url = api.get_vod_cat_URL(self.base_url)
        elif stream_type == self.series_type:
            url = api.get_series_cat_URL(self.base_url)
        else:
            url = ""

        return self._get_request(url)

    # GET Streams
    def _load_streams_from_provider(self, stream_type: str):
        """Get from provider all streams for specific stream type

        Args:
            stream_type (str): Stream type can be Live, VOD, Series

        Returns:
            [type]: JSON if successful, otherwise None
        """
        url = ""
        if stream_type == self.live_type:
            url = api.get_live_streams_URL(self.base_url)
        elif stream_type == self.vod_type:
            url = api.get_vod_streams_URL(self.base_url)
        elif stream_type == self.series_type:
            url = api.get_series_URL(self.base_url)
        else:
            url = ""

        return self._get_request(url)

    # GET Streams by Category
    def _load_streams_by_category_from_provider(self, stream_type: str, category_id):
        """Get from provider all streams for specific stream type with category/group ID

        Args:
            stream_type (str): Stream type can be Live, VOD, Series
            category_id ([type]): Category/Group ID.

        Returns:
            [type]: JSON if successful, otherwise None
        """
        url = ""

        if stream_type == self.live_type:
            url = api.get_live_streams_URL_by_category(category_id, self.base_url)
        elif stream_type == self.vod_type:
            url = api.get_vod_streams_URL_by_category(category_id, self.base_url)
        elif stream_type == self.series_type:
            url = api.get_series_URL_by_category(category_id, self.base_url)
        else:
            url = ""

        return self._get_request(url)

    # GET SERIES Info
    def _load_series_info_by_id_from_provider(self, series_id: str, return_type: str = "DICT"):
        """Gets information about a Serie

        Args:
            series_id (str): Serie ID as described in Group
            return_type (str, optional): Output format, 'DICT' or 'JSON'. Defaults to "DICT".

        Returns:
            [type]: JSON if successful, otherwise None
        """
        data = self._get_request(api.get_series_info_URL_by_ID(series_id, self.base_url))
        if return_type == "JSON":
            return json.dumps(data, ensure_ascii=False)
        return data

    # The seasons array, might be filled or might be completely empty.
    # If it is not empty, it will contain the cover, overview and the air date
    # of the selected season.
    # In your APP if you want to display the series, you have to take that
    # from the episodes array.

    # GET VOD Info
    def vodInfoByID(self, vod_id):
        return self._get_request(api.get_VOD_info_URL_by_ID(vod_id, self.base_url), self.base_url)

    # GET short_epg for LIVE Streams (same as stalker portal,
    # prints the next X EPG that will play soon)
    def liveEpgByStream(self, stream_id):
        return self._get_request(api.get_live_epg_URL_by_stream(stream_id, self.base_url))

    def liveEpgByStreamAndLimit(self, stream_id, limit):
        return self._get_request(api.get_live_epg_URL_by_stream_and_limit(stream_id, limit, self.base_url))

    #  GET ALL EPG for LIVE Streams (same as stalker portal,
    # but it will print all epg listings regardless of the day)
    def allLiveEpgByStream(self, stream_id):
        return self._get_request(api.get_all_live_epg_URL_by_stream(stream_id, self.base_url))

    # Full EPG List for all Streams
    def allEpg(self):
        return self._get_request(api.get_all_epg_URL(self.base_url, self.username, self.password))
