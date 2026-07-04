"""Main application entry point."""
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from ai_gateway.api.router import router
from ai_gateway.config.settings import get_settings

load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(title="AI Gateway API", description="Multi-provider LLM gateway with routing, caching, rate limiting, and billing", version="1.0.0")
    app.include_router(router)
    return app

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("ai_gateway.main:app", host=settings.api.host, port=settings.api.port, reload=settings.api.reload)
