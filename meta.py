import requests
from googletrans import Translator
import asyncio
import os
import dotenv
import subprocess
import re
from html import unescape

dotenv.load_dotenv()
url = "https://home.subaru3rem.site/kavita/api"
headers = {"Authorization": "Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoic3ViYXJ1M3JlbSIsIm5hbWVpZCI6IjEiLCJyb2xlIjpbIkFkbWluIiwiTG9naW4iXSwibmJmIjoxNzY0MjUyNzYxLCJleHAiOjE3NjUxMTY3NjEsImlhdCI6MTc2NDI1Mjc2MX0.ZBWwZD9bTOsf872GHyadDKUnSrRel3hcSF8mHBS2R8xMJPhqtpYrjsBegar9qu4JW0kDV2TeCzXwHF__ybfUtg"}

def get_kavita_mangas(series_id=None):
    body = {
    	"statements": [
    		{
    			"field": 19,
    			"value": str(series_id),
    			"comparison": 0
    		}
    	],
    	"combination": 1,
    	"limitTo": 0,
    	"sortOptions": {
    		"isAscending": True,
    		"sortField": 1
    	}
    }
    
    response = requests.post(url + "/Series/v2", json=body, headers=headers)
    if response.status_code != 200:
        print(str(response.status_code) + " - " + response.text)
        return []
    mangas = response.json()
    return mangas

def get_manga_metadata(manga_id):
    manga_url = f"{url}/series/metadata"
    manga_url += f"?seriesId={manga_id}" 
    response = requests.get(manga_url, headers=headers)
    manga_meta = response.json()
    return manga_meta

def translate_text(text, target_language="pt"):
    async def _async_translate():
        async with Translator() as translator:
            result = await translator.translate(text, dest=target_language)
            return result.text

    return asyncio.run(_async_translate())

def set_manga_metadata(metadata):
    update_url = f"{url}/Series/metadata"
    body = {"seriesMetadata": metadata}
    response = requests.post(update_url, json=body, headers=headers)
    if response.status_code != 200:
        print(f"Failed to update metadata: {response.status_code} - {response.text}")
    return response.status_code == 200

def get_book_volumes(manga_id):
    volumes_url = f"{url}/Series/volumes"
    volumes_url += f"?seriesId={manga_id}" 
    response = requests.get(volumes_url, headers=headers)
    volumes = response.json()
    return volumes

def get_volume_metadata(volume_id):
    volume_url = f"{url}/volume/metadata"
    volume_url += f"?volumeId={volume_id}" 
    response = requests.get(volume_url, headers=headers)
    volume_meta = response.json()
    return volume_meta

def extrair_comments(metadata_text: str) -> str:
    """
    Extrai o conteúdo do campo 'Comments' em um texto de metadados estilo Calibre.
    Pega tudo após 'Comments :' até o final do texto.
    Funciona mesmo que não haja <div> ou <p>.
    """
    # Expressão para pegar tudo após 'Comments' até o fim
    match = re.search(r'Comments\s*:\s*(.*)', metadata_text, re.DOTALL)
    if not match:
        return None

    # Remove espaços e quebras de linha extras
    conteudo = match.group(1).strip()
    return conteudo

def strip_tags(text: str) -> str:
    """Remove todas as tags HTML e decodifica entidades HTML."""
    if not text:
        return text
    TAG_RE = re.compile(r'<[^>]*?>', re.S)   # captura tags HTML (não-gulosa)
    # 1) opcional: remover scripts e styles inteiros primeiro
    text = re.sub(r'(?is)<(script|style).*?>.*?</\1>', '', text)
    # 2) remover tags
    text = TAG_RE.sub('', text)
    # 3) decodificar entidades HTML (&amp; -> & etc.)
    text = unescape(text)
    # 4) normalizar espaços (opcional)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def corrigir_texto(texto: str) -> str:
    """
    Corrige texto com caracteres estranhos causados por erro de encoding
    (ex: 'Ã©' → 'é', 'Ã§' → 'ç').
    """
    try:
        return texto.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
    except UnicodeEncodeError as error:
        # Se não funcionar, tenta o inverso
        print(error)
        return texto.encode('ansii').decode('latin1')

def processar_ebook(epub: str, ebook: str = ""):
    comando = f'ebook-meta "{os.path.join(os.getenv("EBOOK_PATH"), ebook, epub)}"'
    meta = subprocess.run(comando, shell=True, capture_output=True, text=True)
    if meta.returncode != 0:
        print(f"  -> Erro ao ler metadados de {epub}: {meta.stderr}")
        return
    if meta.stdout == None:
        print(f"  -> Metadados vazios em {epub}. Pulando.")
        return
    comments = extrair_comments(meta.stdout)
    if not comments:
        print(f"  -> Nenhum comentário encontrado em {epub}. Pulando.")
        return
    new_sumarry = translate_text(comments, "pt")
    new_sumarry = strip_tags(new_sumarry)
    new_sumarry = corrigir_texto(new_sumarry)
    updated_meta = subprocess.run(comando + f' --comments "{new_sumarry}"', shell=True, capture_output=True, text=True)
    if updated_meta.returncode != 0:
        print(f"  -> Erro ao atualizar comentários em {epub}: {updated_meta.stderr}")
    print(f"  -> Comentários traduzidos atualizados em {epub}.")

def main():
    mangas = get_kavita_mangas(1)
    for manga in mangas:
        manga_id = manga.get("id")
        print(f"Processing manga ID: {manga.get('id')} - Title: {manga.get('name')}")
        metadata = get_manga_metadata(manga_id)
        description_en = metadata.get("summary", "")
        description_pt = translate_text(description_en, "pt")
        metadata["summary"] = description_pt
        success = set_manga_metadata(metadata)
        if success:
            print(f"Updated metadata for manga ID {manga_id}")
        else:
            print(f"Failed to update metadata for manga ID {manga_id}")
    # ebooks = os.listdir(os.getenv("EBOOK_PATH"))
    # print(f"Encontrados {len(ebooks)} ebooks para processar.")
    # for ebook in ebooks:
    #     if not os.path.isdir(os.path.join(os.getenv("EBOOK_PATH"), ebook)):
    #         continue
    #     epubs = [f for f in os.listdir(os.path.join(os.getenv("EBOOK_PATH"), ebook))]
    #     print(f"Processando {len(epubs)} epubs na pasta {ebook}.")
    #     for epub in epubs:
    #         if os.path.isfile(os.path.join(os.getenv("EBOOK_PATH"), ebook, epub)):
    #             if not epub.endswith('.epub'):
    #                 continue
    #             processar_ebook(epub, ebook)
    #         else:
    #             for files in os.listdir(os.path.join(os.getenv("EBOOK_PATH"), ebook, epub)):
    #                 if files.endswith('.epub'):
    #                     processar_ebook(files, ebook + '/' + epub)

if __name__ == "__main__":
    main()