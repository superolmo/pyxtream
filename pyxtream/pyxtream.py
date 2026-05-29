#!/usr/bin/python3
"""
High-performance Python library for Xtream Codes IPTV panels. Supports Live TV, VOD, and Series.
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
from typing import Any, Optional, Tuple

import requests

from pyxtream import api
from pyxtream.schemaValidator import SchemaType, schemaValidator
from pyxtream.constants import (
    AUTH_LOOP_EXIT_VALUE,
    AUTH_MAX_ATTEMPTS,
    AUTH_TIMEOUT_SEC,
    CATCH_ALL_CATEGORY_ID,
    DEFAULT_FLASK_PORT,
    DEFAULT_RELOAD_TIME_SEC,
    DOWNLOAD_BLOCK_SIZE,
    DOWNLOAD_TIMEOUT_SEC,
    KB_FACTOR,
    MB_FACTOR,
    MOVIES_RECENT_30_DAYS_THRESHOLD,
    MOVIES_RECENT_7_DAYS_THRESHOLD,
    REQUEST_BLOCK_SIZE,
    REQUEST_DEFAULT_TIMEOUT,
    REQUEST_MAX_ATTEMPTS,
    SECONDS_IN_DAY,
    SECONDS_IN_YEAR,
)

try:
    from pyxtream.rest_api import FlaskWrap
    USE_FLASK = True
except ImportError:
    USE_FLASK = False


class Channel:
    """Represents a Live TV or VOD stream."""
    def __init__(self, xtream: object, group_title, stream_info: dict):
        self.date_now = datetime.now(timezone.utc)
        self.stream_type = stream_info["stream_type"]
        # Adjust the odd "created_live" type
        if self.stream_type in ("created_live", "radio_streams"):
            self.stream_type = "live"

        if self.stream_type not in ("live", "movie"):
            print(f"Error the channel has unknown stream type "
                  f"`{self.stream_type}`\n`{stream_info}`")
            self.raw = {}
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

            if self.stream_type == "live":
                stream_extension = "ts"

                # Check if epg_channel_id key is available
                if "epg_channel_id" in stream_info.keys():
                    self.epg_channel_id = stream_info["epg_channel_id"]

            elif self.stream_type == "movie":
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
            self.url = f"{xtream.server}/{self.stream_type}/{xtream.authorization['username']}/" \
                       f"{xtream.authorization['password']}/{stream_info['stream_id']}.{stream_extension}"

            # Check that the constructed URL is valid
            if not xtream._validate_url(self.url):
                print(f"{self.name} - Bad URL? `{self.url}`")

    def export_json(self):
        """Return a dictionary representation of the channel with its computed URL."""
        jsondata = {}

        jsondata["url"] = self.url
        jsondata.update(self.raw)
        jsondata["logo_path"] = self.logo_path

        return jsondata


class Group:
    """Represents a category of channels, movies, or series."""
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
    """Represents a single episode of a TV series."""
    def __init__(self, xtream: object, series_info, group_title, episode_info: dict) -> None:
        # Raw JSON Episode
        self.raw = episode_info

        self.title = episode_info["title"]
        self.name = self.title
        self.group_title = group_title
        self.id = episode_info["id"]
        self.container_extension = episode_info["container_extension"]
        self.episode_number = episode_info["episode_num"]
        self.av_info = episode_info["info"]

        self.logo = series_info.get("cover", "")
        self.logo_path = xtream._get_logo_local_path(self.logo) if len(self.logo) > 0 else ""

        self.url = f"{xtream.server}/series/" \
                   f"{xtream.authorization['username']}/" \
                   f"{xtream.authorization['password']}/{self.id}.{self.container_extension}"

        # Check that the constructed URL is valid
        if not xtream._validate_url(self.url):
            print(f"{self.name} - Bad URL? `{self.url}`")


class Serie:
    """Represents a TV Series collection."""
    def __init__(self, xtream: object, series_info: dict):

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
        """Return a dictionary representation of the series."""
        jsondata = {}

        jsondata.update(self.raw)
        jsondata['logo_path'] = self.logo_path

        return jsondata


class Season:
    """Represents a specific season within a series."""

    def __init__(self, name):
        self.name = name
        self.episodes = {}


class XTream:
    """Core client for interacting with Xtream Codes IPTV providers."""
    def __init__(
        self,
        provider_name: str,
        provider_username: str,
        provider_password: str,
        provider_url: str,
        headers: dict = {},
        hide_adult_content: bool = False,
        cache_path: str = "",
        reload_time_sec: int = DEFAULT_RELOAD_TIME_SEC,
        validate_json: bool = False,
        enable_flask: bool = False,
        debug_flask: bool = True,
        flask_port: int = DEFAULT_FLASK_PORT
            ):
        """Initialize the XTream client.

        Sets up the connection parameters, authentication state, and local cache
        configuration for interacting with an Xtream Codes IPTV provider.

        Args:
            provider_name (str): Human-readable name of the IPTV provider.
            provider_username (str): Username for authentication.
            provider_password (str): Password for authentication.
            provider_url (str): Base URL of the IPTV provider.
            headers (dict, optional): Custom HTTP headers for requests. Defaults to {}.
            hide_adult_content (bool, optional): If True, filters out adult content. Defaults to False.
            cache_path (str, optional): Directory for local data persistence. Defaults to "".
            reload_time_sec (int, optional): Cache TTL in seconds. Defaults to DEFAULT_RELOAD_TIME_SEC.
            validate_json (bool, optional): If True, validates responses against schemas. Defaults to False.
            enable_flask (bool, optional): If True, starts the REST API server. Defaults to False.
            debug_flask (bool, optional): If True, enables Flask debug mode. Defaults to True.
            flask_port (int, optional): Port for the Flask server. Defaults to DEFAULT_FLASK_PORT.
        """
        self.server = provider_url
        self.username = provider_username
        self.password = provider_password
        self.name = provider_name
        self.cache_path = cache_path
        self.hide_adult_content = hide_adult_content
        self.threshold_time_sec = reload_time_sec
        self.validate_json = validate_json
        self.live_type = "Live"
        self.vod_type = "VOD"
        self.series_type = "Series"

        self.live_catch_all_group = Group(
            {"category_id": "9999", "category_name": "xEverythingElse", "parent_id": 0}, self.live_type
        )
        self.vod_catch_all_group = Group(
            {"category_id": "9999", "category_name": "xEverythingElse", "parent_id": 0}, self.vod_type
        )
        self.series_catch_all_group = Group(
            {"category_id": "9999", "category_name": "xEverythingElse", "parent_id": 0}, self.series_type
        )

        self.auth_data = {}
        self.authorization = {'username': '', 'password': ''}

        self.groups = []
        self.channels = []
        self.series = []
        self.movies = []
        self.movies_30days = []
        self.movies_7days = []

        self.connection_headers = {}

        self.state = {'authenticated': False, 'loaded': False, 'offline': False}

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
        """Print a message prefixed with the provider name.

        Useful for logging multiple instances of the XTream class simultaneously.

        Args:
            msg (str): The message to be printed.
            end (str, optional): The string appended after the last value. Defaults to "\\n".
            flush (bool, optional): Whether to forcibly flush the stream. Defaults to True.
        """
        print(f"{self.name}: {msg}", end=end, flush=flush)

    def get_download_progress(self, stream_id: int = None):
        """Return the current download progress as a JSON string.

        Retrieves the state of the downloader, including total bytes and progress.

        Args:
            stream_id (int, optional): The specific stream ID to check. Currently unused.

        Returns:
            str: A JSON-formatted string containing 'StreamId', 'Total', and 'Progress'.
        """
        # TODO: Add check for stream specific ID
        return json.dumps(self.download_progress)

    def get_last_7days(self):
        """Return movies added in the last 7 days as a JSON string.

        Returns:
            str: A JSON-formatted list of movies added recently.
        """
        return json.dumps(self.movies_7days, default=lambda x: x.export_json())

    def get_last_30days(self):
        """Return movies added in the last 30 days as a JSON string.

        Returns:
            str: A JSON-formatted list of movies added in the last month.
        """
        return json.dumps(self.movies_30days, default=lambda x: x.export_json())

    def get_state(self):
        """Return the current authentication and loading state as a JSON string.

        Returns:
            str: A JSON string containing 'authenticated', 'loaded', and 'offline' flags.
        """
        return json.dumps(self.state)

    def search_stream(self, keyword: str,
                      ignore_case: bool = True,
                      return_type: str = "LIST",
                      stream_type: list = ("series", "movies", "channels"),
                      added_after: datetime = None) -> list:
        """Search for streams across the loaded collection.

        Uses regular expressions to find matches in titles across specified stream types.

        Args:
            keyword (str): The regex pattern or search term.
            ignore_case (bool, optional): Whether to ignore case in the regex. Defaults to True.
            return_type (str, optional): The output format, either 'LIST' or 'JSON'. Defaults to "LIST".
            stream_type (list, optional): Collections to search in. Defaults to ("series", "movies", "channels").
            added_after (datetime, optional): Filter results added after this date.

        Returns:
            list: A list of matching items in the requested format (LIST or JSON string).
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

    def download_video(self, stream_id: int) -> str:
        """Download a video stream by its ID and return the local file path.

        Attempts to resolve the stream ID to a movie or series episode and downloads it.

        Args:
            stream_id (int): The unique ID of the stream to download.

        Returns:
            str: The absolute local path to the downloaded file, or an empty string on failure.
        """
        url = ""
        filename = ""

        # Search for the stream_id within series
        for series_stream in self.series:
            if series_stream.series_id == stream_id:
                if series_stream.episodes and "1" in series_stream.episodes:
                    episode_object: Episode = series_stream.episodes["1"]
                    url = f"{series_stream.url}/{episode_object.id}.{episode_object.container_extension}"
                    # Construct a local filename for the episode
                    fn = f"{self._slugify(series_stream.name)}-E1.{episode_object.container_extension}"
                    filename = osp.join(self.cache_path, fn)
                break

        # Search for the stream_id within movies (streams) if not found in series
        if not url:
            for stream in self.movies:
                if stream.id == stream_id:
                    url = stream.url
                    fn = f"{self._slugify(stream.name)}.{stream.raw['container_extension']}"
                    filename = osp.join(self.cache_path, fn)
                    break

        # If the url was correctly built and file does not exists, start downloading
        if url == "":
            return ""

        for attempt in range(10):
            if self._download_video_impl(url, filename):
                return filename

        return ""

    def _download_video_impl(self, url: str, fullpath_filename: str) -> bool:
        """Internal implementation for downloading a stream.

        Handles chunked downloading, progress updates, and resumable transfers via Range headers.

        Args:
            url (str): The direct URL of the video stream.
            fullpath_filename (str): The local destination path.

        Returns:
            bool: True if the download completed successfully, False otherwise.
        """
        ret_code = False
        mb_size = MB_FACTOR
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
                url, timeout=(DOWNLOAD_TIMEOUT_SEC),
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
                block_bytes = int(DOWNLOAD_BLOCK_SIZE)

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
        """Convert a string to a safe filename format.

        Args:
            string (str): Input string.

        Returns:
            str: A lowercase, sanitized string.
        """
        return "".join(x.lower() for x in string if x.isprintable())

    def _validate_url(self, url: str) -> bool:
        """Check if a URL string has a valid format.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
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
        """Generate a local cache path for a stream logo URL.

        Args:
            logo_url (str): The remote URL of the logo.

        Returns:
            str: The local file path where the logo should be cached.
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
        """Authenticate with the provider and initialize base URLs.

        Attempts to log in using the player_api.php endpoint. On failure, it triggers
        the offline fallback mechanism if a local cache exists.

        Sets the authentication state and base URLs for subsequent API calls.
        """
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
            while i < AUTH_MAX_ATTEMPTS:
                try:
                    # Request authentication, wait AUTH_TIMEOUT_SEC seconds maximum
                    r = requests.get(url, timeout=(AUTH_TIMEOUT_SEC), headers=self.connection_headers)
                    if r.ok:
                        i = AUTH_LOOP_EXIT_VALUE
                    else:
                        i += 1
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
                    self._fallback_to_offline()
            else:
                self.printx(f"\n{self.name}: Provider refused the connection")
                self._fallback_to_offline()

    def _fallback_to_offline(self):
        """Check for local cache and enter offline mode if available"""
        cache_exists = False
        for stream_type in (self.live_type, self.vod_type, self.series_type):
            filename = f"all_groups_{stream_type}.json"
            full_filename = osp.join(self.cache_path, f"{self._slugify(self.name)}-{filename}")
            if osp.isfile(full_filename):
                cache_exists = True
                break

        if cache_exists:
            self.printx("Offline mode active: Using local cache fallback")
            self.state["offline"] = True
            self.authorization = {
                "username": self.username,
                "password": self.password
            }
            self.auth_data = {
                "user_info": {
                    "username": self.username,
                    "password": self.password,
                    "exp_date": str(int(datetime.now(timezone.utc).timestamp() + SECONDS_IN_YEAR))
                },
                "server_info": {"url": self.server}
            }
            self.base_url = f"{self.server}/player_api.php?username={self.username}&password={self.password}"
            self.state["authenticated"] = True
        else:
            self.printx("No local cache available.")

    def _load_from_file(self, filename: str) -> Optional[Any]:
        """Load a JSON structure from the local cache.

        Args:
            filename (str): The name of the file to load (without provider prefix).

        Returns:
            Optional[Any]: The loaded data if fresh and available, otherwise None.
        """
        # Build the full path
        full_filename = osp.join(self.cache_path, f"{self._slugify(self.name)}-{filename}")

        # If the cached file exists, attempt to load it
        if osp.isfile(full_filename):

            # Get the elapsed seconds since last file update
            file_age_sec = time.time() - osp.getmtime(full_filename)
            # If the file was updated less than the threshold time,
            # it means that the file is still fresh, we can load it.
            # If threshold is -1, we force load from file regardless of age (Persistence Mode).
            # Otherwise skip and return None to force a re-download
            if self.state['offline'] or self.threshold_time_sec == -1 or self.threshold_time_sec > file_age_sec:
                # Load the JSON data
                try:
                    with open(full_filename, mode="r", encoding="utf-8") as myfile:
                        return json.load(myfile) or None
                except Exception as e:
                    self.printx(f" - Could not load from file `{full_filename}`: e=`{e}`")

        return None

    def _save_to_file(self, data_list: dict, filename: str) -> bool:
        """Save a dictionary as a JSON file in the local cache.

        Args:
            data_list (dict): Data to be persisted.
            filename (str): Local filename.

        Returns:
            bool: True if saving was successful.
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
        """Orchestrates the loading and processing of all IPTV content.

        Iterates through Live, VOD, and Series types. Loads categories and streams
        from the local cache if available and fresh, or fetches them from the provider.

        Returns:
            bool: True if the loading cycle completed successfully.
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
                            stream_channel["category_id"] = str(CATCH_ALL_CATEGORY_ID)
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
                            if new_channel.group_id == CATCH_ALL_CATEGORY_ID:
                                self.printx(f" - xEverythingElse Channel -> {new_channel.name} - {new_channel.stream_type}")
                            self.channels.append(new_channel)
                        elif loading_stream_type == self.vod_type:
                            if new_channel.group_id == CATCH_ALL_CATEGORY_ID:
                                try:
                                    self.printx(f" - xEverythingElse Channel -> {new_channel.name} - {new_channel.stream_type}")
                                except AttributeError as e:
                                    print(f"{new_channel.raw} {e}")
                            self.movies.append(new_channel)
                            if new_channel.age_days_from_added < MOVIES_RECENT_30_DAYS_THRESHOLD:
                                self.movies_30days.append(new_channel)
                            if new_channel.age_days_from_added < MOVIES_RECENT_7_DAYS_THRESHOLD:
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
        """Log skipped streams to a local JSON file for debugging.

        Args:
            stream_channel (Channel): The channel object being skipped.

        Returns:
            bool: True if logging succeeded.
        """
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
        """Fetch and populate seasons and episodes for a specific series object.

        Args:
            get_series (Serie): The series object to be populated with detailed data.
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
                    # add only episodes of current season
                    # use series_season as fallback to make sure episodes will be set
                    # if we can not parse the season number
                    if int(series_info.get('season_number', series_season)) != int(series_season):
                        continue
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

    def _get_request(self, url: str, timeout: Tuple[int, int] = REQUEST_DEFAULT_TIMEOUT) -> Optional[dict]:
        """Perform a GET request with retries and progress reporting.

        Args:
            url (str): The target URL.
            timeout (Tuple[int, int], optional): Connection and read timeout.

        Returns:
            Optional[dict]: The parsed JSON response, or None on error.
        """

        all_data = []
        down_stats = {"bytes": 0, "kbytes": 0, "mbytes": 0, "start": 0.0, "delta_sec": 0.0}

        response = None
        for attempt in range(REQUEST_MAX_ATTEMPTS):
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
            block_bytes = int(REQUEST_BLOCK_SIZE)

            # Grab data by block_bytes
            for data in response.iter_content(block_bytes, decode_unicode=False):
                down_stats["bytes"] += len(data)
                down_stats["kbytes"] = down_stats["bytes"] / KB_FACTOR
                down_stats["mbytes"] = down_stats["bytes"] / MB_FACTOR
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
        """Fetch all categories for a specific stream type from the provider.

        Args:
            stream_type (str): Either 'Live', 'VOD', or 'Series'.
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
        """Fetch all streams for a specific stream type from the provider.

        Args:
            stream_type (str): Either 'Live', 'VOD', or 'Series'.
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
        """Fetch streams within a specific category from the provider.

        Args:
            stream_type (str): Either 'Live', 'VOD', or 'Series'.
            category_id (int|str): The unique ID of the category.
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
        """Fetch detailed information about a series from the provider.

        Args:
            series_id (str): The unique series ID.
            return_type (str, optional): The format, 'DICT' or 'JSON'. Defaults to "DICT".
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
        """Fetch VOD information by movie ID.

        Args:
            vod_id (int|str): The movie ID.
        """
        return self._get_request(api.get_VOD_info_URL_by_ID(vod_id, self.base_url), self.base_url)

    # GET short_epg for LIVE Streams (same as stalker portal,
    # prints the next X EPG that will play soon)
    def liveEpgByStream(self, stream_id):
        """Fetch current short EPG data for a live stream.

        Args:
            stream_id (int|str): The stream ID.
        """
        return self._get_request(api.get_live_epg_URL_by_stream(stream_id, self.base_url))

    def liveEpgByStreamAndLimit(self, stream_id, limit):
        """Fetch short EPG data for a live stream with a result limit.

        Args:
            stream_id (int|str): The stream ID.
            limit (int): Maximum number of entries.
        """
        return self._get_request(api.get_live_epg_URL_by_stream_and_limit(stream_id, limit, self.base_url))

    #  GET ALL EPG for LIVE Streams (same as stalker portal,
    # but it will print all epg listings regardless of the day)
    def allLiveEpgByStream(self, stream_id):
        """Fetch all available EPG data for a live stream via simple_data_table.

        Args:
            stream_id (int|str): The stream ID.
        """
        return self._get_request(api.get_all_live_epg_URL_by_stream(stream_id, self.base_url))

    # Full EPG List for all Streams
    def allEpg(self):
        """Fetch the complete XMLTV EPG for all channels."""
        return self._get_request(api.get_all_epg_URL(self.base_url, self.username, self.password))
