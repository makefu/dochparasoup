
import urllib

from dochparasoup.crawler import Crawler, CrawlerError

from yapsy.IPlugin import IPlugin

import logging
log = logging.getLogger("Bildschirmarbeiter")

base_uri="http://www.bildschirmarbeiter.com/plugs/category/{}"
default_cat = 'pics'

class BildschirmarbeiterPlugin(IPlugin):
    def build(self,categories):
        """
        Bildschirmarbeiter factory
        expects a list of categories
        """
        if not categories or 'true' in categories:
            log.info('using default category {}'.format(default_cat))
            categories = [default_cat]
        elif 'false' in categories:
            log.info('plugin disabled')
            return []

        return [ Bildschirmarbeiter(base_uri.format(cat)) for cat in categories]


class Bildschirmarbeiter(Crawler):
    """ bildschirmarbeiter image provider """

    __uri = ""
    __next = ""

    @staticmethod
    def __build_uri(uri):
        return uri

    def _restart_at_front(self):
        self.__next = self.__uri

    def __init__(self, uri):
        """
        http://www.bildschirmarbeiter.com/plugs/category/%s/
        """
        self.__uri = self.__build_uri(uri)
        self._restart_at_front()
        

    def _crawl(self):
        uri = self.__next
        self.__next = None
        log.debug("crawl url: %s" % ( uri))

        (page, base, _) = self._fetch_remote_html(uri)
        if not page:
            log.debug("crawled EMPTY url: %s" % ( uri))
            return
        new_imgs=0
        for plug in page.find_all("a",class_="plugthumb"):
            # grab each 'plug' from the current page
            try:
                (npage,base,_) = self._fetch_remote_html(plug["href"])
            except urllib.error.HTTPError as e:
                log.warn("could not fetch page {}".format(plug["href"]))
                continue
            for gal_divs in npage.find_all("div",class_="gallery"):
                # this may be skipped if there is no gallery
                for img in gal_divs.find_all("img"):
                    self._add_image(img["src"])
                    new_imgs +=1
        for page_link in page.find("div",id="col1_content").find_all("a"):
            if page_link.get_text().strip() == ">":
                self.__next = page_link['href']

        if not self.__next:
            raise CrawlerError("at last page for url {} ?".format(uri))

        if not new_imgs:
            log.warn("no images found for url {}".format(uri))


