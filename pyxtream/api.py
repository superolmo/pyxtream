"""
API URL builders
"""


def get_live_categories_URL(base: str) -> str:
    return f"{base}&action=get_live_categories"


def get_live_streams_URL(base: str) -> str:
    return f"{base}&action=get_live_streams"


def get_live_streams_URL_by_category(category_id, base: str) -> str:
    return f"{base}&action=get_live_streams&category_id={category_id}"


def get_vod_cat_URL(base: str) -> str:
    return f"{base}&action=get_vod_categories"


def get_vod_streams_URL(base: str) -> str:
    return f"{base}&action=get_vod_streams"


def get_vod_streams_URL_by_category(category_id, base: str) -> str:
    return f"{base}&action=get_vod_streams&category_id={category_id}"


def get_series_cat_URL(base: str) -> str:
    return f"{base}&action=get_series_categories"


def get_series_URL(base: str) -> str:
    return f"{base}&action=get_series"


def get_series_URL_by_category(category_id, base: str) -> str:
    return f"{base}&action=get_series&category_id={category_id}"


def get_series_info_URL_by_ID(series_id, base: str) -> str:
    return f"{base}&action=get_series_info&series_id={series_id}"


def get_VOD_info_URL_by_ID(vod_id, base: str) -> str:
    return f"{base}&action=get_vod_info&vod_id={vod_id}"


def get_live_epg_URL_by_stream(stream_id, base: str) -> str:
    return f"{base}&action=get_short_epg&stream_id={stream_id}"


def get_live_epg_URL_by_stream_and_limit(stream_id, limit, base: str) -> str:
    return f"{base}&action=get_short_epg&stream_id={stream_id}&limit={limit}"


def get_all_live_epg_URL_by_stream(stream_id, base: str) -> str:
    return f"{base}&action=get_simple_data_table&stream_id={stream_id}"


def get_all_epg_URL(base: str, username: str, password: str) -> str:
    return f"{base}/xmltv.php?username={username}&password={password}"
