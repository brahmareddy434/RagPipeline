from fastapi import Request

def container(request: Request):
    return request.app.state.container
