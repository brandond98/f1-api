from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_route():
    return {"Hello": "World"}
