from scrapy import conf
from scrapy import linkextractors
from scrapy import spiders

import persist
import recipe_key


class Error(Exception):
    """Base Error class."""
    pass


class MissingDownloadDirectory(Error):
    """Error raised when the download directory is not defined."""
    pass


def _get_download_root():
    download_root = conf.settings.get('DOWNLOAD_ROOT')
    if not download_root:
        raise MissingDownloadDirectory(
            'Make sure you\'re providing a download directory.')
    return download_root


class CallbackHandler(object):

    def __init__(self, content_saver, recipe_key_from_url_func):
        self._content_saver = content_saver
        self._recipe_key_from_url_func = recipe_key_from_url_func

    def process_callback(self, response):
        key = self._recipe_key_from_url_func(response.url)
        self._content_saver.save_metadata(key, {
            'url':
            response.url,
            'referer':
            response.request.headers['Referer'],
        })
        self._content_saver.save_recipe_html(key, response.text.encode('utf8'))


class KetoConnectSpider(spiders.CrawlSpider):
    name = 'ketoconnect'

    callback_handler = CallbackHandler(
        content_saver=persist.ContentSaver(_get_download_root()),
        recipe_key_from_url_func=recipe_key.from_url)

    allowed_domains = ['ketoconnect.net']
    start_urls = ['https://www.ketoconnect.net/recipes/']

    rules = [
        # Extract links for food category pages,
        # e.g. https://ketoconnect.net/desserts/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=r'https://www.ketoconnect.net/\w+(-\w+)*/$',
                restrict_xpaths=
                '//div[@id="tve_editor"]//span[@class="tve_custom_font_size rft"]'
            )),

        # Extract links for the actual recipes
        # e.g. https://www.ketoconnect.net/recipe/spicy-cilantro-dressing/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=r'https://www.ketoconnect.net/recipe/\w+(-\w+)*/$',
                restrict_xpaths='//div[@class="tve_post tve_post_width_4"]'),
            callback=callback_handler.process_callback,
            follow=False),
    ]


class RuledMeSpider(spiders.CrawlSpider):
    name = 'ruled-me'

    callback_handler = CallbackHandler(
        content_saver=persist.ContentSaver(_get_download_root()),
        recipe_key_from_url_func=recipe_key.from_url)

    allowed_domains = ['ruled.me']
    start_urls = ['https://www.ruled.me/keto-recipes/']

    rules = [
        # Extract links for food category pages,
        # e.g. https://www.ruled.me/keto-recipes/breakfast/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=r'https://www.ruled.me/keto-recipes/\w+(-\w+)*/$',
                restrict_xpaths='//div[@class="r-list"]')),

        # Extract links for finding additional pages within food category pages,
        # e.g. https://www.ruled.me/keto-recipes/dinner/page/2/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=r'https://www.ruled.me/keto-recipes/\w+(\w+)*/page/\d+/')
        ),

        # Extract links for the actual recipes,
        # e.g. https://www.ruled.me/easy-keto-cordon-bleu/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=r'https://www.ruled.me/(\w+-)+\w+/$',
                restrict_xpaths='//div[@id="content"]'),
            callback=callback_handler.process_callback,
            follow=False)
    ]
