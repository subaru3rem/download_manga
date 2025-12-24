import os
import requests

def get_sakura_headers():
    url = os.getenv("FLARESOLVER_URL")
    body = {
        "url": "https://sakuramangas.org/",
        "maxTimeout": 60000, 
        "cmd": "request.get"
    }
    res = requests.post(url, json=body)
    if res.status_code != 200:
        print(f"Erro ao pegar token do manga livre: Status code {res.status_code}")
        return None
    data = res.json()
    if data["status"] != "ok":
        print(f"Erro ao pegar headers do manga livre: Status code {data['status']}")
        return None
    headers = {
        "User-Agent": data["solution"]["userAgent"],
        "Cookie": "cf_clearance="+data["solution"]["cookies"][0]["value"]
    }
    return headers


def get_sakura_url(manga_name):
    url = "https://sakuramangas.org/dist/sakura/global/sidebar/sidebar.php"
    param = {
        "q": manga_name
    }
    requests_headers = get_sakura_headers()
    if requests_headers == None:
        return None
    res = requests.get(url, headers=requests_headers, params=param)
    if res.status_code != 200:
        print(f"Erro ao pegar url do manga {manga_name}: Status code {res.status_code}")
        return None
    data = res.json()
    if len(data) <= 0:
        print("Obra nao encontrada no sakura mangas")
        return None
    
    return "https://sakuramangas.org" + data[0]["url"]