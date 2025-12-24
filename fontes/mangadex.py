import os
import requests
import io
from PIL import Image
from utils import format_number, save_cbz, file_exists_with_regex


def get_mangadex_id(manga_name):
    search_url = f"https://api.mangadex.org/manga?title={manga_name}&order[relevance]=desc"
    response = requests.get(search_url)
    if response.status_code != 200:
        print(f"Erro ao buscar manga ID: Status code {response.status_code}")
        return None
    data = response.json()
    if data["result"] == "ok" and data["data"]:
        return data["data"][0]["id"]
    return None

def get_mangadex_chapters(manga_id):
    chapters_url = f"https://api.mangadex.org/manga/{manga_id}/feed?translatedLanguage[]=pt-br&order[chapter]=asc"
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
        if file_exists_with_regex(output_folder_name, fr".*Ch\.{format_number(chap_number)}\.cbz"):
            print(f"Capítulo {chap_number} já existe. Pulando.")
            continue
        print(f"Baixando capítulo: {chap_number}")
        cap_imgs = get_mangadex_chapter_images(chap_id)
        if len(cap_imgs) == 0:
            print(f"  -> Aviso: Nenhuma imagem baixada para o capítulo {chap_number}. Pulando.")
            continue
        save_cbz(cap_imgs, f"{format_number(chap_number)}", output_folder_name, manga_path, chap_vol if chap_vol or chap_vol != '0' else None)
        print(f"  -> Download do capítulo {chap_number} concluído.")
  