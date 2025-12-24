import os
import io
import re
from time import time
import requests
from PIL import Image
from bs4 import BeautifulSoup
from utils import format_number, save_cbz, file_exists_with_regex
# ### SELENIUM ### - Importações necessárias
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_mangapark_url(manga_name):
    base_url = "https://mangapark.net/apo/"
    body = {"query":"query get_searchComic($select: SearchComic_Select) {\n    get_searchComic(\n      select: $select\n    ) {\n      reqPage reqSize reqSort reqWord\n      newPage\n      paging { \n  total pages page init size skip limit prev next\n }\n      items {\n        id data {\n          id dbStatus name\n          origLang tranLang\n          urlPath urlCover600 urlCoverOri\n          genres altNames authors artists\n          is_hot is_new sfw_result\n          score_val follows reviews comments_total\n          max_chapterNode {\n            id data {\n              id dateCreate\n              dbStatus isFinal sfw_result\n              dname urlPath is_new\n              userId userNode {\n                id data {\n                  id name uniq avatarUrl urlPath\n                }\n              }\n            }\n          }\n        }\n        sser_follow\n        sser_lastReadChap {\n          date chapterNode {\n            id data {\n              id dbStatus isFinal sfw_result\n              dname urlPath is_new\n              userId userNode {\n                id data {\n                  id name uniq avatarUrl urlPath\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }",
        "variables":{"select":{"word":manga_name,"size":10,"page":1,"sortby":"field_name"}}}
    headers = {
        "accept-language": "pt-BR,pt;q=0.9",
        "Cookie": "tfv=1760701601549; theme=mdark; bset=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJiaWQiOiI2OGYyMmRmMzFiOTBjMzBmODZmMmYxZjIiLCJpYXQiOjE3NjIwNzA1MTl9.jt3q9_5gf7vIUXZL83oxlyoaOSSjhP1VPyXc6ibtLD4; cf_clearance=8kBGybs5vmM9HUzF3d1kw6mXptDl.6R7TjkUDN6nxTs-1762074984-1.2.1.1-Hl.GCr.SATp.0tAmeiEWjNHn6kLsgFAwmkXjiRBjXlzrYwQqEkn8lRw.lvBsnnF8Nk34lG_tZX5gX5cRTBgt51BN0tjXOKYcQ33GtAI7gAQdpbnJ_gVPx1_rErQFqv40eFPKNvnClRukLDtrC.45N9vvmV9Gd7HWBpDmE.0qgHTTn5GjsKwAzIC0ExxM4Q7X5T_3esdzB2xVGgPFwJ4zjwOZp._ps90.zPfttq65BZM; wd=513x950"
    }
    response = requests.post(base_url, json=body, headers=headers)
    if response.status_code != 200:
        print(f"Manga '{manga_name}' não encontrado no MangaPark.")
        return None
    data = response.json()
    if len(data["data"]["get_searchComic"]["items"]) == 0:
        return None
    return data["data"]["get_searchComic"]["items"][0]["data"]["urlPath"]

def get_mangapark_chapters(manga_url):
    base_url = "https://mangapark.net"
    full_url = base_url + manga_url
    response = requests.get(full_url)
    if response.status_code != 200:
        print(f"Erro ao acessar {full_url}: Status code {response.status_code}")
        return {}
    soup = BeautifulSoup(response.text, 'lxml')
    div_chapters = soup.find_all(attrs={"data-name": "chapter-list"})[0]
    chapter_links = div_chapters.find_all('a', href=True)
    links = []
    for link in chapter_links:
        chap_name = link.text.strip()
        chap_url = base_url + link['href']
        links.append((chap_name, chap_url))
    links.reverse()
    return dict(links)

def get_mangapark_chapter_images(chapter_url, driver):
    driver.get(chapter_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "images"))
        )
    except Exception as e:
        print(f"  -> Erro ao carregar a página do capítulo: {e}")
        return []
    time.sleep(2)  # Espera extra para garantir que todas as imagens carregaram
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'lxml')
    image_div = soup.find_all(attrs={"id": "images"})[0]
    image_tags = image_div.find_all('img')
    images = []
    print(f"  -> Encontradas {len(image_tags)} páginas. Baixando com 'requests'...")
    for page, img_tag in enumerate(image_tags):
        image_url = img_tag.get("src")
        r = requests.get(image_url)
        if r.status_code == 200:
            img_data = io.BytesIO(r.content)
            img = Image.open(img_data)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        print(f"    -> Página {page + 1} baixada.", end='\r')
    return images

def download_mangapark(manga_path, output_folder_name, driver):
    manga_url = get_mangapark_url(manga_path)
    if not manga_url:
        return
    caps = get_mangapark_chapters(manga_url)
    if not os.path.exists(output_folder_name):
        os.makedirs(output_folder_name, exist_ok=True)
    if len(caps) == len(os.listdir(output_folder_name)):
        print("Todos os capítulos já foram baixados. Saindo.")
        return
    print(f"Encontrados {len(caps)} capítulos.")
    for chap_name, chap_url in caps.items():
        volume_number = re.search(r'Vol.\d+', chap_name)
        if volume_number:
            volume_number = volume_number.group().replace('Vol.', '')
        chap_number = re.search(r'(?:Ch(?:\.|apter)?)\s*(\d+(?:\.\d+)?)', chap_name, re.IGNORECASE)
        if not chap_number:
            print(f"  -> Aviso: Número do capítulo não encontrado em {chap_name}. Pulando.")
            continue
        chap_number = chap_number.group(1)
        if file_exists_with_regex(output_folder_name, fr".*Ch\.{format_number(chap_number)}\.cbz"):
            print(f"Capítulo {chap_name} já existe. Pulando.")
            continue
        print(f"Baixando capítulo: {chap_name}")
        imgs = get_mangapark_chapter_images(chap_url, driver)
        if len(imgs) == 0:
            print(f"  -> Aviso: Nenhuma imagem baixada para o capítulo {chap_name}. Pulando.")
            continue
        save_cbz(imgs, format_number(chap_number), output_folder_name, manga_path, volume_number if not volume_number or volume_number != '0' else None)
