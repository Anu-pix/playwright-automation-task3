
import pytest_asyncio
from playwright.async_api import async_playwright


@pytest_asyncio.fixture
async def browser_page():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page(
            viewport={"width": 1440, "height": 900}
        )
        yield page
        await browser.close()


import logging
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright


# Project folders
ROOT_DIR = Path(__file__).resolve().parent
LOG_DIR = ROOT_DIR / "logs"
SCREENSHOT_DIR = ROOT_DIR / "artifacts" / "screenshots"
TRACE_DIR = ROOT_DIR / "artifacts" / "traces"

for folder in (LOG_DIR, SCREENSHOT_DIR, TRACE_DIR):
    folder.mkdir(parents=True, exist_ok=True)


# Timestamped console + file logging
logger = logging.getLogger("playwright_tests")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(
        LOG_DIR / "pytest.log", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def safe_url(url: str) -> str:
    """Remove query strings and fragments before logging URLs."""
    parts = urlsplit(url)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, "", "")
    )


def safe_test_name(nodeid: str) -> str:
    """Make a test ID safe to use in an artifact filename."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call":
        test_logger = logging.getLogger("playwright_tests")

        if report.failed:
            test_logger.error("TEST FAILED: %s", item.nodeid)
            if call.excinfo:
                test_logger.error(
                    "Exception:\n%s", call.excinfo.getrepr()
                )
        elif report.passed:
            test_logger.info("TEST PASSED: %s", item.nodeid)
        elif report.skipped:
            test_logger.warning("TEST SKIPPED: %s", item.nodeid)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    logging.getLogger("playwright_tests").info(
        "TEST START: %s", item.nodeid
    )


@pytest_asyncio.fixture
async def browser_page(request):
    test_name = safe_test_name(request.node.nodeid)
    page = None
    context = None
    tracing_started = False

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1366, "height": 900}
        )

        # Start tracing before the test performs browser actions.
        await context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )
        tracing_started = True

        page = await context.new_page()

        def on_request_failed_response(response):
            if response.status >= 400:
                logger.warning(
                    "HTTP %s | %s | test=%s",
                    response.status,
                    safe_url(response.url),
                    request.node.nodeid,
                )

        page.on("response", on_request_failed_response)

        logger.info("Browser ready | test=%s", request.node.nodeid)

        try:
            yield page
        finally:
            call_report = getattr(request.node, "rep_call", None)
            test_failed = (
                call_report is not None and call_report.failed
            )

            if page is not None:
                logger.info(
                    "Test ending | test=%s | URL=%s",
                    request.node.nodeid,
                    safe_url(page.url),
                )

            if test_failed and page is not None:
                screenshot_path = (
                    SCREENSHOT_DIR / f"{test_name}.png"
                )
                try:
                    await page.screenshot(
                        path=str(screenshot_path),
                        full_page=True,
                    )
                    logger.info(
                        "Failure screenshot saved: %s",
                        screenshot_path,
                    )
                except Exception:
                    logger.exception(
                        "Could not capture failure screenshot"
                    )

            if tracing_started and context is not None:
                try:
                    if test_failed:
                        trace_path = TRACE_DIR / f"{test_name}.zip"
                        await context.tracing.stop(
                            path=str(trace_path)
                        )
                        logger.info(
                            "Failure trace saved: %s", trace_path
                        )
                    else:
                        # Don't keep trace ZIPs for passing tests.
                        await context.tracing.stop()
                except Exception:
                    logger.exception("Could not save/stop trace")

            if context is not None:
                await context.close()
            await browser.close()
