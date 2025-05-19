from fastapi import Request
from fastapi.responses import JSONResponse


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Unexpected error: {e}")
        return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})
