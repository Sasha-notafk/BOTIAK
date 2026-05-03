import asyncio
import json
import random
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# 1. Включаем логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# 2. Проверка токена
TOKEN = os.getenv("8774808308:AAEokPwb_HxRt1gvDU4F_Q2otirF1UAnUeY")
if not TOKEN:
    # Если запускаешь на компьютере, замени 'YOUR_TOKEN' на свой токен от BotFather
    TOKEN = "8774808308:AAEokPwb_HxRt1gvDU4F_Q2otirF1UAnUeY" 

# 3. Безопасная загрузка JSON
try:
    with open("data.json", "r", encoding="utf-8") as f:
        games = json.load(f)
except FileNotFoundError:
    print("Ошибка: Файл data.json не найден! Создай его в папке с ботом.")
    games = {}

bot = Bot(token=TOKEN)
dp = Dispatcher()

class GameState(StatesGroup):
    waiting_for_players = State()
    waiting_for_spies = State()
    playing = State()

def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Dota 2", callback_data="game_dota")],
        [InlineKeyboardButton(text="🔫 Brawl Stars", callback_data="game_brawl")],
        [InlineKeyboardButton(text="🏰 Clash Royale", callback_data="game_clash")]
    ])

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎮 Выбери игру:", reply_markup=get_start_keyboard())

@dp.callback_query(F.data.startswith("game_"))
async def choose_game(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    game_name = callback.data.split("_")[1]
    await state.update_data(game=game_name)
    await state.set_state(GameState.waiting_for_players)
    await callback.message.edit_text(f"Выбрана игра: {game_name.upper()}\n\n👥 Введи количество игроков:")

@dp.message(GameState.waiting_for_players)
async def set_players(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введи число!")
    
    await state.update_data(players=int(message.text))
    await state.set_state(GameState.waiting_for_spies)
    await message.answer("🕵️ Введи количество шпионов:")

@dp.message(GameState.waiting_for_spies)
async def set_spies_and_start(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введи число!")
    
    spies = int(message.text)
    user_data = await state.get_data()
    players = user_data["players"]
    
    if spies >= players:
        return await message.answer("Шпионов не может быть больше, чем игроков!")

    game_key = user_data["game"]
    game = games.get(game_key, {"heroes": []})
    
    if not game["heroes"]:
        return await message.answer("В списке этой игры нет героев!")

    main_hero = random.choice(game["heroes"])
    roles = ["spy"] * spies + ["player"] * (players - spies)
    random.shuffle(roles)
    
    await state.update_data(spies=spies, index=0, main_hero=main_hero, roles=roles)
    await state.set_state(GameState.playing)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Посмотреть роль", callback_data="show")]
    ])
    await message.answer(f"🎮 {game_key.upper()}\n👉 Игрок 1", reply_markup=kb)

@dp.callback_query(F.data == "show", GameState.playing)
async def show_role(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    index = user_data["index"]
    roles = user_data["roles"]
    
    role = roles[index]
    if role == "spy":
        text = "🕵️‍♂️ ТЫ ШПИОН"
    else:
        hero = user_data["main_hero"]
        text = f"🎭 {hero['en']} - {hero['ru']}"
        
    await callback.answer(text, show_alert=True) # Показывает роль во всплывающем окне

    index += 1
    await state.update_data(index=index)
    
    if index >= user_data["players"]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Играть снова", callback_data="restart")]
        ])
        await callback.message.answer("🔥 Все посмотрели роли! Начинайте обсуждение.", reply_markup=kb)
        await state.clear()
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👀 Посмотреть роль", callback_data="show")]
        ])
        await callback.message.edit_text(f"👉 Игрок {index + 1}", reply_markup=kb)

@dp.callback_query(F.data == "restart")
async def restart(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.answer("🎮 Выбери игру:", reply_markup=get_start_keyboard())

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())