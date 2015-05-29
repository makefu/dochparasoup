#!/usr/bin/env python

### import libraries
from os import path
import random
import logging
import time
import threading
import argparse

try:
    from configparser import RawConfigParser    # py 3
except ImportError:
    from ConfigParser import RawConfigParser    # py 2

try:
    from urllib.parse import quote_plus as url_quote_plus   # py3
except ImportError:
    from urllib import quote_plus as url_quote_plus         # py2


from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.serving import run_simple


## import templates
import templates as tmpl


## import crawler
from crawler import Crawler


_file_path = path.dirname(path.realpath(__file__))

# argument parser
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-c', '--config-file', metavar='<file>',
                        type=argparse.FileType('r'),
                        default=open(path.join(_file_path, 'config.ini'), 'r'),
                        help='a file path to the config ini',
                        dest="config_file")
args = arg_parser.parse_args()


## configuration
config = RawConfigParser()
config.read(path.join(_file_path, 'config.defaults.ini'))
try:
    config.read_file(args.config_file)  # py3
except AttributeError:
    config.readfp(args.config_file)     # py2
args.config_file.close()

nps_port = config.getint("General", "Port")
nps_bindip = config.get("General", "IP")
min_cache_imgs = config.getint("Cache", "Images")
min_cache_imgs_before_refill = config.getint("Cache", "Images_min_limit")
user_agent = config.get("General", "Useragent")
logverbosity = config.get("Logging", "Verbosity")
logger = logging.getLogger(config.get("Logging", "Log_name"))
hdlr = logging.FileHandler(config.get("Logging", "File"))
hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(hdlr)
logger.setLevel(logverbosity.upper())

call_flush_timeout = 10  # value in seconds
call_flush_last = time.time() - call_flush_timeout

call_reset_timeout = 10  # value in seconds
call_reset_last = time.time() - call_reset_timeout

Crawler.request_headers({'User-Agent': user_agent})
Crawler.set_logger(logger)

### config the  crawlers
from crawler.reddit import Reddit
from crawler.soupio import SoupIO
from crawler.pr0gramm import Pr0gramm
from crawler.ninegag import NineGag
from crawler.instagram import Instagram
from crawler.fourchan import Fourchan
from crawler.giphy import Giphy
from crawler.bildschirmarbeiter import Bildschirmarbeiter


def get_crawlers(configuration, section):
    """
    parse the config section for crawlers
    * does recognize (by name) known and implemented crawlers only
    * a robust config reading and more freedom for users

    :param configuration: RawConfigParser
    :param section: string
    :return: list
    """
    crawlers = []

    for crawler_class in Crawler.__subclasses__():
        crawler_class_name = crawler_class.__name__
        if not configuration.has_option(section, crawler_class_name):
            continue    # skip crawler if not configured

        crawler_config = configuration.get(section, crawler_class_name)
        if not crawler_config or crawler_config.lower() == "false":
            continue    # skip crawler if not configured or disabled

        crawler_uris = []

        # mimic old behaviours for bool values
        if crawler_config.lower() == "true":
            if crawler_class == Pr0gramm:
                crawler_config = "static"
            elif crawler_class == SoupIO:
                crawler_config = "everyone"

        crawler_sites = [url_quote_plus(site_stripped) for site_stripped in
                         [site.strip() for site in crawler_config.split(",")]   # trim sites
                         if site_stripped]  # filter stripped list for valid values
        if not crawler_sites:
            continue    # skip crawler if no valid sites configured

        logger.info("found configured Crawler: %s = %s" % (crawler_class_name, repr(crawler_sites)))

        if crawler_class == Reddit:
            crawler_uris = ["http://www.reddit.com/r/%s" % site for site in crawler_sites]
        elif crawler_class == NineGag:
            crawler_uris = ["http://9gag.com/%s" % site for site in crawler_sites]
        elif crawler_class == Pr0gramm:
            crawler_uris = ["http://pr0gramm.com/static/%s" % site for site in crawler_sites]
        elif crawler_class == SoupIO:
            crawler_uris = [("http://www.soup.io/%s" if site in ["everyone"]    # public site
                             else "http://%s.soup.io") % site                   # user site
                            for site in crawler_sites]
        elif crawler_class == Instagram:
            crawler_uris = ["http://instagram.com/%s" % site for site in crawler_sites]
        elif crawler_class == Fourchan:
            crawler_uris = ["http://boards.4chan.org/%s/" % site for site in crawler_sites]
        elif crawler_class == Giphy:
            crawler_uris = ["http://api.giphy.com/v1/gifs/search?q=%s" % site for site in crawler_sites]
        elif crawler_class == Bildschirmarbeiter:
            crawler_uris = ["http://www.bildschirmarbeiter.com/plugs/category/%s/P120/" % site for site in crawler_sites]

        crawlers += [crawler_class(crawler_uri) for crawler_uri in crawler_uris]

    return crawlers

sources = get_crawlers(config, "Sites")




### runtime
# main function how to run
# on start-up, fill the cache and get up the webserver
if __name__ == "__main__":
    sources = get_crawlers(config, "Sites")
    while True:
        for s in sources:
            logging.info('crawling {}'.format(s))
            s.crawl()
    if not sources:
        raise Exception("no sources configured")
