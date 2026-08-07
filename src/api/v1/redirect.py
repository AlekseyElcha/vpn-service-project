from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")

@router.get("/connect", response_class=HTMLResponse)
async def connect_redirect(request: Request, os: str, link: str):
    deep_link = link
    
    if os.lower() == "ios":
        deep_link = f"streisand://import/{link}"
    elif os.lower() == "android":
        deep_link = f"v2rayng://install-config?url={link}"

    return templates.TemplateResponse(
        request=request,
        name="connect.html",
        context={"deep_link": deep_link}
    )
