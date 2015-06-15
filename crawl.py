#!/usr/bin/env python
""" usage: crawl [-c CONFIG]

Options:
    -c CONFIG           Path to config file [default: config.ini]
"""

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


## import crawler
from yapsy.PluginManager import PluginManager

from docopt import docopt

_file_path = path.dirname(path.realpath(__file__))

# argument parser
args = docopt(__doc__)
config_file = args['-c']

## configuration
config = RawConfigParser()
config.read(path.join(_file_path, 'config.defaults.ini'))
try:
    with open(config_file) as conf:
        try:
            config.read_file(conf)  # py3
        except AttributeError:
            config.readfp(conf)     # py2
except IOError as e:
    log.error('cannot open config file {}'.format(config_file))
    sys.exit(1)

nps_port = config.getint("General", "Port")
nps_bindip = config.get("General", "IP")
min_cache_imgs = config.getint("Cache", "Images")
min_cache_imgs_before_refill = config.getint("Cache", "Images_min_limit")
user_agent = config.get("General", "Useragent")
logverbosity = config.get("Logging", "Verbosity")
logger = logging.getLogger(config.get("Logging", "Log_name"))
#hdlr = logging.FileHandler(config.get("Logging", "File"))
#hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
#logger.addHandler(hdlr)
logging.basicConfig(level=logverbosity.upper())
logging.debug("level set to debug")

call_flush_timeout = 10  # value in seconds
call_flush_last = time.time() - call_flush_timeout

call_reset_timeout = 10  # value in seconds
call_reset_last = time.time() - call_reset_timeout

from dochparasoup.crawler import Crawler
Crawler.request_headers({'User-Agent': user_agent})
Crawler.set_logger(logger)

### config the  crawlers

def get_crawlers(configuration, section):
    """
    parse the config section for crawlers
    * does recognize (by name) known and implemented crawlers only
    * a robust config reading and more freedom for users

    :param configuration: RawConfigParser
    :param section: string
    :return: list
    """
    manager = PluginManager()
    manager.setPluginPlaces([configuration.get("Sites","plugin_dir")])
    manager.collectPlugins()
    crawlers = []
    for plugin in manager.getAllPlugins():

        plug = plugin.plugin_object
        plug_name = plugin.name
        if not configuration.has_option(section, plug_name):
            logger.debug("plugin {} not configured".format(plug_name))
            continue    # skip crawler if not configured

        crawler_config = configuration.get(section, plug_name)
        logger.debug("{} config is: {}".format(plug_name,crawler_config))
        if crawler_config.lower() == "false":
            logger.debug("plugin {} disabled".format(plug_name))
            continue    # skip crawler if disabled

        crawler_uris = []

        configured_categories = [url_quote_plus(site_stripped) for site_stripped in
                         [site.strip() for site in crawler_config.split(",")]   # trim sites
                         if site_stripped]  # filter stripped list for valid values

        # plugin factories always provide a 'default' if no category is
        # configured
        crawlers += plug.build(configured_categories)

    logger.info("configured crawlers: {}".format(crawlers))
    return crawlers


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
