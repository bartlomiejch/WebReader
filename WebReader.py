#!/usr/bin/python3
import configparser
import logging
import redis
import requests
import sys
import threading
import time
import validators

from http.server import BaseHTTPRequestHandler, HTTPServer

REDIS_DB = redis.StrictRedis(host="localhost", port=6379, db=0)


def validate_configuration(section):
    """

    :param section: Section from configuration file
    :return: string contain error message or 'OK' if configuration is fine
    """
    keys = []
    result = ''

    for key, value in section:
        if key == 'url':
            if not validators.url(value):
                result += 'wrong url. '
        if key == 'period':
            try:
                int(value)
            except ValueError:
                result += 'period value should be an integer. '
        keys.append(key)
    if 'url' not in keys:
        result += 'does not contain "url" parameter. '
    elif 'content' not in keys:
        result += 'does not contain "content" parameter. '
    elif 'period' not in keys:
        result += 'does not contain "period" parameter. '
    else:
        if result == '':
            result += 'OK'
    return result


class WebReader():
    def __init__(self, config_parser):
        self.config_parser = config_parser
        logging.basicConfig(format='%(levelname)s:%(message)s', filename='WebReader.log', level=logging.DEBUG)

    def http_request(self, url, content, period, section):
        """

        :param url: url address
        :param content: content requirement
        :param period: interval in seconds to make HTTP request
        :param section: name of section in configuration file
        :return: None
        """
        while True:
            try:
                response = requests.get(url)
                response_time = response.elapsed.total_seconds()
                matches = False
                if response.status_code not in range(400, 512):
                    if content in response.text:
                        matches = True

                REDIS_DB.set(section, "url: %s, status: %s, matches the content requirements: %s, response time in sec: %s"
                 % (url, response.status_code, str(matches), response_time))
                logging.debug("url: %s, status: %s, matches the content requirements: %s, response time in sec: %s"
                 % (url, response.status_code, str(matches), response_time))
            except Exception as e:
                logging.error("Error while connecting to page: %s: %s" % (url, e))
            time.sleep(int(period))

    def prepare_configuration_items(self):
        """
        :return: dictionary contain all needed values to run thread
        """
        conf_items = {}
        for section in self.config_parser.sections():
            message = validate_configuration(self.config_parser.items(section))
            if message == 'OK':
                conf_items[section] = {}
                for key, value in self.config_parser.items(section):
                    conf_items[section][key] = value
            else:
                logging.error("Configuration error - section ignored: %s - %s" % (section, message))
                REDIS_DB.delete(section)

        return conf_items

    def start(self):
        """
        Starts thread for every task from configuration file
        :return: None
        """
        conf_items = self.prepare_configuration_items()
        for section, conf_values in conf_items.items():
            th = threading.Thread(target=self.http_request, args=(conf_values['url'],
                conf_values['content'], conf_values['period'], section))
            th.daemon = True
            th.start()


class ServerHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        html = ""
        for key in REDIS_DB.keys():
            html += '<h2>%s<h2>' % REDIS_DB.get(key)

        self.wfile.write(html.encode('utf-8'))


def run(server_class=HTTPServer, handler_class=ServerHandler, port=8080):
    """
    :param server_class: object of class:'HTTPServer'
    :param handler_class: object of class: 'ServerHandler'
    :param port: default 8080
    :return: None
    """
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


def wrapper(conf_file, port):
    """
    :param conf_file: configuration file
    :param port: port number to run server interface
    :return: None
    """
    config_parser = configparser.ConfigParser()
    config_parser.read(conf_file)

    try:
        w = WebReader(config_parser)
        w.start()
        run(port=port)
    except Exception as e:
        logging.error("Could not start webreader. %s" % e)
        sys.exit()


if __name__ == '__main__':

    conf_file = None
    port = None

    try:
        conf_file = sys.argv[1]
        port = int(sys.argv[2])
    except Exception as e:
        logging.error('Incorrect number of arguments, or incorrect type of arguments: %s' % e)

    if conf_file and port:
        wrapper(conf_file, port)
