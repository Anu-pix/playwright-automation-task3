
import pytest
from playwright.async_api import expect

from pages.home_page import HomePage
from pages.product_page import ProductPage
from pages.cart_page import CartPage


@pytest.mark.asyncio
async def test_demowebshop_product_to_cart(browser_page):
    home = HomePage(browser_page)
    product = ProductPage(browser_page)
    cart = CartPage(browser_page)

    # 1. Open home page and verify navigation
    await home.open()

    # 2. Hover over navigation if supported
    books_link = home.books_link
    await expect(books_link).to_be_visible()
    await books_link.hover()

    # 3. Open Books and search for a book
    await home.open_books()
    await home.search_product("Computing and Internet")

    # 4. Autocomplete is optional; use the actual search results
    # if the site does not display a suggestion list.

    # 5. Open product, verify title and price
    await product.open_first_result()
    details = await product.get_details()

    assert details["title"]
    assert details["price"] > 0

    # Add to cart and verify the confirmation
    await product.add_to_cart()

    # Open cart and verify the selected product
    await cart.open()
    await cart.verify_product(details)

    # 6. Right-click a safe product title and verify the event.
    title = product.product_title
    await title.evaluate("""
        element => {
            element.dataset.contextMenuSeen = "false";
            element.addEventListener("contextmenu", () => {
                element.dataset.contextMenuSeen = "true";
            }, { once: true });
        }
    """)
    await title.click(button="right")
    assert await title.get_attribute("data-context-menu-seen") == "true"

    # Double-click and hidden-state interactions can be verified
    # on a local practice page if no meaningful site control exists.
