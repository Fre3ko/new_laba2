import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import random
from questions import questions
import settings

# Создание бота и диспетчера
bot = Bot(token=settings.API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Создание класса для хранения состояния игры
class Game(StatesGroup):
    start = State()
    question = State()
    answer = State()
    result = State()

# Инициализация переменной для списка оставшихся вопросов
remaining_questions = questions.copy()

# Функция для начала игры
@dp.message_handler(commands=['start'], state='*')
async def start_game(message: types.Message):
    await Game.start.set()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Начать')).add(KeyboardButton('Начать заново'))
    await message.answer('Добро пожаловать в игру "Кто хочет стать миллионером?"!\n'
                        'Вам предлагается ответить на 3 вопроса.\n'
                        'Если вы ответите правильно на все 3 вопроса, вы победите.\n'
                        'Если неправильно, игра будет прекращена.\n'
                        'Нажмите "Начать" для начала игры или "Начать заново" для перезапуска.', reply_markup=keyboard)

# Обработчик нажатия на кнопку "Начать"
@dp.message_handler(lambda message: message.text == 'Начать', state=Game.start)
async def start_game_handler(message: types.Message, state: FSMContext):
    global remaining_questions
    remaining_questions = questions.copy()
    await Game.next()
    await next_question(message, state)

# Обработчик нажатия на кнопку "Начать заново"
@dp.message_handler(lambda message: message.text == 'Начать заново', state='*')
async def restart_game(message: types.Message, state: FSMContext):
    await state.finish()
    await start_game(message)

# Функция для следующего вопроса
async def next_question(message: types.Message, state: FSMContext):
    global remaining_questions
    if remaining_questions:
        game_index = random.randint(0, len(remaining_questions) - 1)
        current_question = remaining_questions.pop(game_index)
        await state.update_data(current_question=current_question)  # Сохраняем текущий вопрос в состоянии FSMContext
        await message.answer(current_question['text'], reply_markup=ReplyKeyboardMarkup(keyboard=[
            ['a', 'b', 'c', 'd'],
            ['Отмена']
        ], resize_keyboard=True))
    else:
        await message.answer('Поздравляем Вы ответили правильно на все 3 вопроса и победили в игре!\n'
                            'Спасибо за игру!', reply_markup=ReplyKeyboardRemove())
        await state.finish()

# Функция для ответа на вопрос
@dp.message_handler(state=Game.question, content_types=types.ContentType.TEXT)
async def answer_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_question = data.get('current_question')
    if current_question:
        if message.text.lower() in ['a', 'b', 'c', 'd']:
            if message.text.lower() == current_question['correct_answer']:
                await message.answer('Верно!\n'
                                    'Вы продолжаете играть.', reply_markup=ReplyKeyboardMarkup(keyboard=[
                                        ['a', 'b', 'c', 'd'],
                                        ['Отмена']
                                    ], resize_keyboard=True))
                correct_answers = data.get('correct_answers', 0) + 1
                await state.update_data(correct_answers=correct_answers)
                if correct_answers == 3:  # Уменьшаем количество вопросов для победы на 1
                    await message.answer('Поздравляем! Вы ответили правильно на все 3 вопроса и победили в игре!\n'
                                        'Спасибо за игру!', reply_markup=ReplyKeyboardRemove())
                    await state.finish()
                else:
                    await next_question(message, state)
            else:
                await message.answer('Неверно.\n'
                                    'Игра прекращена.\n'
                                    'Спасибо за игру!', reply_markup=ReplyKeyboardMarkup(keyboard=[
                                        ['Начать заново']
                                    ], resize_keyboard=True))
                await state.finish()
        elif message.text.lower() == 'отмена':
            await message.answer('Игра прекращена.\n'
                                'Спасибо за игру!', reply_markup=ReplyKeyboardRemove())
            await state.finish()
        else:
            await message.answer('Неверный формат ответа.\n'
                                'Пожалуйста, выберите ответ из предложенных вариантов.', reply_markup=ReplyKeyboardMarkup(keyboard=[
                                    ['a', 'b', 'c', 'd'],
                                    ['Отмена']
                                ], resize_keyboard=True))
    else:
        await message.answer('Произошла ошибка. Пожалуйста, начните игру заново.')

# Функция для результата игры
@dp.message_handler(state=Game.result)
async def game_result(message: types.Message):
    await message.answer('Спасибо за игру!', reply_markup=ReplyKeyboardRemove())

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)