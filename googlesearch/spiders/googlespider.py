from urllib import urlencode
from urlparse import urljoin, urlparse
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.spider import BaseSpider
from scrapy.utils.response import get_base_url
from googlesearch.items import GoogleSearchItem

"""
A spiser to parse the google search result.
"""
class GoogleSearchSpider(BaseSpider):
    name = 'googlesearch'
    kws = 'contact information'
    country = 'com'
    start_urls = []

    def start_requests(self):
        url = self.make_google_search_request(self.country, self.kws)
        yield Request(url=url)

    def make_google_search_request(self, country, keywords):
        return 'http://www.google.{}/search?{}'.format(country, urlencode({'q': keywords}))

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        for sel in hxs.select('//div[@id="ires"]//li[@class="g"]'):
            name = ''.join(sel.select(".//h3[@class='r']//text()").extract())
            url =  ''.join(sel.select(".//cite//text()").extract())
            yield Request(url=self._urlnorm(url), callback=self.parse_item, meta={'name':name})

        next_page = hxs.select('//table[@id="nav"]//td[@class="b" and position() = last()]/a')
        if next_page:
            url = self._build_absolute_url(response, next_page.select('.//@href').extract()[0])
            yield Request(url=url, callback=self.parse)

    def parse_item(self, response):
        name = response.meta['name']
        url = response.url
        body = response.body[:1024 * 256]
        yield GoogleSearchItem({'name': name, 'url': url, 'body': body})

    def _build_absolute_url(self, response, url):
        return urljoin(get_base_url(response), url)

    def _urlnorm(self, url, encoding='utf8'):

        url = url.strip()
        if isinstance(url, unicode):
            url = url.encode('ascii', 'ignore')
        else:
            url = url.decode(encoding).encode('ascii', 'ignore')

        if '://' not in url:
            url = 'http://%s' % url

        scheme, netloc, path = urlparse(url)[:3]
        return '%s://%s%s' % (scheme, netloc, path or '/')