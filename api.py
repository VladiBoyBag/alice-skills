# # coding: utf-8
# # Импортирует поддержку UTF-8.
# from __future__ import unicode_literals
#
# # Импортируем модули для работы с JSON и логами.
# import json
# import logging
#
# # Импортируем подмодули Flask для запуска веб-сервиса.
# from flask import Flask, request
# app = Flask(__name__)
#
#
# logging.basicConfig(level=logging.DEBUG)
#
# # Хранилище данных о сессиях.
# sessionStorage = {}
#
# # Задаем параметры приложения Flask.
# @app.route("/", methods=['POST'])
#
# def main():
# # Функция получает тело запроса и возвращает ответ.
#     logging.info('Request: %r', request.json)
#
#     response = {
#         "version": request.json['version'],
#         "session": request.json['session'],
#         "response": {
#             "end_session": False
#         }
#     }
#
#     handle_dialog(request.json, response)
#
#     logging.info('Response: %r', response)
#
#     return json.dumps(
#         response,
#         ensure_ascii=False,
#         indent=2
#     )
#
# # Функция для непосредственной обработки диалога.
# def handle_dialog(req, res):
#     user_id = req['session']['user_id']
#
#     if req['session']['new']:
#         # Это новый пользователь.
#         # Инициализируем сессию и поприветствуем его.
#
#         sessionStorage[user_id] = {
#             'suggests': [
#                 "Не хочу.",
#                 "Не буду.",
#                 "Отстань!",
#             ]
#         }
#
#         res['response']['text'] = 'Привет! Пошёл нахуй!'
#         res['response']['buttons'] = get_suggests(user_id)
#         return
#
#     # Обрабатываем ответ пользователя.
#     if req['request']['original_utterance'].lower() in [
#         'ладно',
#         'куплю',
#         'покупаю',
#         'хорошо',
#         'иди сам хахуй',
#         'руся ебень'
#     ]:
#         # Пользователь согласился, прощаемся.
#         res['response']['text'] = 'Твою мать можно найти на Яндекс.Маркете!'
#         return
#
#     # Если нет, то убеждаем его купить слона!
#     res['response']['text'] = 'Все говорят "%s", а ты поищи свою мать на рынке!' % (
#         req['request']['original_utterance']
#     )
#     res['response']['buttons'] = get_suggests(user_id)
#
# # Функция возвращает две подсказки для ответа.
# def get_suggests(user_id):
#     session = sessionStorage[user_id]
#
#     # Выбираем две первые подсказки из массива.
#     suggests = [
#         {'title': suggest, 'hide': True}
#         for suggest in session['suggests'][:2]
#     ]
#
#     # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
#     session['suggests'] = session['suggests'][1:]
#     sessionStorage[user_id] = session
#
#     # Если осталась только одна подсказка, предлагаем подсказку
#     # со ссылкой на Яндекс.Маркет.
#     if len(suggests) < 2:
#         suggests.append({
#             "title": "Ладно",
#             "url": "https://market.yandex.ru/search?text=мать",
#             "hide": True
#         })
#
#     return suggests

from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.

cities = {
    'москва': ['1540737/daa6e420d33102bf6947',
               '213044/7df73ae4cc715175059e'],
    'нью-йорк': ['1652229/728d5c86707054d4745f',
                 '1030494/aca7ed7acefde2606bdc'],
    'париж': ["1652229/f77136c2364eb90a3ea8",
              '3450494/aca7ed7acefde22341bdc']
}

# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Какой город хочешь увидеть?'
            # получаем варианты buttons из ключей нашего словаря cities
            res['response']['buttons'] = [
                {
                    'title': city.title(),
                    'hide': True
                } for city in cities
            ]
    # если мы знакомы с пользователем и он нам что-то написал,
    # то это говорит о том, что он уже говорит о городе,
    # что хочет увидеть.
    else:
        # ищем город в сообщение от пользователя
        city = get_city(req)
        # если этот город среди известных нам,
        # то показываем его (выбираем одну из двух картинок случайно)
        if city in cities:
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Этот город я знаю.'
            res['response']['card']['image_id'] = random.choice(cities[city])
            res['response']['text'] = 'Я угадал!'
        # если не нашел, то отвечает пользователю
        # 'Первый раз слышу об этом городе.'
        else:
            res['response']['text'] = \
                'Первый раз слышу об этом городе. Попробуй еще разок!'


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()