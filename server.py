import base64
import hmac
import hashlib
import json
from typing import Optional


#                  чтение из формы и Куки
from fastapi import FastAPI, Form, Cookie, Body
from fastapi.responses import Response

app = FastAPI() # экземпрляр app

SECRET_KEY = "365ddca1aa8e9ad53a9f08a10e57b54fb8da09adf1f7e738b67135c8b68328a7"
PASSWORD_SALT = "2149f00a060614b09da61c774e756e7aaafbfd53f51da29464d808fb8d8af63c"


def sign_data(data: str) -> str:
    """ф-я которая подписывает данные"""
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    usernsme_base64, sign = username_signed.split(".")
    username = base64.b64decode(usernsme_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def verify_password(username: str, password: str) -> bool:
    password_hash = hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest().lower()
    stored_password_hash = users[username]["password"].lower()
    return password_hash == stored_password_hash


users = {
    "alexey@user.com": {
        "name": "Алексей",
        "password": "7207b3c696c0bd7e9efc5092a537f8d0b9b36686b056b576440ea64492049670",
        "balance": 100_000
    },
    "petr@user.com": {
        "name": "Петр",
        "password": "8fedc78c33c53d75e56512afdba13017e7936437fbd449868537b7ba64502b00",
        "balance": 555_555
    }
}


@app.get("/") # главная страничка
def index_page(username: Optional[str] = Cookie(default=None)): 
    with open('templates/login.html', 'r') as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type="text/html")
    valid_username = get_username_from_signed_string(username)
    if not valid_username: # если подпись не валидна
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="usernsme") # удаляем куку
        return response
    # проверка пользователя которого у нас нет если поменяны куки
    try:            
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="usernsme") # удаляем куку если не наша установлена
        return response
    return Response(
        f"Привет, {users[valid_username]['name']}!<br />"\
        f"Баланс: {users[valid_username]['balance']}"
        , media_type="text/html")


@app.post("/login") # прием с бэкэнд
def process_login_page(data: dict = Body(...)):
    username = data["username"]
    password = data["password"]
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "Я вас не знаю!"
            }),
            media_type="application/json")

    response = Response(
        json.dumps({
            "success": True,
            "message": f"Привет {user['name']}!<br />Баланс {user['balance']}"
        }),
         media_type='application/json')

    username_signed = base64.b64encode(username.encode()).decode() + "." + \
        sign_data(username)
    response.set_cookie(key="username", value=username_signed)
    return response

