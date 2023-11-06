#!/usr/bin/python3

provider_name = "YourProvider"
url=""
username=""
password=""

import json
import sys
from os import remove
from time import sleep

# Initialize pyxtream
from pyxtream import XTream, __version__

if url == "" or username == "" or password == "":
    print("Please edit this file with the provider credentials")
    sys.exit()

def str2list(commands: str) -> list:

    """Convert a string with comma delimited numbers into a python list of integers

    Args:
        commands (str): A list of commands comma delimited

    Returns:
        list: list of integers containing the commands
    """
    # conver to the list
    command_list = commands.split(",")
    #print("Command List: {}".format(command_list))

    # convert each element as integers
    li = []
    for i in command_list:
        try:
            li.append(int(i))
        except ValueError:
            pass

    return li

print("pyxtream version {}".format(__version__))

xt = XTream("YourProvider", username, password, url, reload_time_sec=60*60*8, debug_flask=False)

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
        print("\t[{}]: ".format(choice))

        if choice == 0:
            #xt.flaskapp.shutdown()
            sys.exit(0)

        elif choice == 1:
            xt.load_iptv()

        elif choice == 2:
            search_string = input("Search for REGEX (ex. '^Destiny.*$'): ")
            search_result_obj = xt.search_stream(search_string)
            result_number = len(search_result_obj)
            print("\tFound {} results".format(result_number))
            if result_number < 10:
                for stream in search_result_obj:
                    print("Found `{}` at URL: {}".format(stream['name'], stream['url']))

        elif choice == 3:
            search_string = input("Search for text: ")
            search_result_obj = xt.search_stream(r"^.*{}.*$".format(search_string))
            result_number = len(search_result_obj)
            print("\tFound {} results".format(result_number))
            if result_number < 10:
                for stream in search_result_obj:
                    try:
                        print("Found {} at URL: {}".format(stream['name'], stream['url']))
                    except KeyError:
                        print("Exception")

        elif choice == 4:
            stream_id = input("Stream ID: ")
            try:
                stream_id_number = int(stream_id)
            except:
                stream_id_number = 0

            if stream_id_number > 0:
                print("\tFile saved at `{}`".format(xt.download_video(int(stream_id))))
            else:
                print("\tInvalid number")

        elif choice == 5:
            url = input("Enter URL to download: ")
            filename = input("Enter Fullpath Filename: ")
            xt.download_video_impl(url,filename)
