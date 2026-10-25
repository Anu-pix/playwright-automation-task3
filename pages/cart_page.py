
from playwright.async_api import Page, expect


class CartPage:
    def __init__(self, page: Page):
        self.page = page
        self.cart_link = page.locator("a.ico-cart")
        self.cart_rows = page.locator("tr.cart-item-row")

    async def open(self):
        await expect(self.cart_link).to_be_visible()
        await self.cart_link.click()
        await expect(self.page).to_have_url(
            "https://demowebshop.tricentis.com/cart"
        )

    async def verify_product(self, expected_product: dict):
        await expect(self.cart_rows.first).to_be_visible()

        row = self.cart_rows.filter(
            has=self.page.get_by_role(
                "link", name=expected_product["title"], exact=True
            )
        ).first

        await expect(row).to_be_visible()
