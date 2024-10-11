# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GitscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class gitItem(scrapy.Item):
    author_name = scrapy.Field()
    repository_name = scrapy.Field()
    stars = scrapy.Field()
    repository_url = scrapy.Field()
    main_topic = scrapy.Field()
    tags = scrapy.Field(output_processor=lambda x: [tag.strip() for tag in x.split(' ')])