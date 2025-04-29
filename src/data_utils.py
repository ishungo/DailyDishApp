from langchain_openai import ChatOpenAI
from typing import List
from datetime import datetime, timedelta
from pathlib import Path
import json

from langchain_core.output_parsers.openai_tools import PydanticToolsParser

SCRIPT_DIR = Path(__file__).parent

APP_BASE_DIR = SCRIPT_DIR.parent
import dotenv
""" ここでAPIキーを読み込む """
dotenv.load_dotenv(APP_BASE_DIR / 'env')

""" パスの定義 """
DAILY_DISH_JSON_PATH = APP_BASE_DIR / 'data' / 'daily_dish.json'
GROCERY_JSON_PATH = APP_BASE_DIR / 'data' / 'grocery.json'


def load_grocery() -> set:
    """ 所持している食材の情報を読み込む """
    if not GROCERY_JSON_PATH.exists(): return set()
    groceries = json.load(GROCERY_JSON_PATH.open('r'))
    return set(groceries['groceries'])


def save_grocery(grocery_list: set):
    """ 変更された食材の情報を保存する """
    json_data = {'groceries': list(grocery_list)}
    with open(GROCERY_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)


def add_grocery_to_list(grocery: str):
    """ 食材の情報をリストに追加する """
    # 既存の食材リストを読み込む
    grocery_list = load_grocery()
    # 新しい食材を追加
    grocery_list.add(grocery)
    # 保存
    save_grocery(grocery_list)


def remove_grocery_from_list(grocery: str):
    """ 食材の情報をリストから削除する """
    # 既存の食材リストを読み込む
    grocery_list = load_grocery()
    # 食材を削除
    if grocery in grocery_list:
        grocery_list.remove(grocery)
    # 保存
    save_grocery(grocery_list)


def load_dish_list() -> dict:
    """ 作った料理の情報を読み込む """
    if not DAILY_DISH_JSON_PATH.exists(): return {}
    dish_list  = json.load(DAILY_DISH_JSON_PATH.open('r'))
    date_list = sorted(dish_list.keys())
    for key in date_list:
        dish_list[key] = set(dish_list[key])
    return dish_list


def save_dish_list(dish_list: dict):
    """ 変更された料理の情報を保存する """
    date_list = sorted(dish_list.keys())
    for key in date_list:
        dish_list[key] = list(dish_list[key])
        if len(dish_list[key]) == 0: dish_list.pop(key)
    with open(DAILY_DISH_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(dish_list, f, indent=4, ensure_ascii=False)



def add_dish_list(dish: str, days_ago: int = 0):
    """ 作った料理の情報をリストに追加する
    days_ago: 何日前に作った料理か
    dish: 作ったもしくは食べた料理名
    """
    date = datetime.now().date() - timedelta(days=days_ago)
    date_str = date.strftime('%Y-%m-%d')
    dish_list = load_dish_list()
    if date_str not in dish_list:
        dish_list[date_str] = {dish}
    else:
        dish_list[date_str].add(dish)
    save_dish_list(dish_list)


def remove_dish_list(dish: str, days_ago: int = 0):
    """ 作った料理の情報をリストから削除する
    days_ago: 何日前に作った料理か
    dish: リストから消す料理名
    """
    date = datetime.now().date() - timedelta(days=days_ago)
    date_str = date.strftime('%Y-%m-%d')
    dish_list = load_dish_list()
    if date_str in dish_list and dish in dish_list[date_str]:
        dish_list[date_str].remove(dish)
    save_dish_list(dish_list)


if __name__ == '__main__':
    llm = ChatOpenAI(model='gpt-4o-mini')
    tools = [add_grocery_to_list, remove_grocery_from_list, add_dish_list, remove_dish_list]
    llm_with_tools = llm.bind_tools(tools)
    chain = llm_with_tools | PydanticToolsParser(tools=tools)
    chain.invoke('麻婆豆腐を食べた')
    # chain.invoke('ぶどうを使って、たけのこを買い足した')
