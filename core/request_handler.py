from .. import logging
from ..models.request import Request
from ..models.responses import Response

from typing import Callable, Awaitable
import asyncio
import httpx


class RequestHandler:


    def __init__(self, max_connections: int = 200, max_requests: int = 100):
        """Handles all HTTP requests and error handling for requests."""

        self.client = httpx.AsyncClient(
            limits = httpx.Limits(
                max_connections = max_connections,
                max_keepalive_connections = max_connections // 2
            )
        )

        #note that this is just limited for the sake of the
        #other server. Having 1000 requests at once is a lot harder
        #than having 200 requests 5 times over a time.
        self.semaphore = asyncio.Semaphore(max_requests)


    async def get_response_batch(self, requests: list[Request], on_result: Callable[[Response], Awaitable[None]]) -> None:
        """Takes the given requests and passes their results into on_result().
        Note that on_result must take a Response as an argument
        """
        results = await asyncio.gather(
            *(self.send_request(request.url, request.method, headers=request.headers) 
              for request in requests
            )
        )
        #iterating after getting results - to ensure order
        for result in results:
            await on_result(result)


    async def send_request(self, url: str, method: str, *args, headers: dict[str, str], **kwargs) -> Response:
        
        try:
            async with self.semaphore:
                response: httpx.Response = await self.client.request(
                    method,
                    url,
                    headers = headers,
                    *args, **kwargs
                )
            response.raise_for_status()
            return Response(
                True,
                url,
                response,
            )
        
        except httpx.ConnectError as e:
            return Response(
                False,
                url,
                error = e,
                error_message = f"Failed to establish connection to '{url}'."
            )

        except httpx.ConnectTimeout as e:
            return Response(
                False,
                url,
                error = e,
                error_message = f"Timed out while trying to connect to '{url}'."
            )

        except httpx.ReadTimeout as e:
            return Response(
                False,
                url,
                error = e,
                error_message = f"Timed out while receiving data from '{url}'."
            )

        except httpx.PoolTimeout as e:
            return Response(
                False,
                url,
                error = e,
                error_message = f"Timed out while trying to acquire connection from connection pool."
            )

        except httpx.HTTPStatusError as e:
            return Response(
                False,
                url,
                error = e,
                error_message = f"Got {e.response.status_code} while connecting to '{url}'."
            )


        except httpx.RequestError as e:
            return Response(
                False,
                url,
                error = e,
                error_message = f"HTTP request failed to '{url}'."
            )


        except Exception as e:
            return Response(
                False,
                url,
                error = e,
                error_message = f"Caught unexpected exception while connecting to '{url}'"
            )


        
















        