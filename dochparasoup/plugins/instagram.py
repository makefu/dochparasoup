

try:
    from urllib.parse import urljoin    # py3
except ImportError:
    from urlparse import urljoin        # py2

import json


from dochparasoup.crawler import Crawler, CrawlerError

from yapsy.IPlugin import IPlugin
default_cat = 'dickbutt'
base_uri = "http://instagram.com/{}"

class InstagramPlugin(IPlugin):
    def build(self,categories):
        if not categories or 'true' in categories:
            log.info('using default category {}'.format(default_cat))
            categories = [default_cat]
        elif 'false' in categories:
            log.info('plugin disabled')
            return []

        return [ Instagram(base_uri.format(cat)) for cat in categories]


class Instagram(Crawler):
    """ instagram image provider """

    __uri = ""
    __last = ""

    ## class methods

    @staticmethod
    def __build_uri(uri):
        return urljoin(uri+"/", "./media/")

    ## instance methods

    def _restart_at_front(self):
        self.__last = ""

    def __init__(self, uri):
        self.__uri = self.__class__.__build_uri(uri)
        self._restart_at_front()

    def _crawl(self):
        uri = urljoin(self.__uri, "?max_id="+self.__last)
        self.__class__._log("debug", "%s crawls url: %s" % (self.__class__.__name__, uri))

        (remote, uri) = self.__class__._fetch_remote(uri)
        if not remote:
            self.__class__._log("debug", "%s crawled EMPTY url: %s" % (self.__class__.__name__, uri))
            return

        data = json.loads(remote)
        if "status" not in data or data["status"] != "ok":
            raise CrawlerError()

        images_added = 0
        for item_image in [item for item in data['items'] if item["type"] == "image"]:
            if 'id' in item_image:
                self.__last = item_image['id']

            if 'images' in item_image \
                    and 'standard_resolution' in item_image['images']\
                    and 'url' in item_image['images']['standard_resolution']:
                image = item_image['images']['standard_resolution']['url']
                if image:
                    if self._add_image(image):
                        images_added += 1

        if not images_added:
            self.__class__._log("debug", "%s found no images on url: %s" % (self.__class__.__name__, uri))

