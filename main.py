import os
import sys
import requests
import io
import re
import time
import base64
from bs4 import BeautifulSoup
from PIL import Image
from dotenv import load_dotenv
import zipfile

# ### SELENIUM ### - Importações necessárias
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

def format_number(number: str):
    if "." in number:
        inteiro, decimal = number.split(".")
        formatted = f"{int(inteiro):02}.{decimal}"
    elif "," in number:
        inteiro, decimal = number.split(".")
        formatted = f"{int(inteiro):02}.{decimal}"
    else:
        formatted = f"{int(number):02}"
    
    return formatted


def file_exists_with_regex(directory, pattern):
    """
    Checks if any file in the given directory matches the provided regex pattern.

    Args:
        directory (str): The path to the directory to search.
        pattern (str): The regular expression pattern to match filenames against.

    Returns:
        bool: True if at least one file matches the pattern, False otherwise.
    """
    try:
        # Compile the regex pattern for efficiency
        regex = re.compile(pattern)
        if pattern == r'.*Ch\.02.5\.cbz':
            pass
        
        # List all files and directories in the given directory
        for filename in os.listdir(directory):
            # Check if the filename matches the regex pattern
            if regex.match(filename):
                return True
        return False
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def save_cbz(images, chapter_number, output_folder, manga_name, volume_number=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    cbz_filename = f"{manga_name} {f'Vol.{volume_number} ' if volume_number != None else ''}Ch.{chapter_number}.cbz"
    cbz_path = os.path.join(output_folder, cbz_filename)
    with zipfile.ZipFile(cbz_path, 'w') as cbz:
        for idx, img in enumerate(images):
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            cbz.writestr(f"{idx+1:03d}.jpg", img_bytes.read())
    return cbz_filename

def getmangalivrechapters(manga_name):
     # ### SELENIUM ### - Usa o driver para abrir a página
        cookie = os.getenv("MANGA_LIVRE_COOKIE")
        User_Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        url = f"https://mangalivre.tv/manga/{manga_name}/ajax/chapters/?t=1"
        requests_headers = {
            "User-Agent": User_Agent,
            "Cookie": cookie
        }
        req = requests.post(url, headers=requests_headers)
        if req.status_code != 200:
            print(f"Erro ao acessar {url}: Status code {req.status_code}")
            return {}
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

def getmangalivrechaptersimg(chapter_url, chapter_name):
    cookie = os.getenv("MANGA_LIVRE_COOKIE")
    User_Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    requests_headers = {
        "User-Agent": User_Agent,
        "Cookie": cookie
    }
    req = requests.post(chapter_url, headers=requests_headers)
    if req.status_code != 200:
        print(f"Erro ao acessar {chapter_url}: Status code {req.status_code}")
        return {}
    html_content = req.text
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

def download_mangalivre(manga_path, output_folder_name):
    manga_name = manga_path.replace(' ', '-').lower()
    caps = getmangalivrechapters(manga_name)
    if not os.path.exists(output_folder_name):
        os.makedirs(output_folder_name, exist_ok=True)
    if len(caps) == len(os.listdir(output_folder_name)):
        print("Todos os capítulos já foram baixados. Saindo.")
        return
    print(f"Encontrados {len(caps)} capítulos.")
    for chap_name, chap_url in caps.items():
        chap_number = re.search(r'\d+(?:\.\d+)?', chap_name).group()
        if file_exists_with_regex(output_folder_name, fr".*Ch\.{chap_number:02}\.cbz"):
            print(f"Capítulo {chap_name} já existe. Pulando.")
            continue
        print(f"Baixando capítulo: {chap_name}")
        imgs = getmangalivrechaptersimg(chap_url, chap_name)
        if len(imgs) == 0:
            print(f"  -> Aviso: Nenhuma imagem baixada para o capítulo {chap_name}. Pulando.")
            continue
        save_cbz(imgs, f"{chap_number:02}", output_folder_name, manga_path)

def get_mangadex_id(manga_name):
    search_url = f"https://api.mangadex.org/manga?title={manga_name}&limit=1"
    response = requests.get(search_url)
    if response.status_code != 200:
        print(f"Erro ao buscar manga ID: Status code {response.status_code}")
        return None
    data = response.json()
    if data["result"] == "ok" and data["data"]:
        return data["data"][0]["id"]
    return None

def get_mangadex_chapters(manga_id):
    chapters_url = f"https://api.mangadex.org/manga/{manga_id}/feed?translatedLanguage[]=pt-br"
    response = requests.get(chapters_url)
    if response.status_code != 200:
        print(f"Erro ao buscar capítulos: Status code {response.status_code} - {response.text}")
        return {}
    data = response.json()
    chapters = [
        (chapter["attributes"]["chapter"], chapter["id"], chapter["attributes"]["volume"]) for chapter in data["data"]
    ]
    return chapters

def get_mangadex_chapter_images(chapter_id):
    images_url = f"https://api.mangadex.org/at-home/server/{chapter_id}"
    response = requests.get(images_url)
    if response.status_code != 200:
        print(f"Erro ao buscar imagens do capítulo: Status code {response.status_code}")
        return []
    data = response.json()
    url = data["baseUrl"]
    images = []

    print(f"  -> Encontradas {len(data['chapter']['data'])} páginas. Baixando com 'requests'...")
    for page, dt in enumerate(data["chapter"]["data"]):
        r = requests.get(f"{url}/data/{data['chapter']['hash']}/{dt}")
        if r.status_code == 200:
            img_data = io.BytesIO(r.content)
            img = Image.open(img_data)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        print(f"    -> Página {page + 1} baixada.", end='\r')
        
    return images

def download_mangadex(manga_path, output_folder_name):
    get_id = get_mangadex_id(manga_path)
    if not get_id:
        print(f"Manga '{manga_path}' não encontrado no MangaDex.")
        return
    caps = get_mangadex_chapters(get_id)
    if not os.path.exists(output_folder_name):
        os.makedirs(output_folder_name, exist_ok=True)
    if len(caps) == len(os.listdir(output_folder_name)):
        print("Todos os capítulos já foram baixados. Saindo.")
        return
    print(f"Encontrados {len(caps)} capítulos.")
    for chap_number, chap_id, chap_vol in caps:
        if file_exists_with_regex(output_folder_name, fr".*Ch\.{int(chap_number):02}\.cbz"):
            print(f"Capítulo {chap_number} já existe. Pulando.")
            continue
        print(f"Baixando capítulo: {chap_number}")
        cap_imgs = get_mangadex_chapter_images(chap_id)
        if len(cap_imgs) == 0:
            print(f"  -> Aviso: Nenhuma imagem baixada para o capítulo {chap_number}. Pulando.")
            continue
        save_cbz(cap_imgs, f"{int(chap_number):02}", output_folder_name, manga_path, chap_vol if chap_vol or chap_vol != '0' else None)
        print(f"  -> Download do capítulo {chap_number} concluído.")
    
def get_mangapark_url(manga_name):
    base_url = "https://mangapark.net/apo/"
    body = {"query":"query get_searchComic($select: SearchComic_Select) {\n    get_searchComic(\n      select: $select\n    ) {\n      reqPage reqSize reqSort reqWord\n      newPage\n      paging { \n  total pages page init size skip limit prev next\n }\n      items {\n        id data {\n          id dbStatus name\n          origLang tranLang\n          urlPath urlCover600 urlCoverOri\n          genres altNames authors artists\n          is_hot is_new sfw_result\n          score_val follows reviews comments_total\n          max_chapterNode {\n            id data {\n              id dateCreate\n              dbStatus isFinal sfw_result\n              dname urlPath is_new\n              userId userNode {\n                id data {\n                  id name uniq avatarUrl urlPath\n                }\n              }\n            }\n          }\n        }\n        sser_follow\n        sser_lastReadChap {\n          date chapterNode {\n            id data {\n              id dbStatus isFinal sfw_result\n              dname urlPath is_new\n              userId userNode {\n                id data {\n                  id name uniq avatarUrl urlPath\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }",
"variables":{"select":{"word":manga_name,"size":10,"page":1,"sortby":"field_score"}}}
    headers = {
        "accept-language": "pt-BR,pt;q=0.9",
        "Cookie": "tfv=1760701601549; theme=mdark; bset=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJiaWQiOiI2OGYyMmRmMzFiOTBjMzBmODZmMmYxZjIiLCJpYXQiOjE3NjIwNzA1MTl9.jt3q9_5gf7vIUXZL83oxlyoaOSSjhP1VPyXc6ibtLD4; cf_clearance=8kBGybs5vmM9HUzF3d1kw6mXptDl.6R7TjkUDN6nxTs-1762074984-1.2.1.1-Hl.GCr.SATp.0tAmeiEWjNHn6kLsgFAwmkXjiRBjXlzrYwQqEkn8lRw.lvBsnnF8Nk34lG_tZX5gX5cRTBgt51BN0tjXOKYcQ33GtAI7gAQdpbnJ_gVPx1_rErQFqv40eFPKNvnClRukLDtrC.45N9vvmV9Gd7HWBpDmE.0qgHTTn5GjsKwAzIC0ExxM4Q7X5T_3esdzB2xVGgPFwJ4zjwOZp._ps90.zPfttq65BZM; wd=513x950"
    }
    response = requests.post(base_url, json=body, headers=headers)
    if response.status_code != 200:
        print(f"Manga '{manga_name}' não encontrado no MangaPark.")
        print(f"Erro ao buscar manga URL: Status code {response.status_code}")
        print(response.text)
        return None
    data = response.json()
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

def get_mangapark_chapter_images(chapter_url):
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

def download_mangapark(manga_path, output_folder_name):
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
        chap_number = re.search(r'Ch.\d+(?:\.\d+)?', chap_name)
        if not chap_number:
            print(f"  -> Aviso: Número do capítulo não encontrado em {chap_name}. Pulando.")
            continue
        chap_number = chap_number.group().replace('Ch.', '')
        if file_exists_with_regex(output_folder_name, fr".*Ch\.{format_number(chap_number)}\.cbz"):
            print(f"Capítulo {chap_name} já existe. Pulando.")
            continue
        print(f"Baixando capítulo: {chap_name}")
        imgs = get_mangapark_chapter_images(chap_url)
        if len(imgs) == 0:
            print(f"  -> Aviso: Nenhuma imagem baixada para o capítulo {chap_name}. Pulando.")
            continue
        save_cbz(imgs, format_number(chap_number), output_folder_name, manga_path, volume_number if not volume_number or volume_number != '0' else None)

def main():
    if len(sys.argv) != 2:
        print("Erro ao pegar o nome do manga")
        exit(1)
    load_dotenv()
    global driver
    driver = uc.Chrome()
    manga_path = sys.argv[1]
    output_folder_name = os.getenv("MANGA_PATH") + "/" + manga_path.split('/')[-1]
    download_mangapark(manga_path, output_folder_name)
    download_mangadex(manga_path, output_folder_name)
    download_mangalivre(manga_path, output_folder_name)
    driver.quit()


if __name__ == "__main__":
    main()
