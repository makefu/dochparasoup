

try:
    import urllib.parse as urlparse     # py3
except ImportError:
    import urlparse                     # py2

import json

from . import Crawler, CrawlerError


class Reddit(Crawler):
    """ class def: a crawler for Reddit image threads """

    __uri = ""
    __next = ""

    @staticmethod
    def __build_uri(uri):
        return uri + ".json"

    def _restart_at_front(self):
        self.__next = ""

    def __init__(self, uri):
        self.__uri = self.__class__.__build_uri(uri)
        self._restart_at_front()

    def _crawl(self):
        uri = urlparse.urljoin(self.__uri, "?after="+self.__next)
        self.__class__._log("debug", "%s crawls url: %s" % (self.__class__.__name__, uri))

        (remote, uri) = self.__class__._fetch_remote(uri)
        if not remote:
            self.__class__._log("debug", "%s crawled EMPTY url: %s" % (self.__class__.__name__, uri))
            return

        data = json.loads(remote)

        self.__next = data['data']['after']

        images_added = 0
        for child in data['data']['children']:
            image = child['data']['url']
            if image:
                if self._add_image(image):
                    images_added += 1

        if not images_added:
            self.__class__._log("debug", "%s found no images on url: %s" % (self.__class__.__name__, uri))
