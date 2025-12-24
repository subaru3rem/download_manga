import requests
from bs4 import BeautifulSoup

def get_novel_chapters(name):
    html = requests.get("https://centralnovel.com/series/" + name)
    soup = BeautifulSoup(html, 'lxml')
    volumes = soup.find_all()

def download_novel(novel):
    pass
