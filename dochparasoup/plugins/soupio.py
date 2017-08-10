

try:
    from urllib.parse import urljoin    # py3
except ImportError:
    from urlparse import urljoin        # py2

from dochparasoup.crawler import Crawler, CrawlerError
from yapsy.IPlugin import IPlugin
default_cat = 'dickbutt'
base_uri = "http://9gag.com/{}"


frontpage_uri = "http://www.soup.io/everyone"
user_uri =  "http://{}.soup.io/"

class SoupIOPlugin(IPlugin):
    """ TODO: split into Public and User pages """
    def build(self,users):
        if not users or 'true' in users:
            log.debug("using front page for soupio")
            users = 'everyone'
        elif 'false' in users:
            log.info('plugin disabled')
            return []
        return  [SoupIO(frontpage_uri) if user in ["everyone"] else
                SoupIO(user_uri.format(user)) for user in users]

class SoupIO(Crawler):
    """ soup.io image provider """

    __uri = ""
    __next = ""

    @staticmethod
    def __build_uri(uri):
        return urljoin(uri, "?type=image")

    def _restart_at_front(self):
        self.__next = self.__uri

    def __init__(self, uri):
        self.__uri = self.__class__.__build_uri(uri)
        self._restart_at_front()

    def _crawl(self):
        uri = urljoin(self.__uri, self.__next)
        self.__class__._log("debug", "%s crawls url: %s" % (self.__class__.__name__, uri))

        (page, base, _) = self.__class__._fetch_remote_html(uri)
        if not page:
            self.__class__._log("debug", "%s crawled EMPTY url: %s" % (self.__class__.__name__, uri))
            return

        # get more content ("scroll down")
        # to know what page to parse next
        # update new last URI when we're not on first run
        _next = None
        _more = page.find("div", {"id": "more_loading"})
        if _more:
            _more = _more.find("a", {"href": True})
            if _more:
                _next = urljoin(base, _more["href"])
        if _next:
            self.__next = _next
        else:
            self.__class__._log("debug", "%s found no `next` on url: %s" % (self.__class__.__name__, uri))

        # for every found imageContainer
        # add img-src to map if not blacklisted
        images_added = 0
        for con in page.find_all("div", {"class": "imagecontainer"}):
            image = con.find('img', {"src": True})
            if image:
                if self._add_image(urljoin(base, image['src'])):
                    images_added += 1

        if not images_added:
            self.__class__._log("debug", "%s found no images on url: %s" % (self.__class__.__name__, uri))
