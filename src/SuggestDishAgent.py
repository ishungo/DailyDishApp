""" 標準ライブラリのimport """
from typing import List
from pprint import pprint
from datetime import datetime

""" langchain """
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

""" pydantic """
from pydantic import BaseModel, Field

""" 独自関数のimport """
from data_utils import add_grocery_to_list, remove_grocery_from_list
from data_utils import add_dish_list, remove_dish_list
from data_utils import load_dish_list, load_grocery


class MessageClassification(BaseModel):
    """ メッセージの分類結果 """
    classification: int = Field(..., description="メッセージの分類番号")



# ユーザのリクエストを分類する
def request_classifier(llm: ChatOpenAI, messages: List[BaseMessage]) -> str:
    output_parser = PydanticOutputParser(pydantic_object=MessageClassification)
    # ユーザのリクエストを分類する
    format_instructions = output_parser.get_format_instructions()
    system_template = f"""
    以下の会話からユーザのリクエストを分類してください。
    1. 冷蔵庫の食材、食べた料理名を保存しているデータベースへの登録や内容の更新
    2. 冷蔵庫の食材、食べた料理を保存しているデータベースの確認
    3. 食べたい料理のリクエスト
    4. その他
    {format_instructions}
    """
    system = SystemMessage(system_template)
    messages = [system] + messages

    chain = llm | output_parser
    llm_output = chain.invoke(messages)
    return llm_output.classification



# ユーザのリクエストを処理する
def process_request(messages: List[BaseMessage]):
    llm = ChatOpenAI(model='gpt-4.1', streaming=True)
    classification = request_classifier(llm, messages)
    # yield f"リクエストの分類番号は{classification}です。\n\n"
    if classification == 1:
        response = process_db_update_request(llm, messages)
    elif classification == 2:
        response = process_db_show_request(llm, messages)
    elif classification == 3:
        response = today_dish_suggestion(llm, messages)
    elif classification == 4:
        response = simple_chat(llm, messages)
    else:
        response = "内部での処理に失敗しました。"

    # return response
    for text in response:
        yield text



# DB更新リクエストの処理
def process_db_update_request(llm: ChatOpenAI, messages: List[BaseMessage]):
    try:
        # 今日の日付情報を追加
        str_date = datetime.now().strftime('%Y年%m月%d日')
        system_template = f"""今日の日付は{str_date}です"""
        system = SystemMessage(system_template)
        messages = [system] + messages

        tools = [add_grocery_to_list, remove_grocery_from_list, add_dish_list, remove_dish_list]
        llm_with_tools = llm.bind_tools(tools)
        chain = llm_with_tools | PydanticToolsParser(tools=tools)
        chain.invoke(messages)
        status = True
    except Exception as e:
        error_message = f"エラーが発生しました: {e}"
        status = False

    db_info = '\n'.join([show_dish(), show_grocery()])

    if status:
        return f"データベースの更新が完了しました\n\n{db_info}"
    else:
        return f"データベースの更新に失敗しました\n{error_message}\n\n{db_info}"

# DB表示リクエストの処理
def process_db_show_request(llm, messages):
    tools = [show_dish, show_grocery]
    llm_with_tools = llm.bind_tools(tools)
    chain = llm_with_tools | PydanticToolsParser(tools=tools)
    responses = chain.invoke(messages)
    return '\n\n'.join(responses)


def show_grocery():
    """ 冷蔵庫の食材を表示する """
    grocery_list = load_grocery()
    response = "### 冷蔵庫の食材:"
    for grocery in grocery_list:
        response += f"\n{grocery}"
    return response


def show_dish():
    """ 直近食べた料理を表示する """
    dish_list = load_dish_list()
    response = "### 直近食べた料理:"
    for date, dishes in sorted(dish_list.items()):
        response += f"\n{date}:"
        for dish in dishes:
            response += f" {dish}"
    return response


def today_dish_suggestion(llm, messages):
    system_template = f"""
    あなたはユーザの料理を考える専門家です。
    ユーザのリクエストを考慮しつつ今日の料理を提案してください。
    以下の項目を遵守してください。
    1. 冷蔵庫の食材をいくつか使用する料理を提案してください
    2. 直近1週間以内に食べた料理は避けてください。
    3. 一般的な日本の家庭で作ることのできる料理を提案してください。
    4. 一般的な名称の存在している料理を提案してください。
    5. 3~5つの多様な料理を提案してください。
    6. 料理名、1~2行の簡単な説明、7の形式のURLを記載してください
    7. 'https://cookpad.com/jp/search/<料理名>'

    {show_dish()}

    {show_grocery()}
    """
    system = SystemMessage(system_template)
    messages = [system] + messages
    chain = llm | StrOutputParser()
    response = chain.stream(messages)
    return response

def simple_chat(llm, messages):
    chain = llm | StrOutputParser()
    response = chain.stream(messages, stream=True)
    return response



if __name__ == '__main__':
    # messages = [HumanMessage("データを見せて")]
    # messages = [HumanMessage("はじめまして")]
    # messages = [HumanMessage("昨日は赤から鍋を食べた")]
    messages = [HumanMessage("レシピを考えて")]

    ret = ""
    for chunk in process_request(messages):
        ret += chunk
    print(ret)
