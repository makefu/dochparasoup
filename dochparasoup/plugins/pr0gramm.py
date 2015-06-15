
import re

try:
    from urllib.parse import urljoin    # py3
except ImportError:
    from urlparse import urljoin        # py2

from dochparasoup.crawler import Crawler, CrawlerError
from yapsy.IPlugin import IPlugin

default_cat = 'static'
base_uri = "http://pr0gramm.com/static/{}"

class Pr0grammPlugin(IPlugin):
    def build(self,categories):
        if not categories or 'true' in categories:
            log.info('using default category {}'.format(default_cat))
            categories = [default_cat]
        elif 'false' in categories:
            log.info('plugin disabled')
            return []

        return [ Pr0gramm(base_uri.format(cat)) for cat in categories]

class Pr0gramm(Crawler):
    """ pr0gramm.com image provider"""

    ## class constants

    ## properties

    __uri = ""
    __next = ""

    __filter = re.compile('^/static/[\d]+')

    ## functions

    @staticmethod
    def __build_uri(uri):
        return uri

    def _restart_at_front(self):
        self.__next = self.__uri

    def __init__(self, uri):
        self.__uri = self.__class__.__build_uri(uri)
        self._restart_at_front()

    def _crawl(self):
        uri = self.__next
        self.__class__._log("debug", "%s crawls url: %s" % (self.__class__.__name__, uri))

        (page_container, base, _) = self.__class__._fetch_remote_html(uri)
        if not page_container:
            self.__class__._log("debug", "%s crawled EMPTY url: %s" % (self.__class__.__name__, uri))
            return

        pages = page_container.findAll("a", href=self.__filter)
        images_added = 0
        for page in pages:
            if self.__crawl_page(urljoin(base, page["href"])):
                images_added += 1

        # @todo add paging: fetch next and stuff ...

        if not images_added:
            self.__class__._log("debug", "%s found no images on url: %s" % (self.__class__.__name__, uri))

    def __crawl_page(self, uri):
        (page, base, _) = self.__class__._fetch_remote_html(uri)
        if not page:
            self.__class__._log("debug", "%s sub-crawled EMPTY url: %s" % (self.__class__.__name__, uri))
            return False

        image = page.find("img", {"src": True})
        if not image:
            return False

        return self._add_image(urljoin(base, image["src"]))
