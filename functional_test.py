#!/usr/bin/python3
"""
Test application to validate provider account access
"""

import sys
from time import sleep

from pyxtream import XTream, __version__

PROVIDER_NAME = ""
PROVIDER_URL = ""
PROVIDER_USERNAME = ""
PROVIDER_PASSWORD = ""

if PROVIDER_URL == "" or PROVIDER_USERNAME == "" or PROVIDER_PASSWORD == "":
    print("Please edit this file with the provider credentials")
    sys.exit()


def str2list(input_string: str) -> list:

    """Convert a string with comma delimited numbers into a python list of integers

    Args:
        input_string (str): A list of commands comma delimited

    Returns:
        list: list of integers containing the commands
    """
    # convert to list
    output_list = input_string.split(",")

    # convert each element as integers
    li = []
    for list_index in output_list:
        try:
            li.append(int(list_index))
        except ValueError:
            pass

    return li


print(f"pyxtream version {__version__}")

xt = XTream(
    PROVIDER_NAME,
    PROVIDER_USERNAME,
    PROVIDER_PASSWORD,
    PROVIDER_URL,
    reload_time_sec=60*60*8,
    debug_flask=True,
    enable_flask=True
    )

sleep(0.5)

# If we could not connect, exit
if xt.auth_data == {}:
    print("Authentication failed")
    sleep(0.5)
    sys.exit(0)

while True:
    print(
        """
        ** Menu **
        ----------
        (1) Load IPTV
        (2) Search Streams Regex
        (3) Search Streams Text
        (4) Download Video (stream_id)
        (5) Download Video Impl (URL, filename)
        (6) Show how many movies added in past 30 days
        (7) Show how many movies added in past 7 days
        (8) Get Series Info By ID (series_id)
        (9) Get Live EPG by Stream ID
        ----------
        (0) Quit
        """
        )
    sleep(0.1)
    # Get user input
    commands = input(">>> ").lower().rstrip()
    # Convert string of commands to list of integers
    command_list = str2list(commands)

    for choice in command_list:
        print(f"\t[{choice}]: ")

        if choice == 0:
            sys.exit(0)

        elif choice == 1:
            if not xt.load_iptv():
                print("Something wrong")

        elif choice == 2:
            search_string = input("Search for REGEX (ex. '^Destiny.*$'): ")
            search_result_obj = xt.search_stream(search_string, stream_type=("movies", "series"))
            result_number = len(search_result_obj)
            print(f"\tFound {result_number} results")
            if result_number < 10:
                for stream in search_result_obj:
                    if 'url' in stream:
                        print(f"Found `{stream['name']}` at URL: {stream['url']}")
                    else:
                        print(stream)

        elif choice == 3:
            search_string = input("Search for text: ")
            search_result_obj = xt.search_stream(
                rf"^.*{search_string}.*$", stream_type=("movies", "series")
                )
            result_number = len(search_result_obj)
            print(f"\tFound {result_number} results")
            if result_number < 10:
                for stream in search_result_obj:
                    if 'url' in stream:
                        print(f"Found {stream['name']} at URL: {stream['url']}")
                    else:
                        print(stream)

        elif choice == 4:
            stream_id = input("Stream ID: ")
            stream_id_number = int(stream_id)

            if stream_id_number > 0:
                print(f"\n\tFile saved at `{xt.download_video(int(stream_id))}`")
            else:
                print("\n\tInvalid number")

        elif choice == 5:
            url = input("Enter URL to download: ")
            filename = input("Enter Fullpath Filename: ")
            xt._download_video_impl(url, filename)

        elif choice == 6:
            NUM_MOVIES = len(xt.movies_30days)
            print(f"Found {NUM_MOVIES} new movies in the past 30 days")
            if NUM_MOVIES < 20:
                for i in range(0, NUM_MOVIES):
                    print(xt.movies_30days[i].title)

        elif choice == 7:
            NUM_MOVIES = len(xt.movies_7days)
            print(f"Found {NUM_MOVIES} new movies in the past 7 days")
            if NUM_MOVIES < 20:
                for i in range(0, NUM_MOVIES):
                    print(xt.movies_7days[i].title)

        elif choice == 8:
            series_id = input("Series ID: ")
            # Load series seasons and episodes
            data = xt._load_series_info_by_id_from_provider(series_id, "JSON")
            if data is not None:
                print(data)
            else:
                print("No series found for that ID")

        elif choice == 9:
            stream_id = input("Stream ID: ")
            data = xt.liveEpgByStream(stream_id)
            print(data)
