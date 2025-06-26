import json
import os
import html2text
import openai

from typing import Optional
from playwright.sync_api import sync_playwright


class DelistingDownloader:
    def __init__(self, index_url, doc_selector):
        self.index_url = index_url
        self.doc_selector = doc_selector

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
        )
        self.page = self.browser.new_page()
        self.llm = openai.OpenAI(
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
        )

    def announcements(self):
        self.page.goto(self.index_url)
        h = html2text.HTML2Text()
        markdown = h.handle(self.page.content())

        completion = self.llm.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Extract announcement titles, dates and links from the markdown content. This page url is {self.index_url}"
                        "Return the result as a JSON list of dictionaries with keys 'title', 'date'(format %Y-%m%-%d), and 'link'(full url). "
                        "The output must be a valid JSON object with key 'announcements'."
                    ),
                },
                {"role": "user", "content": markdown},
            ],
            response_format={"type": "json_object"},
        )

        try:
            result = json.loads(completion.choices[0].message.content)  # pyright: ignore
            if "announcements" in result:
                return result["announcements"]
        except json.JSONDecodeError:
            pass

        return []

    def delistings(self, announcement) -> Optional[list]:
        self.page.goto(announcement["link"])
        doc = self.page.query_selector(self.doc_selector)
        if not doc:
            return

        content = doc.text_content()
        if not content:
            return

        h = html2text.HTML2Text()
        markdown = h.handle(content)

        completion = self.llm.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "From the following markdown content, extract all **delisted items** with the following fields:\n\n"
                        "- `symbol`: the trading symbol or name that was delisted.\n"
                        "- `delisted_time`: the date and time when the item was or will be delisted, in the format `YYYY-MM-DD HH:MM` (24-hour time).\n"
                        "- `product_type`: the type of product (e.g., Spot, Futures, Perpetual).\n\n"
                        "Return the result as a JSON object with the key `delisted_items`, where the value is a list of dictionaries with keys: `symbol`, `delisted_time`, and `product_type`.\n\n"
                        "Do not include any explanations or extra text, only output pure JSON."
                    ),
                },
                {"role": "user", "content": markdown},
            ],
            response_format={"type": "json_object"},
        )

        try:
            result = json.loads(completion.choices[0].message.content)  # pyright: ignore
            if "delisted_items" in result:
                return result["delisted_items"]
        except json.JSONDecodeError:
            pass

        return []

    def download(self):
        announcements = self.announcements()

        delistings = []
        for announcement in announcements:
            result = self.delistings(announcement)
            if result:
                delistings += result

        return delistings

    def close(self):
        self.browser.close()
        self.playwright.stop()
        self.llm.close()


def main():
    delisting_configs = {
        "bybit": {
            "index_url": "https://announcements.bybit.com/en/?category=delistings&page=1",
            "doc_selector": "#article-detail",
        },
        "okx": {
            "index_url": "https://www.okx.com/zh-hans/help/section/announcements-delistings",
            "doc_selector": "#article-container",
        },
        "binance": {
            "index_url": "",
            "doc_selector": "#support_article",
        },
    }
    delistings = {}
    for exchange_name, config in delisting_configs.items():
        downloader = DelistingDownloader(**config)
        delistings[exchange_name] = downloader.download()
        downloader.close()

    print(delistings)
