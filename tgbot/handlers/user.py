import imdb
import movieposters as mp
# import requests
import rottentomatoes as rt
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from bs4 import BeautifulSoup
from translate import Translator

from tgbot.keyboards.inline import kbd_best_info
from tgbot.keyboards.reply import kbd_menu, kbd_stop
from tgbot.misc.states import MovieSelection, search_url
import calendar
import aiohttp

translator = Translator(from_lang="uk", to_lang="en")


async def user_start(message: types.Message):
    await message.reply(
        f"<b>Вітаю!Мета цього бота - допомогти вам слідкувати за всією важливою інформацією,"
        f"яка має відношення до фільмів.</b>\n"
        f"<b>Ваші можливості:</b>\n"
        f"  <b>Пошук інформації:</b>\n"
        f"    /rate - показує оцінки фільму\n"
        f"    /topbest - показує топ фільмів за зборами протягом цього року\n"
        f"    /calendar - малий календар на місяць, поміченими датами виходу фільмів\n"
        f"    /stop - вихід з режму пошуку інформації\n"
        f"  <b>Кінотеатри:</b>\n"
        f"    /cinemshort - показує короткий список з фільмів,що йдуть та будуть йти в кінотеатрі\n"
        f"    /cinemanow - показує фільми,що йдуть в кінотеатрі\n"
        f"    /cinemasoon - показує фільми,що скоро будуть йти в кінотеатрі\n"

        , reply_markup=kbd_menu)


async def rate_stop(message: types.Message, state: FSMContext):
    await message.answer("<b>Стан пошуку інформації виключено</b>", reply_markup=kbd_menu)
    await state.finish()


async def rate_filter(message: types.Message):
    await message.answer("<b>Введіть назву фільма</b>", reply_markup=kbd_stop)
    await MovieSelection.movie1.set()


async def rate_message(message: types.Message, state: FSMContext):
    await message.answer("<b><i>Пошук...</i></b>")
    try:
        moviesDB = imdb.IMDb()
        async with state.proxy() as data:
            try:
                data['movies'] = moviesDB.search_movie(translator.translate(message.text))
                data['id'] = data['movies'][0].getID()
                data['movie'] = moviesDB.get_movie(data['id'])
                data['title'] = data['movie']['title']
                data['year'] = data['movie']['year']
                data['rating_imdb'] = data['movie']['rating']
                data['directors'] = data['movie']['directors']
                data['directStr'] = ' '.join(map(str, data['directors']))
            except:
                data['movies'] = None
                data['id'] = None
                data['movie'] = None
                data['rating_imdb'] = None
                data['directors'] = None
                data['directStr'] = None
                data['title'] = message.text
                data['year'] = rt.year_released(data['title'])
            try:
                data['movie_tom'] = rt.Movie(data['title'])
            except:
                data['movie_tom'] = None
            data['kbd_actions'] = InlineKeyboardMarkup(row_width=1)
            data['btnActor'] = InlineKeyboardButton(text="Актори", callback_data=f"Actors {data['title']}:")
            data['btnTomatoes'] = InlineKeyboardButton(text="Інформація про Tomatoes",
                                                       callback_data=f"Tomatoes {data['title']}:")
            data['kbd_actions'].insert(data['btnActor'])
            data['kbd_actions'].insert(data['btnTomatoes'])
            data['link'] = mp.get_poster(title=data['title'])
        if data['movie_tom'] is not None:
            await message.answer_photo(data['link'], caption=
            f"<b>Інформація про фільм:</b>\n"
            f"{data['title']} - {data['year']}\n"
            f"{data['movie_tom'].duration}\n"
            f"<b>Жанр:</b> {', '.join(map(str, data['movie_tom'].genres))}\n"
            f"<b>Оцінка IMDb:</b> {data['rating_imdb']}\n"
            f"<b>Оцінка Tomatoes:</b> {data['movie_tom'].tomatometer}\n"
            f"<b>Режисер:</b> {data['directStr']}"
                                       , reply_markup=data['kbd_actions'])
        elif data['movie_tom'] is None:
            await message.answer_photo(data['link'], caption=
            f"<b>Інформація про фільм:</b>\n"
            f"{data['title']} - {data['year']}\n"
            f"<b>Оцінка IMDb:</b> {data['rating_imdb']}\n"
            f"<b>Оцінка Tomatoes:</b> None\n"
            f"<b>Режисер:</b> {data['directStr']}"
                                       , reply_markup=data['kbd_actions'])
    except:
        await message.answer("<b>Фільм не знайдено. Використовуйте англійську назву фільма для кращого пошуку</b>")


async def see_actors_modern(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as dat:
            dat['title'] = call.data.replace("Actors ", "")
        async with state.proxy() as data:
            data['casting'] = rt.actors(data['title'], max_actors=10)
            data['actors'] = ', '.join(map(str, data['casting']))
        await call.message.answer(f"{data['title']}\n<b>Актори:</b> {str(data['actors'])}")
    except:
        await call.message.answer("<b>Помилка.</b>")


async def see_tomatoes_modern(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as dat:
            dat['title'] = call.data.replace("Tomatoes ", "")
        async with state.proxy() as data:
            data['movie_tom'] = rt.Movie(data['title'])
        await call.message.answer(
            f"{data['title']}\n"
            f"<b>Оцінка критиків:</b>{data['movie_tom'].weighted_score}\n"
            f"<b>Оцінка глядачів:</b>{data['movie_tom'].audience_score}"
        )
    except:
        await call.message.answer("<b>Немає точної інформації</b>")


async def cinema_watch(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as dat:
            if message.text == "/cinemanow":
                dat['cl_name'] = "content__section movies__section"
            elif message.text == "/cinemasoon":
                dat['cl_name'] = "content__section soon__section movies__section"
            dat['MAIN_URL'] = "https://planetakino.ua/"
            dat['url'] = 'https://planetakino.ua/movies/'
            async with aiohttp.ClientSession() as session:
                async with session.get(dat['url'], ssl=False) as response:
                    dat['html_text'] = await response.text()
            # dat['r'] = requests.get(dat['url'])
            # dat['html_text'] = dat['r'].text
            dat['doc'] = BeautifulSoup(dat['html_text'], "lxml")
            dat['all_movies'] = dat['doc'].find(class_=dat['cl_name']).find_all(class_="movie-block__link")
            dat['list_of_linnks'] = []
            dat['list_of_name'] = []
            for dat['link'] in dat['all_movies']:
                if dat['link'].get('href') in dat['list_of_linnks']:
                    continue
                dat['movie_link'] = dat['MAIN_URL'] + dat['link']['href']
                dat['list_of_linnks'].append(dat['link']['href'])
                dat['movie'] = dat['link'].find(class_="lazy")
                if dat['movie'] is not None:
                    dat['movie_name'] = dat['movie'].get('alt')
                    if dat['movie_name'] in dat['list_of_name']:
                        continue
                    if dat['movie_name'] == "Дізнайся, як обміняти квиток чи повернути гроші":
                        continue
                    dat['movie_poster'] = dat['MAIN_URL'] + dat['movie'].get('src')
                    dat['kbd_link'] = InlineKeyboardMarkup(inline_keyboard=[
                        [KeyboardButton(text="Відкрити сайт", url=dat['movie_link'])]
                    ])
                    dat['extra_information'] = search_url(dat['movie_link'])
                    await message.answer_photo(dat['movie_poster'], caption=
                    f"{dat['movie_name']}\n"
                    f"<b>Рік:</b>{dat['extra_information'][0]}\n"
                    f"<b>Країна:</b>{dat['extra_information'][1]}\n"
                    f"<b>Мова:</b>{dat['extra_information'][2]}\n"
                    f"<b>Жанр:</b>{dat['extra_information'][3]}\n"
                    f"{dat['extra_information'][7]}\n"
                                               , reply_markup=dat['kbd_link'])
                    dat['list_of_name'].append(dat['movie_name'])
    except:
        await message.answer("<b>Досягнуто ліміт фільмів</b>")


async def cinema_short(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['url'] = 'https://planetakino.ua/movies/'
            async with aiohttp.ClientSession() as session:
                async with session.get(data['url'], ssl=False) as response:
                    data['html_text'] = await response.text()
            # data['r'] = requests.get(data['url'])
            # data['html_text'] = data['r'].text
            data['doc'] = BeautifulSoup(data['html_text'], "lxml")
            data['all_movies'] = data['doc'].find(class_="content__section movies__section").find_all(
                class_="movie-block__link")
            data['kbd_movie'] = InlineKeyboardMarkup(row_width=1)
            data['list_of_linnks'] = []
            for data['link'] in data['all_movies']:
                if data['link'].get('href') in data['list_of_linnks']:
                    continue
                data['list_of_linnks'].append(data['link']['href'])
                data['movie'] = data['link'].find(class_="lazy")
                if data['movie'] is not None:
                    data['name'] = data['movie'].get('alt')
                    data['btnName'] = InlineKeyboardButton(text=f"{data['name']}",
                                                           callback_data=f"point{data['movie'].get('alt')}")
                    data['kbd_movie'].insert(data['btnName'])
            await message.answer(text="<b>Зараз в кіно:</b>", reply_markup=data['kbd_movie'])
    except:
        await message.answer("<b>Помилка.</b>")


async def top_best_office(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['MAIN_URL'] = "https://www.boxofficemojo.com/year/world/"
            async with aiohttp.ClientSession() as session:
                async with session.get(data['MAIN_URL'], ssl=False) as response:
                    data['html_text'] = await response.text()
            # data['r'] = requests.get(data['MAIN_URL'])
            # data['html_text'] = data['r'].text
            data['doc'] = BeautifulSoup(data['html_text'], "lxml")
            data['all_box'] = data['doc'].find_all("tr")
            data['n'] = 0
            data['top'] = []
            data['name_list'] = {}
            for data['inf'] in data['all_box']:
                if 1 <= data['n'] <= 10:
                    data['place'] = data['inf'].find(
                        class_="a-text-right mojo-header-column mojo-truncate mojo-field-type-rank mojo-sort-column")
                    data['name'] = data['inf'].find(class_="a-text-left mojo-field-type-release_group")
                    data['money'] = data['inf'].find(class_="a-text-right mojo-field-type-money")
                    data['top'].append(f"<b>{data['place'].text}. {data['name'].text}:</b>\n {data['money'].text}\n")
                    data['name_list'][data['place'].text] = data['name'].text
                    data['n'] += 1
                elif data['n'] <= 1:
                    data['n'] += 1
            data['answer'] = ""
            for i in data['top']:
                data['answer'] += i
            await message.answer(data['answer'], reply_markup=kbd_best_info)
    except:
        await message.answer("<b>Помилка</b>")


async def top_best_movie_select(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.answer("<b>Введіть номер фільму,про який ви бажаєте отримати інформацію</b>", reply_markup=kbd_stop)
        await MovieSelection.best_movie.set()
    except:
        await call.message.answer("<b>Помилка.Спробуйте знову активувати функцію пошука рейтингу та нажати цю кнопку.</b>")


async def top_best_movie_find(message: types.Message, state: FSMContext):
    await message.answer("<b><i>Пошук...</i></b>")
    async with state.proxy() as data:
        moviesDB = imdb.IMDb()
        try:
            data['movies'] = moviesDB.search_movie(data['name_list'][message.text])
            data['id'] = data['movies'][0].getID()
            data['movie'] = moviesDB.get_movie(data['id'])
            data['title'] = data['movie']['title']
            data['year'] = data['movie']['year']
            data['rating_imdb'] = data['movie']['rating']
            data['directors'] = data['movie']['directors']
            data['directStr'] = ' '.join(map(str, data['directors']))
            data['movie_tom'] = rt.Movie(data['title'])
            data['kbd_actions'] = InlineKeyboardMarkup(row_width=1)
            data['btnActor'] = InlineKeyboardButton(text="Актори", callback_data=f"Actors {data['title']}:")
            data['btnTomatoes'] = InlineKeyboardButton(text="Інформація про Tomatoes",
                                                       callback_data=f"Tomatoes {data['title']}:")
            data['kbd_actions'].insert(data['btnActor'])
            data['kbd_actions'].insert(data['btnTomatoes'])
            data['link'] = mp.get_poster(title=data['title'])
            if data['movie_tom'] is not None:
                await message.answer_photo(data['link'], caption=
                f"<b>Інформація про фільм:</b>\n"
                f"{data['title']} - {data['year']}\n"
                f"{data['movie_tom'].duration}\n"
                f"<b>Жанр:</b> {', '.join(map(str, data['movie_tom'].genres))}\n"
                f"<b>Оцінка IMDb:</b> {data['rating_imdb']}\n"
                f"<b>Оцінка Tomatoes:</b> {data['movie_tom'].tomatometer}\n"
                f"<b>Режисер:</b> {data['directStr']}"
                                           , reply_markup=data['kbd_actions'])
        except:
            await message.answer("<b>Помилка пошука</b>")


async def cinema_point(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['title'] = call.data.replace("point", "")
            data['MAIN_URL'] = "https://planetakino.ua/"
            data['url'] = 'https://planetakino.ua/movies/'
            async with aiohttp.ClientSession() as session:
                async with session.get(data['url'], ssl=False) as response:
                    data['html_text'] = await response.text()
            # data['r'] = requests.get(data['url'])
            # data['html_text'] = data['r'].text
            data['doc'] = BeautifulSoup(data['html_text'], "lxml")
            data['all_movies'] = data['doc'].find_all(class_="movie-block__link")
            data['list_of_linnks'] = []
            for data['link'] in data['all_movies']:
                if data['link'].get('href') in data['list_of_linnks']:
                    continue
                data['movie_link'] = data['MAIN_URL'] + data['link']['href']
                data['list_of_linnks'].append(data['link']['href'])
                data['movie'] = data['link'].find(class_="lazy")
                if data['movie'] is not None:
                    data['movie_name'] = data['movie'].get('alt')
                    if data['movie_name'] != data['title']:
                        continue
                    data['movie_poster'] = data['MAIN_URL'] + data['movie'].get('src')
                    data['extra_information'] = search_url(data['movie_link'])
                    data['kbd_link'] = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [KeyboardButton(text="Відкрити сайт", url=data['movie_link'])]
                        ]
                    )
                    await call.message.answer_photo(data['movie_poster'], caption=
                    f"{data['movie_name']}\n"
                    f"<b>Рік:</b>{data['extra_information'][0]}\n"
                    f"<b>Країна:</b>{data['extra_information'][1]}\n"
                    f"<b>Мова:</b>{data['extra_information'][2]}\n"
                    f"<b>Жанр:</b>{data['extra_information'][3]}\n"
                    f"{data['extra_information'][7]}\n"
                                                    , reply_markup=data['kbd_link'])
    except:
        await call.message.answer("<b>Помилка</b>")


async def calendar_menu(message: types.Message):
    kbd_calendar = InlineKeyboardMarkup(row_width=1)
    btnJun = InlineKeyboardButton(text="Червень", callback_data="calendarJun")
    btnJuly = InlineKeyboardButton(text="Липень", callback_data="calendarJulu")
    btnAugust = InlineKeyboardButton(text="Серпень", callback_data="calendarAugust")
    kbd_calendar.insert(btnJun).insert(btnJuly).insert(btnAugust)
    await message.answer("<b><i>Літо 2023</i></b>", reply_markup=kbd_calendar)


async def release_calendar(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as dat:
            if call.data == "calendarJun":
                dat['month'] = "Jun"
                dat['next_month'] = "Jul"
                dat['month_num'] = 6
                dat['add'] = False
            elif call.data == "calendarJulu":
                dat['month'] = "Jul"
                dat['next_month'] = "Aug"
                dat['month_num'] = 7
                dat['add'] = False
            elif call.data == "calendarAugust":
                dat['month'] = "Aug"
                dat['next_month'] = None
                dat['month_num'] = 8
                dat['add'] = False
        async with state.proxy() as data:
            data['movies'] = {}
            try:
                data['url'] = 'https://www.joblo.com/new-movies/'
                async with aiohttp.ClientSession() as session:
                    async with session.get(data['url'], ssl=False) as response:
                        data['html_text'] = await response.text()
                # data['r'] = requests.get(data['url'])
                # data['html_text'] = data['r'].text
                data['doc'] = BeautifulSoup(data['html_text'], "lxml")
                data['all_movies'] = data['doc'].find_all(class_="releases")
                data['c'] = 0
                data['kbd_dates'] = InlineKeyboardMarkup(row_width=3)
                data['all'] = ""
                for link in data['all_movies']:
                    data['dates'] = link.find_all("h2")
                    for i in data['dates']:
                        if data['c'] > 9:
                            data['all'] += f"{i.text}\n"
                        else:
                            data['c'] += 1
                data['movies_list'] = data['all'].strip().split('\n')
                data['current_date'] = None
                data['all_dates'] = 0
                for item in data['movies_list']:
                    data['all_dates'] += 1
                for item in data['movies_list']:
                    if data['next_month'] is not None:
                        if item.startswith(data['month']):
                            data['add'] = True
                            data['btnData'] = InlineKeyboardButton(text=f"{item}", callback_data=f"date{item}")
                            data['kbd_dates'].insert(data['btnData'])
                            data['current_date'] = item
                            data['movies'][data['current_date']] = []
                        elif item.startswith(data['next_month']):
                            raise ValueError
                        else:
                            if not data['add']:
                                continue
                            data['movies'][data['current_date']].append(item)
                    else:
                        if item.startswith(data['month']):
                            data['add'] = True
                            data['all_dates'] -= 1
                            data['btnData'] = InlineKeyboardButton(text=f"{item}", callback_data=f"date{item}")
                            data['kbd_dates'].insert(data['btnData'])
                            data['current_date'] = item
                            data['movies'][data['current_date']] = []
                        elif data['all_dates'] == 16:
                            raise ValueError
                        else:
                            if not data['add']:
                                data['all_dates'] -= 1
                                continue
                            data['movies'][data['current_date']].append(item)
            except ValueError:
                data['dat'] = ""
                for i in data['movies']:
                    data['dat'] += i
                data['movie'] = data['dat'].replace(data['month'], "").replace(" ", "\n")

            data['cal'] = ""
            for i in calendar.monthcalendar(2023, data['month_num']):
                data['pref'] = i
                data['cal'] += f"{data['pref']}\n"
            data['alt'] = data['movie'].split("\n")
            data['cal'] = data['cal'].replace("[", "'").replace("]", "'").replace(",", "'").replace(" ", "'")
            data['c'] = 1
            try:
                while True:
                    data['cal'] = data['cal'].replace(f"'{data['alt'][data['c']]}'", f"<b><i><u>'{data['alt'][data['c']]}'</u></i></b>")
                    data['c'] += 1
            except:
                pass
            data['cal'] = data['cal'].replace("'", " ")
            await call.message.answer(f"<b><i>{data['month']}</i></b>\n{data['cal']}", reply_markup=data['kbd_dates'])
    except:
        await call.message.answer("<b>Помилка.</b>")


async def see_calendar_movies(call: CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as dat:
            dat['keyword'] = call.data.replace("date", "")
            dat['release_list'] = dat['movies'].get(dat['keyword'])
            dat['answer'] = f"<b><i>{call.data.replace('date', '')}:</i></b>\n"
            for item in dat['release_list']:
                if item is not None:
                    dat['answer'] += f"{item}\n"
            await call.message.answer(dat['answer'])
    except:
        await call.message.answer("<b>Помилка.Ви можете побачити інформацію про дати лише до останнього календаря.</b>")


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(rate_stop, commands=["stop"], state="*")
    dp.register_message_handler(rate_filter, commands=["rate"], state="*")
    dp.register_message_handler(cinema_watch, commands=["cinemanow", "cinemasoon"], state="*")
    dp.register_message_handler(cinema_short, commands=["cinemashort"], state="*")
    dp.register_message_handler(top_best_office, commands=["topbest"], state="*")
    dp.register_message_handler(calendar_menu, commands=["calendar"], state="*")
    dp.register_message_handler(top_best_movie_find, state=MovieSelection.best_movie)
    dp.register_message_handler(rate_message, state=MovieSelection.movie1)
    dp.register_callback_query_handler(release_calendar, text_contains="calendar", state="*")
    dp.register_callback_query_handler(cinema_point, text_contains="point", state="*")
    dp.register_callback_query_handler(top_best_movie_select, text_contains="moreinfo", state="*")
    dp.register_callback_query_handler(see_actors_modern, text_contains="Actors", state="*")
    dp.register_callback_query_handler(see_tomatoes_modern, text_contains="Tomatoes", state="*")
    dp.register_callback_query_handler(see_calendar_movies, text_contains="date", state="*")
