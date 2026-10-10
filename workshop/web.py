"""Public web fetches and an isolated Playwright browser, without personal profiles."""
import asyncio
import ipaddress
import socket
from urllib.parse import urlparse, urljoin, quote
import httpx
from bs4 import BeautifulSoup
from .core import path


async def public_url(url: str) -> str:
    """Reject non-HTTP URLs, credentials and hosts resolving to nonpublic addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Use an HTTP(S) URL without embedded credentials")
    answers = await asyncio.to_thread(socket.getaddrinfo, parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    if not answers or any(not ipaddress.ip_address(answer[4][0]).is_global for answer in answers):
        raise ValueError("Public web tools do not access local/private network addresses")
    return url


async def fetch(url: str) -> dict:
    """Fetch bounded HTML/text, checking each redirect; expose links and readable text."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=False, trust_env=False) as client:
        for _ in range(6):
            await public_url(url)
            async with client.stream("GET", url, headers={"User-Agent": "Workshop/0.1"}) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if "html" not in content_type and not content_type.startswith("text/"):
                    raise ValueError("Fetch supports HTML/text; use a document-specific reader for binary data")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 2_000_000:
                        raise ValueError("Page exceeds the 2 MB limit")
                soup = BeautifulSoup(bytes(body), "html.parser")
                links = [{"text": a.get_text(" ", strip=True), "url": urljoin(url, a["href"])} for a in soup.select("a[href]")][:100]
                for tag in soup.select("script,style,nav,footer"):
                    tag.decompose()
                return {"url": url, "title": soup.title.get_text() if soup.title else "", "text": soup.get_text("\n", strip=True)[:40000], "links": links}
        raise ValueError("Too many redirects")


class Browser:
    """One persistent isolated context per server process; serialize operations."""
    def __init__(self):
        self.runtime = None
        self.browser = None
        self.page = None
        self.lock = asyncio.Lock()

    async def start(self):
        if self.page is not None:
            return
        from playwright.async_api import async_playwright
        self.runtime = await async_playwright().start()
        try:
            self.browser = await self.runtime.chromium.launch(headless=True)
            context = await self.browser.new_context(accept_downloads=False, service_workers="block")
            async def guard(route):
                try:
                    await public_url(route.request.url)
                except Exception:
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", guard)
            self.page = await context.new_page()
        except Exception:
            await self.runtime.stop()
            self.runtime = None
            raise

    async def state(self):
        return {"url": self.page.url, "title": await self.page.title(),
                "text": (await self.page.locator("body").inner_text())[:30000],
                "links": await self.page.locator("a[href]").evaluate_all("els => els.slice(0,100).map(e => ({text:e.innerText,url:e.href}))"),
                "inputs": await self.page.locator("input,textarea,button").evaluate_all("els => els.slice(0,100).map(e => ({tag:e.tagName,type:e.type,name:e.name,id:e.id,text:e.innerText,placeholder:e.placeholder}))")}

    async def action(self, action: str, url: str = "", selector: str = "", value: str = "", output: str = "") -> dict:
        if action not in {"open", "read", "click", "fill", "screenshot", "close"}:
            raise ValueError("Unknown browser action")
        async with self.lock:
            if action == "close":
                if self.browser:
                    await self.browser.close()
                if self.runtime:
                    await self.runtime.stop()
                self.browser = self.runtime = self.page = None
                return {"closed": True}
            await self.start()
            if action == "open":
                await public_url(url)
                await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            elif action == "click":
                await self.page.locator(selector).click(timeout=10000)
                await self.page.wait_for_load_state("domcontentloaded")
            elif action == "fill":
                await self.page.locator(selector).fill(value, timeout=10000)
            elif action == "screenshot":
                target = path(output, new=True)
                if target.suffix.lower() != ".png":
                    raise ValueError("Screenshots require .png")
                await self.page.screenshot(path=str(target), full_page=True)
                return {"path": str(target), "url": self.page.url}
            return await self.state()


browser = Browser()


async def search(query: str) -> dict:
    """Search with an owner-supplied Brave key, otherwise open DuckDuckGo in the browser."""
    import os
    key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if key:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response = await client.get("https://api.search.brave.com/res/v1/web/search", params={"q": query, "count": 10}, headers={"X-Subscription-Token": key})
            response.raise_for_status()
            return {"results": response.json().get("web", {}).get("results", [])}
    return await browser.action("open", url="https://duckduckgo.com/?q=" + quote(query))
