from urllib.parse import unquote, parse_qs, quote

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")

APPS_CONFIG = {
    "ios": [
        {
            "name": "Streisand",
            "desc": "Как нативное приложение от Apple. Простой и стильный.",
            "deep_link_scheme": "streisand://import?url=",
            "store_link": "https://apps.apple.com/us/app/streisand/id6450534064"
        },
        {
            "name": "FoXray",
            "desc": "Стильный клиент с поддержкой темной темы.",
            "deep_link_scheme": "foxray://install-sub?url=",
            "store_link": "https://apps.apple.com/us/app/foxray/id6448898396"
        },
        {
            "name": "Happ",
            "desc": "Универсальный и минималистичный клиент.",
            "deep_link_scheme": "happ://add-sub?url=",
            "store_link": "https://apps.apple.com/us/app/happ-proxy-utility/id6468994784"
        },
        {
            "name": "Loon",
            "desc": "Элита прокси. Мощнейшие правила и статистика (Платное).",
            "deep_link_scheme": "loon://import?url=",
            "store_link": "https://apps.apple.com/us/app/loon/id1373567447"
        }
    ],
    "android": [
        {
            "name": "Surfboard",
            "desc": "Лидер по красоте на Android. Material Design.",
            "deep_link_scheme": "surfboard://import-url?url=",
            "store_link": "https://play.google.com/store/apps/details?id=com.getsurfboard"
        },
        {
            "name": "Hiddify",
            "desc": "Простой интерфейс в стиле «одна большая кнопка».",
            "deep_link_scheme": "hiddify://import/",
            "store_link": "https://play.google.com/store/apps/details?id=app.hiddify.com"
        },
        {
            "name": "Karing",
            "desc": "Простой и чистый интерфейс без перегруженных меню.",
            "deep_link_scheme": "karing://install-config?url=",
            "store_link": "https://play.google.com/store/apps/details?id=com.karing.app"
        },
        {
            "name": "Happ",
            "desc": "Универсальный и минималистичный клиент.",
            "deep_link_scheme": "happ://add-sub?url=",
            "store_link": "https://play.google.com/store/apps/details?id=com.happ.proxy"
        },
        {
            "name": "v2rayNG",
            "desc": "Самый популярный классический суровый клиент.",
            "deep_link_scheme": "v2rayng://install-config?url=",
            "store_link": "https://play.google.com/store/apps/details?id=com.v2ray.ang"
        }
    ],
    "windows": [
        {
            "name": "Clash Verge Rev",
            "desc": "Самый красивый клиент для ПК. Великолепный интерфейс.",
            "deep_link_scheme": "clash-verge://install-config?url=",
            "store_link": "https://github.com/clash-verge-rev/clash-verge-rev/releases"
        },
        {
            "name": "Hiddify",
            "desc": "Свежий вид на ПК. Ничего лишнего.",
            "deep_link_scheme": "hiddify://import/",
            "store_link": "https://github.com/hiddify/hiddify-next/releases"
        },
        {
            "name": "Happ",
            "desc": "Универсальный и минималистичный клиент.",
            "deep_link_scheme": "happ://add-sub?url=",
            "store_link": "https://github.com/happ-proxy/happ/releases"
        },
        {
            "name": "v2rayN",
            "desc": "Классический мощный клиент для Windows.",
            "deep_link_scheme": "v2rayn://install-config?url=",
            "store_link": "https://github.com/2dust/v2rayN/releases"
        }
    ],
    "mac": [
        {
            "name": "Clash Verge Rev",
            "desc": "Самый красивый клиент с поддержкой графиков.",
            "deep_link_scheme": "clash-verge://install-config?url=",
            "store_link": "https://github.com/clash-verge-rev/clash-verge-rev/releases"
        },
        {
            "name": "Streisand",
            "desc": "Идеально вписывается в экосистему macOS.",
            "deep_link_scheme": "streisand://import?url=",
            "store_link": "https://apps.apple.com/us/app/streisand/id6450534064"
        },
        {
            "name": "FoXray",
            "desc": "Стильный клиент с удобным управлением подписками.",
            "deep_link_scheme": "foxray://install-sub?url=",
            "store_link": "https://apps.apple.com/us/app/foxray/id6448898396"
        },
        {
            "name": "Hiddify",
            "desc": "Простой интерфейс в стиле «одна большая кнопка».",
            "deep_link_scheme": "hiddify://import/",
            "store_link": "https://github.com/hiddify/hiddify-next/releases"
        },
        {
            "name": "Happ",
            "desc": "Универсальный и минималистичный клиент.",
            "deep_link_scheme": "happ://add-sub?url=",
            "store_link": "https://apps.apple.com/us/app/happ-proxy-utility/id6468994784"
        }
    ]
}


@router.get("/connect", response_class=HTMLResponse)
async def connect_redirect(
        request: Request,
        os: str = Query(...)
):
    platform_key = os.lower()
    apps = APPS_CONFIG.get(platform_key, [])

    raw_query = request.url.query
    parsed_params = parse_qs(raw_query)

    link_value = ""
    for key, values in parsed_params.items():
        if key.lower() == "link" and values:
            link_value = values[0]
            break

    decoded_link = link_value
    while "%" in decoded_link:
        previous = decoded_link
        decoded_link = unquote(decoded_link)
        if previous == decoded_link:
            break

    encoded_inner_link = quote(decoded_link, safe="")

    prepared_apps = []
    for app in apps:
        deep_link = app['deep_link_scheme'] + encoded_inner_link

        if "clash" in deep_link:
            deep_link += "&name=UruruVPN"

        prepared_apps.append({
            "name": app["name"],
            "desc": app["desc"],
            "deep_link": deep_link,
            "store_link": app["store_link"]
        })

    os_display_names = {
        "ios": "iOS (iPhone / iPad)",
        "android": "Android",
        "windows": "Windows",
        "mac": "macOS"
    }

    os_title = os_display_names.get(platform_key, platform_key.capitalize())

    return templates.TemplateResponse(
        request=request,
        name="connect.html",
        context={
            "apps": prepared_apps,
            "os_name": os_title,
            "sub_link": decoded_link
        }
    )