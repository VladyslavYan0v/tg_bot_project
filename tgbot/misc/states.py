from aiogram.dispatcher.filters.state import State, StatesGroup
from bs4 import BeautifulSoup
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
import calendar


class MovieSelection(StatesGroup):
    movie1 = State()
    best_movie = State()


def search_url(url):
    if url is not None:
        r = requests.get(url)
        html_text = r.text
        doc = BeautifulSoup(html_text, "lxml")
        all_inform = doc.find(class_="movie-page-block__summary").find_all("dd")
        all = []
        for find in all_inform:
            inform = find.getText()
            all.append(inform)
        return all
    return "No information"

