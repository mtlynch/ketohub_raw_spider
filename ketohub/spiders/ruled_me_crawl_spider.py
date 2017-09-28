from scrapy import linkextractors
from scrapy import spiders

from ketohub.spiders import raw_content_spider


class RuledMeCrawlSpider(raw_content_spider.RawContentSpider):
    """Spider to crawl keto sites and save the html and image to a local file for each recipe."""
    name = 'ruled_me_raw_content'
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
            callback='download_recipe_contents',
            follow=False)
    ]

    def _get_recipe_main_image_url(self, response):
        """Returns the URL for the recipe's primary image."""
        return str(response.css('img').xpath('@src').extract_first())
