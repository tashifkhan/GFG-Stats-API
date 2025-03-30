from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Global handler for HTTPException that formats the response consistently
    """
    endpoint = request.url.path.split("/")[-1]
    if not endpoint or endpoint.isdigit():
        endpoint = "stats"
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "endpoint": endpoint
        }
    )
