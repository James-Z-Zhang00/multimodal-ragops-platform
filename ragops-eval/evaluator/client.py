import httpx
from typing import Any


class SearchServiceClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def search(self, query: str, session_id: str = "eval") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/search/hybrid",
                json={"query": query, "session_id": session_id, "debug": False},
            )
            response.raise_for_status()
            return response.json()

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/health")
                return r.status_code == 200
        except Exception:
            return False
