import scrapy
from gitscraper.items import gitItem

class GitspiderSpider(scrapy.Spider):
    name = "gitspider"
    allowed_domains = ["github.com"]
    start_urls = ["https://github.com/topics?page=1"]
    count=1
    custom_settings = {
        'FEEDS' : {
            'gitDataFeed.csv' : {'format':'csv' , 'overwrite': True}
        }
    }
    def parse(self, response):
        self.count+=1
        contents = response.css(".py-4.border-bottom.d-flex.flex-justify-between")
        for content in contents:
            inside_url = "https://github.com" + content.css("a:nth-of-type(1)").attrib["href"]
            ss = content.css("a:nth-of-type(1)").attrib["href"].split('/')[2]
            yield response.follow(inside_url,self.parsePage,meta={'main_topic':ss})

        if(self.count<=6):
            url_next=f"https://github.com/topics?page={self.count}"
            yield response.follow(url_next,self.parse)

    def parsePage(self,response):
        main_topic = response.meta.get('main_topic')
        articles = response.css(".border.rounded.color-shadow-small.color-bg-subtle.my-4")
        for article in articles:
            git_item = gitItem()
            git_item['author_name'] = article.css("h3.f3.color-fg-muted.text-normal.lh-condensed a:nth-of-type(1)::text").get().strip()
            git_item['repository_name'] = article.css("h3.f3.color-fg-muted.text-normal.lh-condensed a:nth-of-type(2)::text").get().strip()
            git_item['stars'] = article.css("#repo-stars-counter-star::text").get()
            git_item['repository_url'] = "https://github.com"+article.css("h3.f3.color-fg-muted.text-normal.lh-condensed a:nth-of-type(2)").attrib["href"].strip()
            git_item['main_topic'] = main_topic
            div_with_topics = response.css("div.d-flex.flex-wrap.border-bottom.color-border-muted.px-3.pt-2.pb-2")
            s=""
            for a_tag in div_with_topics.css("a"):
                topic = a_tag.css("::text").get().strip()
                s+=' '+topic
            git_item['tags'] = s
            yield git_item