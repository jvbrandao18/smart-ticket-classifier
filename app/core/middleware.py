from uuid import uuid4

from fastapi import FastAPI, Request


CORRELATION_ID_HEADER = "X-Correlation-ID"


def register_middlewares(application: FastAPI) -> None:
    @application.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response

