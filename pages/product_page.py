
import re
from playwright.async_api import Page, expect


class ProductPage:
    def __init__(self, page: Page):
        self.page = page
        self.product_title = page.locator(".product-name h1")
        self.product_price = page.locator(".product-price")
        self.add_to_cart_button = page.locator(
            "input[id^='add-to-cart-button-']"
        )
        self.cart_notification = page.locator(
            ".bar-notification"
        )

    async def open_first_result(self):
        product_link = self.page.locator(
            ".product-item h2 a"
        ).first
        await expect(product_link).to_be_visible()
        await product_link.click()
        await expect(self.product_title).to_be_visible()

    async def get_details(self) -> dict:
        title = (await self.product_title.inner_text()).strip()
        price_text = (await self.product_price.inner_text()).strip()

        match = re.search(r"[\d,]+(?:\.\d{1,2})?", price_text)
        assert match, f"Could not read product price: {price_text}"

        return {
            "title": title,
            "price": float(match.group().replace(",", "")),
        }

    async def add_to_cart(self):
        await expect(self.add_to_cart_button).to_be_visible()
        await expect(self.add_to_cart_button).to_be_enabled()
        await self.add_to_cart_button.click()
        await expect(self.cart_notification).to_be_visible()
