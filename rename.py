import os
import re
import sys
import dotenv
import zipfile
import requests

def renomear_capitulos(pasta, cap_inicio, cap_fim, novo_volume):
    padrao = re.compile(r'(.*) Ch\.(\d+)(\..+)?')

    for arquivo in os.listdir(pasta):
        caminho_antigo = os.path.join(pasta, arquivo)
        if not os.path.isfile(caminho_antigo):
            continue

        match = padrao.match(arquivo)
        if not match:
            continue

        nome_manga, cap, extensao = match.groups()
        cap_num = int(cap)

        if cap_inicio <= cap_num <= cap_fim:
            nome_manga = re.sub(" Vol.\d+", "", nome_manga)
            novo_nome = f"{nome_manga} Vol.{int(novo_volume):02d} Ch.{cap_num:02d}{extensao or ''}"
            caminho_novo = os.path.join(pasta, novo_nome)
            try:
                os.rename(caminho_antigo, caminho_novo)
                print(f"Renomeado: {arquivo} → {novo_nome}")
            except Exception as e:
                print(f"Erro ao renomear {arquivo}: {e}")

def remove_first_image_from_cbz(folder_path: str, limit: int | None = None, init: int = 0):
    """
    Remove a primeira imagem de cada arquivo .cbz em uma pasta.

    Args:
        folder_path (str): Caminho da pasta contendo os arquivos .cbz
        limit (int | None): Quantidade máxima de arquivos a processar (opcional)
    """
    # Lista todos os arquivos .cbz na pasta
    cbz_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".cbz")]

    if limit is not None:
        cbz_files = cbz_files[:limit]

    cbz_files = cbz_files[init:]

    for cbz_name in cbz_files:
        cbz_path = os.path.join(folder_path, cbz_name)
        temp_path = cbz_path + ".tmp"

        with zipfile.ZipFile(cbz_path, "r") as original_zip:
            # Filtra apenas os arquivos de imagem (jpg/png/webp etc.)
            image_files = sorted(
                [f for f in original_zip.namelist() if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
            )

            if not image_files:
                print(f"[!] Nenhuma imagem encontrada em {cbz_name}, ignorando.")
                continue

            # Define a primeira imagem que será removida
            first_image = image_files[0]
            print(f"Removendo {first_image} de {cbz_name}")

            # Cria um novo .cbz sem a primeira imagem
            with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as new_zip:
                for item in original_zip.infolist():
                    if item.filename != first_image:
                        new_zip.writestr(item, original_zip.read(item.filename))

        # Substitui o original
        os.replace(temp_path, cbz_path)

    print("✅ Operação concluída com sucesso!")

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

def get_cover_names(manga_id):
    cover_url = f"https://api.mangadex.org/cover?manga[]={manga_id}&order[volume]=asc"
    response = requests.get(cover_url)
    if response.status_code != 200:
        print(f"Erro ao buscar capas: Status code {response.status_code}")
        return []
    data = response.json()
    cover_names = []
    if data["result"] == "ok":
        for cover in data["data"]:
            attributes = cover["attributes"]
            file_name = attributes.get("fileName")
            volume = attributes.get("volume")
            if file_name:
                cover_names.append({volume:file_name})
    return cover_names

if __name__ == "__main__":
    dotenv.load_dotenv()
    pasta = os.getenv("MANGA_PATH") + "/" + sys.argv[1]
    volumes = [[86, 89, 22], [90, 94, 23], [95, 98, 24], [99, 103, 25], [104, 200, 26]]
    # # volumes = [[1, 7, 1],[8, 15, 2],[16, 23, 3], [24, 31, 4], [32, 39, 5], [40, 47, 6], 
    # #     [48, 55, 7], [56, 63, 8], [64, 71, 9], [72, 79, 10], [80, 87, 11],[88, 95, 12],
    # #     [96, 102, 13], [103, 109, 14],[110, 115, 15]]
    # # files = os.listdir(pasta)
    # # for file in files:
    # #     # old_name = os.path.join(pasta, file)
    # #     # new_name = os.path.join(pasta, file.replace("teasing master takagi-san", "Teasing Master Takagi-San"))
    # #     # print(old_name)
    # #     # print(new_name)
    # #     # print("")
    # #     # os.rename(old_name, new_name)
    # for cap_inicio, cap_fim, novo_volume in volumes:
    #     renomear_capitulos(pasta, cap_inicio, cap_fim, novo_volume)

    # remove_first_image_from_cbz(pasta, 7, 0)

    manga_name = sys.argv[1].title()
    manga_id = get_mangadex_id(manga_name)
    if not manga_id:
        print(f"Manga '{manga_name}' não encontrado.")
        sys.exit(1)
    cover_names = get_cover_names(manga_id)
    for cover in cover_names:
        for volume, file_name in cover.items():
            if volume is None:
                continue
            
    