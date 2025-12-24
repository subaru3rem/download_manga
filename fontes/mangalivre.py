import os
import io
import re
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

def get_mangalivre_headers():
    url = os.getenv("FLARESOLVER_URL")
    body = {
        "url": "https://mangalivre.tv/",
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

def get_mangalivre_url(manga_name):
    url = "https://mangalivre.tv/wp-admin/admin-ajax.php"
    body = {
        "action":"wp-manga-search-manga",
        "title":manga_name

    }
    requests_headers = get_mangalivre_headers()
    if requests_headers == None:
        return None

    res = requests.post(url, headers=requests_headers, data=body)
    if res.status_code != 200:
        print(f"Erro ao pegar url do manga {manga_name}: Status code {res.status_code}")
        return None

    data = res.json()
    if len(data["data"]) <= 0 or not data["success"]:
        print("Obra nao encontrada no manga livre")
        return None
    
    return data["data"][0]["url"]

def get_mangalivre_chapters(url):
        url = f"{url}ajax/chapters/?t=1"
        requests_headers = get_mangalivre_headers()
        if requests_headers == None:
            print("Erro ao pegar headers do manga livre")
            return None
        req = requests.post(url, headers=requests_headers)
        if req.status_code != 200:
            print(f"Erro ao pegar capítulos do manga: Status code {req.status_code}")
            return None
        
        html_content = req.text
        soup = BeautifulSoup(html_content, 'lxml')
        chapter_elements = soup.find_all('li', class_='wp-manga-chapter')

        if not chapter_elements:
            print(f"Nenhum capítulo encontrado. O HTML foi carregado, mas a classe wp-manga-chapter não foi encontrada.")
            return {}

        # O resto da lógica de extração de capítulos é a mesma
        chapters = {
            link_tag.text.strip(): link_tag['href']
            for element in chapter_elements
            if (link_tag := element.find('a')) and 'href' in link_tag.attrs
        }
        chapters = dict(reversed(list(chapters.items())))
        return chapters

def get_mangalivre_chapter_images(chapter_url, chapter_name, driver):
    cookie = get_mangalivre_headers()["Cookie"]
    if cookie == None:
        return []
    driver.get(chapter_url)
    cookies = [c.strip() for c in cookie.split(';')]
    for cookie in cookies:
        name, value = cookie.split("=", 1)
        driver.add_cookie({"name": name, "value": value})
    driver.refresh()
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "page-break"))
        )
    except Exception as e:
        print(f"  -> Erro ao carregar a página do capítulo: {e}")
        return []

    html_content = driver.page_source
    chap_soup = BeautifulSoup(html_content, 'lxml')
    image_divs = chap_soup.find_all('div', class_='page-break no-gaps')
    if not image_divs:
        print(f"  -> Aviso: Nenhuma imagem encontrada para o capítulo {chapter_name}. Pulando.")
        return
    image_urls = [
        div.find('img')['src'].strip()
        for div in image_divs if div.find('img') and 'src' in div.find('img').attrs
    ]
    print(f"  -> Encontradas {len(image_urls)} páginas. Baixando com 'requests'...")
    
    images_for_current_pdf = []
    for page_num, image_url in enumerate(image_urls):
        try:
            image_response = requests.get(image_url, timeout=20)
            image_response.raise_for_status()
            img_response = image_response.content
            
            image_data = io.BytesIO(img_response)
            image = Image.open(image_data)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            images_for_current_pdf.append(image)
            print(f"    -> Página {page_num + 1} baixada.", end='\r')
        except requests.exceptions.RequestException as e:
            print(f"    -> Erro ao baixar a imagem {image_url}: {e}")
        except IOError:
            print(f"    -> Erro: O conteúdo de {image_url} não é uma imagem válida.")
    print("\n  -> Download do capítulo concluído.")
    return images_for_current_pdf

def download_mangalivre(manga_path, output_folder_name, driver):
    url = get_mangalivre_url(manga_path)
    if url == None:
        return
    caps = get_mangalivre_chapters(url)
    if not os.path.exists(output_folder_name):
        os.makedirs(output_folder_name, exist_ok=True)
    if caps == None:
        return
    if len(caps) == len(os.listdir(output_folder_name)):
        print("Todos os capítulos já foram baixados. Saindo.")
        return
    print(f"Encontrados {len(caps)} capítulos.")
    for chap_name, chap_url in caps.items():
        chap_number = re.search(r'\d+(?:\.\d+)?', chap_name).group()
        if file_exists_with_regex(output_folder_name, fr".*Ch\.{format_number(chap_number)}\.cbz"):
            print(f"Capítulo {chap_name} já existe. Pulando.")
            continue
        print(f"Baixando capítulo: {chap_name}")
        imgs = get_mangalivre_chapter_images(chap_url, chap_name, driver)
        if imgs == None or len(imgs) == 0:
            print(f"  -> Aviso: Nenhuma imagem baixada para o capítulo {chap_name}. Pulando.")
            continue
        save_cbz(imgs, f"{format_number(chap_number)}", output_folder_name, manga_path)
