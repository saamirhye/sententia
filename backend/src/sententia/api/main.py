from fastapi import FastAPI

from sententia.api.routes import router

app = FastAPI(title="Sententia")
app.include_router(router)
