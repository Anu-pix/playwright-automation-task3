
from playwright.async_api import Page, expect


class HomePage:
    URL = "https://demowebshop.tricentis.com/"

    def __init__(self, page: Page):
        self.page = page
        self.search_box = page.locator("#small-searchterms")
        self.search_button = page.locator(
            "input.button-1.search-box-button"
        )
        self.navigation = page.locator(".header-menu")
        self.books_link = page.get_by_role(
            "link", name="Books", exact=True
        )

    async def open(self):
        await self.page.goto(self.URL, wait_until="domcontentloaded")
        await expect(self.navigation).to_be_visible()

    async def open_books(self):
        await expect(self.books_link).to_be_visible()
        await self.books_link.click()

    async def search_product(self, query: str):
        await expect(self.search_box).to_be_visible()
        await expect(self.search_box).to_be_enabled()
        await self.search_box.fill(query)
        await self.search_button.click()

        results = self.page.locator(".product-item")
        await expect(results.first).to_be_visible(timeout=10000)
