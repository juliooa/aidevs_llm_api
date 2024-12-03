import httpx


POST = "POST"
GET = "GET"
PATCH = "PATCH"
DELETE = "DELETE"


class HTTPXClientWrapper:
    async_client = None

    def start(self):
        self.async_client = httpx.AsyncClient(timeout=60.0)

    async def stop(self):
        if self.async_client is None:
            return
        await self.async_client.aclose()
        self.async_client = None

    def __call__(self):
        assert self.async_client is not None
        return self.async_client


httpx_client_wrapper = HTTPXClientWrapper()
