import os
import sys
import seleniumbase as sb
from dotenv import load_dotenv
from fontes.mangadex import download_mangadex
from fontes.mangapark import download_mangapark
from fontes.mangalivre import download_mangalivre

def main():
    if len(sys.argv) != 2:
        print("Erro ao pegar o nome do manga")
        exit(1)
    load_dotenv()
    global driver
    
    driver = sb.Driver(uc_cdp=True, incognito=True, disable_gpu=True, window_size="1920,1080", no_sandbox=True)
    manga_path = sys.argv[1]
    manga_path = manga_path.title()
    output_folder_name = os.getenv("MANGA_PATH") + "/" + manga_path.split('/')[-1]
    download_mangadex(manga_path, output_folder_name)
    download_mangapark(manga_path, output_folder_name, driver)
    download_mangalivre(manga_path, output_folder_name, driver)

    
    driver.quit()


if __name__ == "__main__":
    main()
