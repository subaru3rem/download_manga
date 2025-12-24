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

def get_mangafire_url(manga_name, driver):
    base_url = "https://mangafire.to"
    driver.get(base_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-inner"))
        )
    except Exception as e:
        print(f"  -> Erro ao carregar a página inicial do site")
        return None
    
    form = driver.find_element(By.XPATH, "//form[@action='filter']")
    form.send_keys(manga_name)
    form.send_keys("\n")

def get_mangafire_chapters(manga_name):
    pass

def get_mangafire_chapter_images(chapter_url):
    pass

def download_mangafire(manga_path, output_folder_name, driver):
    manga_url = get_mangafire_url(manga_path, driver)