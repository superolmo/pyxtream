
# Import Flask to control IPTV via REST API
try:
    from flask import Flask
    from flask import Response as FlaskResponse
    from flask import request as FlaskRequest
    from threading import Thread
except:
    pass

from os import path

class EndpointAction(object):

    def __init__(self, action, function_name):
        self.function_name = function_name
        self.action = action

    def __call__(self, **args):

        if args != {}:

            #Stream Search
            if self.function_name == "stream_search":
                regex_term = r"^.*{}.*$".format(args['term'])
                answer = self.action(regex_term,  return_type = 'JSON')

            # Download stream
            elif self.function_name == "download_stream":
                answer = self.action(int(args['stream_id']))

            else:
                print(args)
                answer = "Hello"

            self.response = FlaskResponse(answer, status=200, headers={})
            self.response.headers["Content-Type"] = "text/json; charset=utf-8"
        else:
            answer = self.action
            self.response = FlaskResponse(answer, status=200, headers={})
            self.response.headers["Content-Type"] = "text/html; charset=utf-8"

        return self.response

class FlaskWrap(Thread):

    home_template = """
<!DOCTYPE html><html lang="en"><head></head><body>pyxtream API</body></html>
    """

    host: str = ""
    port: int = 0

    def __init__(self, name, xtream: object, html_template_folder: str = None, host: str = "0.0.0.0", port: int = 5000, debug: bool = True):

        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        self.host = host
        self.port = port
        self.debug = debug

        self.app = Flask(name)
        self.xt = xtream
        Thread.__init__(self)
        
        # Configure Thread
        self.setName("pyxtream REST API")
        self.daemon = True

        # Load HTML Home Template if any
        if html_template_folder != None:
            self.home_template_file_name = path.join(html_template_folder,"index.html")
            if path.isfile(self.home_template_file_name):
                with open(self.home_template_file_name,'r') as home_html:
                    self.home_template = home_html.read()

        # Add all endpoints
        self.add_endpoint(endpoint='/', endpoint_name='home', handler=[self.home_template,""])
        self.add_endpoint(endpoint='/stream_search/<term>', endpoint_name='stream_search', handler=[self.xt.search_stream,"stream_search"])
        self.add_endpoint(endpoint='/download_stream/<stream_id>/', endpoint_name='download_stream', handler=[self.xt.download_video,"download_stream"])

    def run(self):
        self.app.run(debug=self.debug, use_reloader=False, host=self.host, port=self.port)

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None):
        self.app.add_url_rule(endpoint, endpoint_name, EndpointAction(*handler))
