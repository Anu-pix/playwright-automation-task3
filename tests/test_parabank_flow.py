
import pytest
from playwright.async_api import expect


@pytest.mark.asyncio
async def test_parabank_home_page_loads(browser_page):
    await browser_page.goto(
        "https://parabank.parasoft.com/parabank/index.htm",
        wait_until="domcontentloaded",
    )

    await expect(
        browser_page.get_by_role(
            "link", name="Register"
        )
    ).to_be_visible()

    await expect(
        browser_page.locator('input[name="username"]')
    ).to_be_visible()

    await expect(
        browser_page.locator('input[name="password"]')
    ).to_be_visible()
