
import re
from pathlib import Path

from playwright.async_api import Page, expect


class AmazonPage:
    def __init__(self, page: Page):
        self.page = page
        self.search_box = page.get_by_role(
            "searchbox", name=re.compile("search", re.I)
        )
        self.search_button = page.get_by_role(
            "button", name=re.compile("search", re.I)
        )
        self.account_nav = page.locator("#nav-link-accountList")
        self.account_menu = page.locator("#nav-flyout-accountList")
        self.search_results = page.locator(
            '[data-component-type="s-search-result"]'
        )
        self.product_title = page.locator("#productTitle")
        self.product_price = page.locator(
            ".a-price .a-offscreen"
        )

    async def open_home(self):
        await self.page.goto(
            "https://www.amazon.in/",
            wait_until="domcontentloaded",
        )
        await expect(self.page.locator("body")).to_be_visible()

    async def hover_account_menu(self) -> bool:
        if await self.account_nav.count() == 0:
            return False

        await expect(self.account_nav).to_be_visible()
        await self.account_nav.hover()

        # The flyout may be unavailable in some sessions/layouts.
        if await self.account_menu.count() > 0:
            try:
                await expect(self.account_menu).to_be_visible(
                    timeout=3000
                )
                return True
            except AssertionError:
                pass

        return False

    async def search_product(self, query: str):
        await expect(self.search_box).to_be_visible()
        await expect(self.search_box).to_be_enabled()
        await self.search_box.fill(query)

        # Suggestions are dynamic. Choose one only if it appears.
        suggestions = self.page.locator(
            '[role="option"], .s-suggestion'
        )
        if await suggestions.count() > 0:
            try:
                await expect(suggestions.first).to_be_visible(
                    timeout=2000
                )
            except AssertionError:
                pass

        # Submit the unique query instead of relying on a
        # suggestion that may not be present in every session.
        await self.search_button.click()
        await expect(self.search_results.first).to_be_visible(
            timeout=15000
        )

    async def open_first_product(self):
        product_link = self.search_results.first.get_by_role(
            "heading"
        ).get_by_role("link")

        await expect(product_link).to_be_visible()
        await product_link.click()
        await expect(self.product_title).to_be_visible()

    async def get_product_details(self) -> dict:
        title = (await self.product_title.inner_text()).strip()

        price = ""
        if await self.product_price.count() > 0:
            price = (
                await self.product_price.first.inner_text()
            ).strip()

        return {"title": title, "price": price}

    async def save_product_screenshot(self, path: Path):
        await expect(self.product_title).to_be_visible()
        await self.page.screenshot(
            path=str(path),
            full_page=True,
        )
