import json
from json.decoder import JSONDecodeError
from logging import getLogger

import ollama
from html2text import HTML2Text
from litellm import acompletion
from scrapy import Spider

html_cleaner = HTML2Text()
logger = getLogger(__name__)
