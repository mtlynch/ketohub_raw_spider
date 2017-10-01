import datetime
import os

from scrapy import conf
from scrapy import linkextractors
from scrapy import spiders

import images
import persist
import recipe_key


class Error(Exception):
    """Base Error class."""
    pass


class MissingDownloadDirectory(Error):
    """Error raised when the download directory is not defined."""
    pass


def _calculate_download_dir(start_time):
    download_root = conf.settings.get('DOWNLOAD_ROOT')
    if not download_root:
        raise MissingDownloadDirectory(
            'Make sure you\'re providing a download directory.')

    download_subdir = start_time.strftime('%Y%m%d/%H%M%SZ')

    return os.path.join(download_root, download_subdir)


def find_ketoconnect_image_url(response):
    return str(response.css('img')[1].xpath('@src').extract_first())


def find_ruled_me_image_url(response):
    return str(response.css('img').xpath('@src').extract_first())


class CallbackHandler(object):

    def __init__(self, content_saver, recipe_key_from_url_func,
                 find_image_url_func, image_download_data_func):
        self._content_saver = content_saver
        self._recipe_key_from_url_func = recipe_key_from_url_func
        self._find_image_url_func = find_image_url_func
        self._image_download_data_func = image_download_data_func

    def process_callback(self, response):
        key = self._recipe_key_from_url_func(response.url)
        self._content_saver.save_metadata(key, {'url': response.url})
        self._content_saver.save_recipe_html(key, response.text.encode('utf8'))

        image_url = self._find_image_url_func(response)
        image_data = self._image_download_data_func(image_url)
        self._content_saver.save_main_image(key, image_data)


class KetoConnectSpider(spiders.CrawlSpider):
    name = 'ketoconnect'

    callback_handler = CallbackHandler(
        content_saver=persist.ContentSaver(
            _calculate_download_dir(datetime.datetime.utcnow())),
        recipe_key_from_url_func=recipe_key.from_url,
        find_image_url_func=find_ketoconnect_image_url,
        image_download_data_func=images.download_data)

    allowed_domains = ['ketoconnect.net']
    start_urls = ['https://www.ketoconnect.net/recipes/']

    rules = [
        # Extract links for food category pages ex: https://ketoconnect.net/recipes/desserts/
        spiders.Rule(
            linkextractors.LinkExtractor(allow=[
                r'https://ketonnect.com/\w+(-\w+)+/',
            ])),

        # Extract links for the actual recipes
        # ex: https://www.ketoconnect.net/recipe/spicy-cilantro-dressing/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=[r'https://www.ketoconnect.net/recipe/\w+(-\w+)+/']),
            callback=callback_handler.process_callback,
            follow=False)
    ]


class RuledMeSpider(spiders.CrawlSpider):
    name = 'ruled-me'

    callback_handler = CallbackHandler(
        content_saver=persist.ContentSaver(
            _calculate_download_dir(datetime.datetime.utcnow())),
        recipe_key_from_url_func=recipe_key.from_url,
        find_image_url_func=find_ruled_me_image_url,
        image_download_data_func=images.download_data)

    allowed_domains = ['ruled.me']
    start_urls = ['https://www.ruled.me/keto-recipes/']

    rules = [
        # Extract links for food category pages ex: https://www.ruled.me/keto-recipes/breakfast/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=[r'https://www.ruled.me/keto-recipes/\w+/'])),

        # Extract links for finding additional pages within food category pages
        # ex: https://www.ruled.me/keto-recipes/dinner/page/2/
        spiders.Rule(
            linkextractors.LinkExtractor(
                allow=r'https://www.ruled.me/keto-recipes/\w+/page/\d+/')),

        # Extract links for the actual recipes
        # ex: https://www.ruled.me/easy-keto-cordon-bleu/
        spiders.Rule(
            linkextractors.LinkExtractor(allow=[
                r'https://www.ruled.me/(\w+-)+\w+/',
            ]),
            callback=callback_handler.process_callback,
            follow=False)
    ]
