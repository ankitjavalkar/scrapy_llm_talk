import json
from json.decoder import JSONDecodeError
from logging import getLogger

import ollama
from html2text import HTML2Text
from litellm import acompletion
from scrapy import Spider

html_cleaner = HTML2Text()
logger = getLogger(__name__)


class BooksToScrapeComLLMSpider(Spider):
    name = "books_toscrape_com_llm"
    start_urls = [
        "http://books.toscrape.com/catalogue/category/books/mystery_3/index.html"
    ]

    def parse(self, response):
        # Parse the pagination link and parse the next page
        next_page_links = response.css(".next a")
        yield from response.follow_all(next_page_links)

        # Parse the book links on the listing page
        book_links = response.css("article a")
        yield from response.follow_all(book_links, callback=self.parse_book)

    async def parse_book(self, response):
        # Define the field names and field data prompts
        # Call the LLM via API
        # Result data
