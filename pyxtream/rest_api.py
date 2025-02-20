
# Import Flask to control IPTV via REST API
from threading import Thread
import logging
from os import path
from flask import Flask
from flask import Response as FlaskResponse


class EndpointAction(object):

    response: FlaskResponse

    def __init__(self, action, function_name):
        self.function_name = function_name
        self.action = action

    def __call__(self, **args):
        content_types = {
            'html': "text/html; charset=utf-8",
            'json': "text/json; charset=utf-8"
        }

        handlers = {
            # Add handlers here
            "stream_search_generic": lambda: self._handle_search(args['term']),
            "stream_search_with_type": lambda: self._handle_search(args['term'], args.get('type')),
            "download_stream": lambda: self.action(int(args['stream_id'])),
            "get_download_progress": lambda: self.action(int(args['stream_id'])),
            "get_last_7days": lambda: self.action(),
            "home": lambda: self.action,
            "get_series": lambda: self.action(int(args['series_id']), "JSON")
        }

        answer = handlers[self.function_name]()
        content_type = content_types['json'] if self.function_name not in ('home') else content_types['html']

        self.response = FlaskResponse(answer, status=200, headers={"Content-Type": content_type})
        return self.response

    def _handle_search(self, term, stream_type=None):
        regex_term = r"^.*{}.*$".format(term)
        if stream_type:
            stream_type = [stream_type] if stream_type else ("series", "movies", "channels")
            return self.action(regex_term, return_type='JSON', stream_type=stream_type)
        return self.action(regex_term, return_type='JSON')


class FlaskWrap(Thread):

    home_template = """
<!DOCTYPE html><html lang="en"><head></head><body>pyxtream API</body></html>
    """

    host: str = ""
    port: int = 0

    def __init__(self, name, xtream: object, html_template_folder: str = None,
                 host: str = "0.0.0.0", port: int = 5000, debug: bool = True
                 ):

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        self.host = host
        self.port = port
        self.debug = debug

        self.app = Flask(name)
        self.xt = xtream
        Thread.__init__(self)

        # Configure Thread
        self.name = "pyxtream REST API"
        self.daemon = True

        # Load HTML Home Template if any
        if html_template_folder is not None:
            self.home_template_file_name = path.join(html_template_folder, "index.html")
            if path.isfile(self.home_template_file_name):
                with open(self.home_template_file_name, 'r', encoding="utf-8") as home_html:
                    self.home_template = home_html.read()

        # Add all endpoints
        self.add_endpoint(endpoint='/', endpoint_name='home', handler=[self.home_template, "home"])
        self.add_endpoint(endpoint='/stream_search/<term>',
                          endpoint_name='stream_search_generic',
                          handler=[self.xt.search_stream, 'stream_search_generic']
                          )
        self.add_endpoint(endpoint='/stream_search/<term>/<type>',
                          endpoint_name='stream_search_with_type',
                          handler=[self.xt.search_stream, 'stream_search_with_type']
                          )
        self.add_endpoint(endpoint='/download_stream/<stream_id>/',
                          endpoint_name='download_stream',
                          handler=[self.xt.download_video, "download_stream"]
                          )
        self.add_endpoint(endpoint='/get_download_progress/<stream_id>/',
                          endpoint_name='get_download_progress',
                          handler=[self.xt.get_download_progress, "get_download_progress"]
                          )
        self.add_endpoint(endpoint='/get_last_7days',
                          endpoint_name='get_last_7days',
                          handler=[self.xt.get_last_7days, "get_last_7days"]
                          )
        self.add_endpoint(endpoint='/get_series/<series_id>',
                          endpoint_name='get_series',
                          handler=[self.xt._load_series_info_by_id_from_provider, "get_series"]
                          )

    def run(self):
        self.app.run(debug=self.debug, use_reloader=False, host=self.host, port=self.port)

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None):
        self.app.add_url_rule(endpoint, endpoint_name, EndpointAction(*handler))
