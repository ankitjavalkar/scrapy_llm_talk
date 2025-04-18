import json
from json.decoder import JSONDecodeError
from logging import getLogger

import ollama
from html2text import HTML2Text
from litellm import acompletion
from scrapy import Spider

html_cleaner = HTML2Text()
logger = getLogger(__name__)


async def llm_parse(response, prompts):
    """
    This method accepts a Scrapy response object and a dict with the field names as keys and
    the field specific prompts as values. It returns the LLM response
    """

    # Generate a list of keys and formatted string of key value pairs from prompt dict
    key_list = ", ".join(prompts)
    formatted_scheme = "\n".join(f"{k}: {v}" for k, v in prompts.items())

    # Convert response to markdown
    markdown = html_cleaner.handle(response.text)

    # Ask the LLM
    llm_response = await acompletion(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Return a JSON object with the following root keys: "
                    f"{key_list}\n"
                    f"\n"
                    f"Data to scrape:\n"
                    f"{formatted_scheme}\n"
                    f"\n"
                    f"Scrape it from the following Markdown text:\n"
                    f"\n"
                    f"{markdown}"
                ),
            },
        ],
        model="ollama/mistral",
    )

    # Get the result data from the API response
    data = llm_response["choices"][0]["message"]["content"]

    # Check if the result data is valid JSON and return the JSON or JSONDecodeError
    try:
        return json.loads(data)
    except JSONDecodeError:
        logger.error(f"LLM returned an invalid JSON for {response.url}: {data}")
        return {}

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

        # Prompt 1 - To get product name and product price
        prompts = {
            "name": "Product name",
            "price": "Product price as a number, without the currency symbol",
        }

        # Prompt 2 - To get product name and list of character names from description
        # prompts = {
        #     "name": "Product name",
        #     "characters": "Comma separated list of names from the Product description",
        # }


        # Call the LLM via API
        llm_data = await llm_parse(response, prompts)

        # Result data
        yield {
            "url": response.url,
            **llm_data,
        }
