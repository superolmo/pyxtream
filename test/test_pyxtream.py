# test_pyxtream.py
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

import sys
sys.path.insert(0, '../pyxtream')
from pyxtream import Channel, Episode, Group, Serie, XTream

# Mock data for provider connection
mock_provider_name = "Test Provider"
mock_provider_username = "test_user" # Must be the same as in the MOCK_AUTH_DATA
mock_provider_password = "test_pass" # Must be the same as in the MOCK_AUTH_DATA
mock_provider_url = "http://test.server.com" # Must be the same as in the MOCK_AUTH_DATA


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
    {"stream_id": 1, "name": "Channel 1", "stream_type": "live", "category_id": 1,
     "stream_icon": f"{mock_provider_url}/icon1.png", "added": "1638316800"},
    {"stream_id": 2, "name": "Movie 1", "stream_type": "movie", "category_id": 2,
     "stream_icon": f"{mock_provider_url}/icon2.png", "added": "1638316800"}
]

MOCK_SERIES_INFO = {
    "seasons": [
        {"season_number": 1, "name": "Season 1", "cover": f"{mock_provider_url}/cover1.jpg"}
    ],
    "episodes": {
        "1": [
            {"id": 1, "title": "Episode 1", "container_extension": "mp4", "info": {}}
        ]
    }
}

# Fixture for environment setup
@pytest.fixture(autouse=True)
def setup_environment(monkeypatch):
    """Setup environment before each test."""
    # Mock the cache directory
    monkeypatch.setattr("pyxtream.XTream.cache_path", "/tmp/pyxtream_cache")
    # Ensure the cache directory exists
    os.makedirs("/tmp/pyxtream_cache", exist_ok=True)


@pytest.fixture(scope="module")
def mock_xtream():
    with patch('requests.get') as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = MOCK_AUTH_DATA
        USE_FLASK=False
        xtream = XTream(
            provider_name=mock_provider_name,
            provider_username=mock_provider_username,
            provider_password=mock_provider_password,
            provider_url=mock_provider_url
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

def test_group_initialization():
    group_info = {"category_id": 1, "category_name": "Live TV"}
    group = Group(group_info, "Live")
    assert group.group_id == 1
    assert group.name == "Live TV"
    assert group.group_type == 0  # TV_GROUP

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
    assert mock_xtream._slugify("123ABC") == "123abc"

def test_get_logo_local_path(mock_xtream):
    logo_url = f"{mock_provider_url}/logo.png"
    expected_path = os.path.join(
        mock_xtream.cache_path,
        "test provider-logo.png"
    )
    assert mock_xtream._get_logo_local_path(logo_url) == expected_path
