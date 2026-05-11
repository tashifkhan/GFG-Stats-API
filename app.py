from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from config import settings
from core.middleware import CacheRateLimitMiddleware
from models.exceptions import http_exception_handler
from routes import badges, contests, docs, heatmap, legacy, profile, rating, stats, summary, topics

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CacheRateLimitMiddleware, platform="gfg")

app.add_exception_handler(HTTPException, http_exception_handler)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


app.include_router(docs.docs_router)
app.include_router(profile.router)
app.include_router(stats.router)
app.include_router(contests.router)
app.include_router(rating.router)
app.include_router(heatmap.router)
app.include_router(topics.router)
app.include_router(badges.router)
app.include_router(summary.router)
app.include_router(legacy.router)


@app.get("/docs")
async def docs_redirect():
    return RedirectResponse(url="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=58353, reload=True)
