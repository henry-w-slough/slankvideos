from .. import logging
from ..models.request import Request
from ..models.responses import ErrorResponse, SuccessResponse, Response

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
            ),

            verify = False
        )

        #note that this is just limited for the sake of the
        #other server. Having 1000 requests at once is a lot harder
        #than having 200 requests 5 times over a time.
        self.semaphore = asyncio.Semaphore(max_requests)


    async def request_batch(self, requests: list[Request], on_result: Callable[[Response], Awaitable[None]]) -> None:
        """Takes the given requests and passes their responses into on_result().
        Note that on_result must take a Response as an argument.
        """
        results = await asyncio.gather(
            *(self.send_request(request) 
              for request in requests
            )
        )
        #iterating after getting results - to ensure order
        for result in results:
            await on_result(result)


    async def send_request(self, request: Request, *args, **kwargs) -> Response:

        response: Response

        try:
            async with self.semaphore:
                http_response: httpx.Response = await self.client.request(
                    request.method,
                    request.url,
                    headers = request.headers,
                    cookies = request.cookies,
                    *args, **kwargs
                )
            http_response.raise_for_status()
            response = SuccessResponse(
                request.url,
                http_response,
            )
        
        except httpx.ConnectError as e:
            response = ErrorResponse(
                request.url,
                error = e,
                error_message = f"Failed to establish connection to '{request.url}'."
            )

        except httpx.ConnectTimeout as e:
            response = ErrorResponse(
                request.url,
                error = e,
                error_message = f"Timed out while trying to connect to '{request.url}'."
            )

        except httpx.ReadTimeout as e:
            response = ErrorResponse(
                request.url,
                error = e,
                error_message = f"Timed out while receiving data from '{request.url}'."
            )

        except httpx.PoolTimeout as e:
            response = ErrorResponse(
                request.url,
                error = e,
                error_message = f"Timed out while trying to acquire connection from connection pool."
            )

        except httpx.HTTPStatusError as e:
            response = ErrorResponse(
                request.url,
                error = e,
                error_message = f"Got {e.response.status_code} while connecting to '{request.url}'."
            )


        except httpx.RequestError as e:
            response = ErrorResponse(
                request.url,
                error = e,
                error_message = f"HTTP request failed to '{request.url}'."
            )


        except Exception as e:
            response = ErrorResponse(
                request.url,
                error = e,
                error_message = f"Caught unexpected exception while connecting to '{request.url}'"
            )


        if isinstance(response, SuccessResponse):
            logging.log(
                f"Request to {request.url} succeeded with response code {response.http_response.status_code}",
                logging.Severity.INFO
            )
        if isinstance(response, ErrorResponse):
            logging.log(
                f"Request to {request.url} raised Exception (type: {type(response.error).__name__}). Message: '{response.error_message}'",
                logging.Severity.ERROR
            )  

        return response


        
















        