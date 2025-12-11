import telebot
from telebot import types
import requests
import random
import re

TOKEN = "8069259609:AAHJiQPfuRjwzOfDuccfRZYodHPWXjfBH_E"
bot = telebot.TeleBot(TOKEN)
API_URL = "https://api.mymemory.translated.net/get"
MEALDB = "https://www.themealdb.com/api/json/v1/1"

def has_ru(text):
    for ch in text:
        if 'а' <= ch <= 'я' or 'А' <= ch <= 'Я':
            return True
    return False

def translate_text(text, src=None, trg=None):
    if not text:
        return ""
    if not src or not trg:
        langpair = "ru|en" if has_ru(text) else "en|ru"
    else:
        langpair = f"{src}|{trg}"
    parts = [text[i:i+400] for i in range(0, len(text), 400)]
    result = []

    for chunk in parts:
        try:
            r = requests.get(API_URL, params={"q": chunk, "langpair": langpair}, timeout=7)
            data = r.json()
            result.append(data["responseData"]["translatedText"])
        except:
            result.append(chunk)
    return "".join(result)

def strip_html(s):
    return re.sub(r"<.*?>", "", s)


last_recipe = {}
user_choice = {}

cuisines = {
    "American": "Американская",
    "British": "Британская",
    "Canadian": "Канадская",
    "Chinese": "Китайская",
    "French": "Французская",
    "Indian": "Индийская",
    "Italian": "Итальянская",
    "Japanese": "Японская",
    "Mexican": "Мексиканская",
    "Thai": "Тайская"
}

categories = {
    "Beef": "Говядина",
    "Chicken": "Курица",
    "Dessert": "Десерт",
    "Lamb": "Баранина",
    "Miscellaneous": "Разное",
    "Pasta": "Паста",
    "Pork": "Свинина",
    "Seafood": "Морепродукты",
    "Side": "Гарнир",
    "Starter": "Закуска",
    "Vegan": "Веганское",
    "Vegetarian": "Вегетарианское"
}


def back_button(target="menu"):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(" Назад", callback_data=target))
    return kb

def menu_keyboard():
    kb = types.InlineKeyboardMarkup()

    items = list(cuisines.items())
    for i in range(0, len(items), 2):
        row = items[i:i+2]
        row_buttons = []
        for key, title in row:
            row_buttons.append(types.InlineKeyboardButton(title, callback_data=f"c_{key}"))
        kb.row(*row_buttons)

    kb.add(types.InlineKeyboardButton("Случайное блюдо", callback_data="rnd"))
    kb.add(types.InlineKeyboardButton("Назад", callback_data="start_back"))
    return kb

def category_keyboard():
    kb = types.InlineKeyboardMarkup()

    items = list(categories.items())
    for i in range(0, len(items), 2):
        row = items[i:i+2]
        kb.row(*[types.InlineKeyboardButton(title, callback_data=f"t_{key}") for key, title in row])

    kb.add(types.InlineKeyboardButton("Назад", callback_data="menu"))
    return kb


@bot.message_handler(commands=['start'])
def start(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Меню", callback_data="menu"))
    kb.add(types.InlineKeyboardButton("Помощь", callback_data="help"))
    bot.send_message(message.chat.id, "Привет! Давай выберем что-нибудь вкусное", reply_markup=kb)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, "Привет ! Если вдруг что-то сломалось , попробуйте перезапустить бота или перезайти в телеграм , если не помоглo, обратитесь к @asmlwwit")
@bot.message_handler(commands=["menu"])
def menu_cmd(message):
    send_menu(message.chat.id)


def send_menu(chat_id):
    kb = types.InlineKeyboardMarkup()

    items = list(cuisines.items())
    for i in range(0, len(items), 2):
        row = items[i:i+2]
        buttons = []
        for key, title in row:
            buttons.append(
                types.InlineKeyboardButton(title, callback_data=f"c_{key}")
            )
        kb.row(*buttons)

    kb.add(types.InlineKeyboardButton("Случайное блюдо", callback_data="rnd"))
    kb.add(types.InlineKeyboardButton("Назад", callback_data="start_back"))

    bot.send_message(chat_id, "Выбери кухню:", reply_markup=kb)

def send_menu(chat_id):
    bot.send_message(chat_id, "Выбери кухню:", reply_markup=menu_keyboard())

def send_categories(chat_id, cuisine):
    title = cuisines.get(cuisine, cuisine)
    bot.send_message(chat_id, f"Выбрана кухня: {title}\nТеперь выбери категорию:", reply_markup=category_keyboard())

def get_recipe_by_params(area, category):
    try:
        a = requests.get(f"{MEALDB}/filter.php?a={area}").json().get("meals", [])
        b = requests.get(f"{MEALDB}/filter.php?c={category}").json().get("meals", [])

        ids = list({m["idMeal"] for m in a} & {m["idMeal"] for m in b})
        if not ids:
            ids = [m["idMeal"] for m in a]

        chosen = random.choice(ids)
        meal = requests.get(f"{MEALDB}/lookup.php?i={chosen}").json()["meals"][0]
        return meal
    except:
        return None

def send_recipe(chat_id, meal):
    name = meal["strMeal"]
    area = meal["strArea"]
    cat = meal["strCategory"]
    instr = meal["strInstructions"]
    img = meal["strMealThumb"]

    ing_list = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        ms = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            ing_list.append(f"• {ing} — {ms}")

    text = (
        f"<b>{name}</b>\n\n"
        f"<b>Кухня:</b> {area}\n"
        f"<b>Категория:</b> {cat}\n\n"
        f"<b>Ингредиенты:</b>\n" + "\n".join(ing_list) +
        f"\n\n<b>Инструкция:</b>\n{instr}"
    )

    try:
        bot.send_photo(chat_id, img, caption=text, parse_mode="HTML")
    except:
        bot.send_message(chat_id, text, parse_mode="HTML")

    last_recipe[chat_id] = text

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Англ → Рус", callback_data="tr_ru"))
    kb.add(types.InlineKeyboardButton("Рус → Англ", callback_data="tr_en"))
    bot.send_message(chat_id, "Перевести рецепт?", reply_markup=kb)

def translate_recipe(chat_id, src, trg):
    txt = last_recipe.get(chat_id)
    if not txt:
        bot.send_message(chat_id, "Переводить нечего.")
        return

    clean = strip_html(txt)
    tr = translate_text(clean, src, trg)
    bot.send_message(chat_id, tr)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Хочу ещё", callback_data="again"))
    bot.send_message(chat_id, "Готово!", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    cid = call.message.chat.id
    data = call.data

    if data == "start_back":
        start(call.message)
        return

    if data == "menu":
        send_menu(cid)
        return

    if data == "help":
        bot.send_message(cid, "Привет ! Если вдруг что-то сломалось , попробуйте перезапустить бота или перезайти в телеграм , если не помоглo, обратитесь к @asmlwwit")
        return

    if data == "rnd":
        try:
            meal = requests.get(f"{MEALDB}/random.php").json()["meals"][0]
            send_recipe(cid, meal)
        except:
            bot.send_message(cid, "Не получилось загрузить блюдо.", reply_markup=back_button())
        return

    if data.startswith("c_"):
        cuisine = data[2:]
        user_choice[cid] = {"cuisine": cuisine}
        send_categories(cid, cuisine)
        return

    if data.startswith("t_"):
        cat = data[2:]
        cuisine = user_choice.get(cid, {}).get("cuisine")
        if not cuisine:
            bot.send_message(cid, "Кухня не выбрана.", reply_markup=back_button("menu"))
            return

        meal = get_recipe_by_params(cuisine, cat)
        if meal:
            send_recipe(cid, meal)
        else:
            bot.send_message(cid, "Ничего не нашлось.", reply_markup=back_button("menu"))
        return

    if data == "tr_ru":
        translate_recipe(cid, "en", "ru")
        return

    if data == "tr_en":
        translate_recipe(cid, "ru", "en")
        return

    if data == "again":
        send_menu(cid)
        return


@bot.message_handler(func=lambda m: True)
def translate_user(m):
    text = m.text.strip()
    bot.send_message(m.chat.id, translate_text(text))

bot.polling(none_stop=True)
