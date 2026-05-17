# test_pyxtream.py

import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, mock_open, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pyxtream import Channel, Episode, Group, Season, Serie, XTream

# Mock data for provider connection
mock_provider_name = "Test Provider"
mock_provider_username = "test_user"            # Must be the same as in the MOCK_AUTH_DATA
mock_provider_password = "test_pass"            # Must be the same as in the MOCK_AUTH_DATA
mock_provider_url = "http://test.server.com"    # Must be the same as in the MOCK_AUTH_DATA


# Mock data for testing
MOCK_AUTH_DATA = {
    "user_info": {
        "username": mock_provider_username,
        "password": mock_provider_password,
        "exp_date": str(int((datetime.now() + timedelta(days=30)).timestamp()))
    },
    "server_info": {
        "url": "test.server.com",
        "https_port": "443"
    }
}

MOCK_CATEGORIES = [
    {"category_id": 1, "category_name": "Live TV"},
    {"category_id": 2, "category_name": "Movies"}
]

MOCK_STREAMS = [
    {"num": 1, "stream_id": 1, "name": "Channel 1", "stream_type": "live", "category_id": "1",
     "stream_icon": f"{mock_provider_url}/icon1.png", "added": "1638316800"},
    {"num": 2, "stream_id": 2, "name": "Movie 1", "stream_type": "movie", "category_id": "2",
     "stream_icon": f"{mock_provider_url}/icon2.png", "added": "1638316800", "container_extension": "mp4"}
]

MOCK_SERIES = [
    {
        "num": 1, "name": "Test Series", "series_id": 1, "last_modified": "1638316800",
        "cover": f"{mock_provider_url}/cover.jpg", "plot": "Test plot", "cast": "Test cast",
        "director": "Test director", "genre": "Action", "releaseDate": "2021-01-01",
        "rating": "5", "category_id": "1"
    }
]

MOCK_SERIES_INFO = {
    "seasons": [
        {"season_number": 1, "name": "Season 1",
         "cover": f"{mock_provider_url}/cover1.jpg"}
    ],
    "episodes": {
        "1": [
            {"id": 1, "title": "Episode 1", "container_extension": "mp4",
             "info": {}, "episode_num": 1}
        ]
    }
}


# Fixture for environment setup
@pytest.fixture(scope="module")
def mock_xtream(tmp_path_factory):
    cache_dir = tmp_path_factory.mktemp("xtream_cache")
    # Patching dirname and expanduser to avoid touching real home dirs
    with patch('requests.get') as mock_get, \
         patch('os.path.expanduser', return_value=str(cache_dir)):
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = MOCK_AUTH_DATA
        USE_FLASK = False
        xtream = XTream(
            provider_name=mock_provider_name,
            provider_username=mock_provider_username,
            provider_password=mock_provider_password,
            provider_url=mock_provider_url,
            cache_path=str(cache_dir)
        )
        return xtream


def test_authentication(mock_xtream):
    assert mock_xtream.state["authenticated"] is True
    assert mock_xtream.authorization["username"] == mock_provider_username
    assert mock_xtream.authorization["password"] == mock_provider_password


def test_channel_initialization(mock_xtream):
    stream_info = {
        "stream_id": "123",
        "name": "Test Channel",
        "stream_icon": f"{mock_provider_url}/icon.png",
        "stream_type": "live",
        "category_id": "1",
        "added": "1638316800",
        "container_extension": "ts"
    }
    channel = Channel(mock_xtream, "Test Group", stream_info)
    assert channel.id == "123"
    assert channel.name == "Test Channel"
    assert channel.logo == f"{mock_provider_url}/icon.png"
    assert channel.group_title == "Test Group"
    assert channel.url.startswith(
        f"{mock_provider_url}/live/{mock_provider_username}/{mock_provider_password}/123.ts"
        )


def test_channel_export_json(mock_xtream):
    stream_info = {"stream_id": "1", "name": "C1", "stream_icon": "icon", "stream_type": "live", "category_id": "1", "added": "1638316800"}
    channel = Channel(mock_xtream, "Group", stream_info)
    exported = channel.export_json()
    assert exported["url"] == channel.url
    assert exported["logo_path"] == channel.logo_path


def test_group_initialization():
    group_info = {"category_id": 1, "category_name": "Live TV"}
    group = Group(group_info, "Live")
    assert group.group_id == 1
    assert group.name == "Live TV"
    assert group.group_type == 0  # TV_GROUP


def test_group_region_names():
    group_info = {"category_name": "AR | Arab TV"}
    group = Group(group_info, "Live")
    assert group.region_shortname == "AR"
    assert group.region_longname == "Arab"


def test_serie_initialization(mock_xtream):
    series_info = {
        "series_id": 1,
        "name": "Test Series",
        "cover": f"{mock_provider_url}/cover.jpg",
        "last_modified": "1638316800",
        "plot": "Test plot",
        "youtube_trailer": "http://youtube.com/trailer",
        "genre": "Action"
    }
    serie = Serie(mock_xtream, series_info)
    assert serie.series_id == 1
    assert serie.name == "Test Series"
    assert serie.logo == f"{mock_provider_url}/cover.jpg"
    assert serie.url.startswith(
        f"{mock_provider_url}/series/{mock_provider_username}/{mock_provider_password}/1/"
        )
    assert serie.plot == "Test plot"
    assert serie.youtube_trailer == "http://youtube.com/trailer"
    assert serie.genre == "Action"
    assert isinstance(serie.seasons, dict)
    assert isinstance(serie.episodes, dict)


def test_serie_export_json(mock_xtream):
    serie = Serie(mock_xtream, {"series_id": 1, "name": "S1", "cover": "c", "last_modified": "1", "category_id": "1"})
    assert "logo_path" in serie.export_json()


def test_episode_initialization(mock_xtream):
    series_info = {"cover": f"{mock_provider_url}/cover.jpg"}
    episode_info = {
        "id": 1,
        "title": "Episode 1",
        "container_extension": "mp4",
        "info": {},
        "episode_num": 1
    }
    episode = Episode(mock_xtream, series_info, "Test Group", episode_info)
    assert episode.id == 1
    assert episode.title == "Episode 1"


def test_load_categories(mock_xtream):
    with patch.object(mock_xtream, '_get_request', return_value=MOCK_CATEGORIES) as mock_get:
        # Test live categories
        categories = mock_xtream._load_categories_from_provider(mock_xtream.live_type)
        assert len(categories) == 2
        assert categories[0]["category_name"] == "Live TV"


def test_load_streams(mock_xtream):
    with patch.object(mock_xtream, '_get_request', return_value=MOCK_STREAMS) as mock_get:
        # Test live streams
        streams = mock_xtream._load_streams_from_provider(mock_xtream.live_type)
        assert len(streams) == 2
        assert streams[0]["name"] == "Channel 1"


def test_validate_url(mock_xtream):
    assert mock_xtream._validate_url("http://valid.url") is True
    assert mock_xtream._validate_url("invalid.url") is False


def test_slugify(mock_xtream):
    assert mock_xtream._slugify("Test String!") == "test string!"
    assert mock_xtream._slugify("movie_1.mp4") == "movie_1.mp4"
    assert mock_xtream._slugify("123ABC") == "123abc"


def test_get_logo_local_path(mock_xtream):
    logo_url = f"{mock_provider_url}/logo.png"
    expected_path = os.path.join(
        mock_xtream.cache_path,
        "test provider-logo.png"
    )
    assert mock_xtream._get_logo_local_path(logo_url) == expected_path


def test_load_iptv_full_flow(mock_xtream):
    """Tests the complex load_iptv method which covers significant logic."""
    mock_xtream.state["loaded"] = False  # Force reload

    with patch.object(mock_xtream, '_load_from_file', return_value=None), \
         patch.object(mock_xtream, '_get_request') as mock_req, \
         patch.object(mock_xtream, '_save_to_file', return_value=True):

        # Return sequence for: 
        # 1. Live Categories, 2. Live Streams, 
        # 3. VOD Categories, 4. VOD Streams, 
        # 5. Series Categories, 6. Series Streams
        mock_req.side_effect = [
            MOCK_CATEGORIES, MOCK_STREAMS,
            MOCK_CATEGORIES, MOCK_STREAMS,
            MOCK_CATEGORIES, MOCK_SERIES
        ]

        success = mock_xtream.load_iptv()
        assert success is True
        assert len(mock_xtream.channels) > 0
        assert len(mock_xtream.movies) > 0
        assert len(mock_xtream.series) > 0


def test_search_stream(mock_xtream):
    # Assuming test_load_iptv_full_flow populated lists
    results = mock_xtream.search_stream("Channel", return_type="LIST")
    assert any(res["name"] == "Channel 1" for res in results)

    json_results = mock_xtream.search_stream("Movie", return_type="JSON", stream_type=["movies"])
    assert "Movie 1" in json_results


def test_get_series_info_by_id(mock_xtream):
    series_obj = Serie(mock_xtream, {"series_id": 1, "name": "Test", "cover": "c", "last_modified": "1"})
    with patch.object(mock_xtream, '_get_request', return_value=MOCK_SERIES_INFO):
        mock_xtream.get_series_info_by_id(series_obj)
        assert "Season 1" in series_obj.seasons
        assert len(series_obj.seasons["Season 1"].episodes) > 0


def test_download_video(mock_xtream):
    # Mock a movie in the collection
    movie = Channel(mock_xtream, "VOD", MOCK_STREAMS[1])
    mock_xtream.movies = [movie]

    with patch.object(mock_xtream, '_download_video_impl', return_value=True):
        path = mock_xtream.download_video("movie", 2)
        assert "movie 1.mp4" in path


def test_download_video_impl_resume(mock_xtream):
    url = "http://test.com/video.ts"
    filename = os.path.join(mock_xtream.cache_path, "test.ts")

    # Mock existing file for resume
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=100), \
         patch('requests.get') as mock_get, \
         patch('builtins.open', mock_open()) as mocked_file:

        mock_response = Mock()
        mock_response.status_code = 206
        mock_response.headers = {'content-type': 'video/mp2t', 'content-length': '500'}
        mock_response.iter_content.return_value = [b'data']
        mock_get.return_value = mock_response

        res = mock_xtream._download_video_impl(url, filename)
        assert res is True
        # Verify that Range was passed to requests.get correctly
        assert mock_get.call_args[1]['headers']['Range'] == 'bytes=100-'


def test_get_request_progress(mock_xtream):
    with patch('requests.get') as mock_get, \
         patch('sys.stdout', new_callable=Mock):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.iter_content.return_value = [b'{"key": "val"}']
        mock_get.return_value = mock_resp

        data = mock_xtream._get_request("http://api.url")
        assert data == {"key": "val"}


def test_epg_and_info_helpers(mock_xtream):
    with patch.object(mock_xtream, '_get_request', return_value={"data": "test"}):
        assert mock_xtream.vodInfoByID(1) == {"data": "test"}
        assert mock_xtream.liveEpgByStream(1) == {"data": "test"}
        assert mock_xtream.allEpg() == {"data": "test"}


def test_get_last_7days(mock_xtream):
    mock_xtream.movies_7days = [Channel(mock_xtream, "VOD", MOCK_STREAMS[1])]
    res = json.loads(mock_xtream.get_last_7days())
    assert len(res) == 1


def test_multiple_instances_isolation(tmp_path):
    """Test that 4 instances of the XTream class are fully isolated when used at the same time."""
    configs = []
    # 1. Define 4 distinct configurations
    for i in range(4):
        configs.append({
            "name": f"Provider {i}",
            "url": f"http://server{i}.com",
            "user": f"user{i}",
            "pass": f"pass{i}",
            "cache": str(tmp_path / f"cache{i}"),
            "auth_data": {
                "user_info": {
                    "username": f"user{i}",
                    "password": f"pass{i}",
                    "exp_date": str(int((datetime.now() + timedelta(days=30)).timestamp()))
                },
                "server_info": {"url": f"server{i}.com", "https_port": "443"}
            }
        })

    instances = []
    # 2. Mock requests.get to handle different URLs based on the user/pass credentials
    with patch('requests.get') as mock_get:
        def side_effect(url, **kwargs):
            for c in configs:
                if c["user"] in url and c["pass"] in url:
                    resp = Mock()
                    resp.ok = True
                    resp.json.return_value = c["auth_data"]
                    return resp
            return Mock(ok=False, status_code=401)

        mock_get.side_effect = side_effect

        # 3. Create 4 instances
        for c in configs:
            # Ensure the directory exists so XTream doesn't reject the custom path
            os.makedirs(c["cache"], exist_ok=True)
            instances.append(XTream(
                provider_name=c["name"],
                provider_username=c["user"],
                provider_password=c["pass"],
                provider_url=c["url"],
                cache_path=c["cache"]
            ))

    # 4. Verify isolation
    for i in range(4):
        inst = instances[i]
        config = configs[i]
        assert inst.name == config["name"]
        assert inst.username == config["user"]
        assert inst.cache_path == config["cache"]
        assert inst.authorization["username"] == config["user"]
        assert inst.state["authenticated"] is True

        # Verify that modifying mutable collections in one instance doesn't affect others
        inst.groups.append(f"unique_to_{i}")
        inst.state[f"flag_{i}"] = True

        # Test catch-all group isolation
        # Create a dummy channel and add it to the catch-all group of this instance
        dummy_channel = Channel(inst, "dummy", {
            "stream_id": "99", "name": "N", "stream_icon": "http://i.com",
            "stream_type": "live", "added": "1638316800"
        })
        inst.live_catch_all_group.channels.append(dummy_channel)

        for j in range(4):
            if i != j:
                assert f"unique_to_{i}" not in instances[j].groups
                assert f"flag_{i}" not in instances[j].state
                # Check that the dummy channel is NOT found in other instances' groups
                assert dummy_channel not in instances[j].live_catch_all_group.channels
