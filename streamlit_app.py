import streamlit as st
from openai import OpenAI
from deep_translator import GoogleTranslator
import sqlite3
from datetime import datetime
from PIL import Image
import re

# OpenAI 클라이언트 초기화
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key= st.secrets["openai"]["api_key"])

# Google Translator 초기화
translator = GoogleTranslator(source='auto', target='ko')

# SQLite 데이터베이스 연결
conn = sqlite3.connect('english_korea_dictionary.db')
c = conn.cursor()

# 테이블 생성 (이미 존재하지 않는 경우)
c.execute('''CREATE TABLE IF NOT EXISTS words
             (id INTEGER PRIMARY KEY, word TEXT, definitionContents TEXT, createdDate DATE, updatedDate DATE)''')

# 이미지 파일 경로
image_path = "./img/drizzlenote.png"

# 이미지 로드
image = Image.open(image_path)

# 이미지 크기 지정 (픽셀 단위)
image_width = 1792  # 원하는 가로 크기
image_height = 512  # 원하는 세로 크기

image = image.resize((image_width, image_height))

# 이미지 표시
#st.image(image, caption='', use_column_width=True)
#st.image(image, caption='', width=image_width, height=image_height)
st.image(image, caption='')

# CSS를 사용하여 제목 스타일 지정
st.markdown("""
    <style>
    .title-center {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 가운데 정렬된 제목 표시
st.markdown("<h1 class='title-center'>🎈단비노트 챗봇서비스🎈</h1>", unsafe_allow_html=True)

#st.title("🎈단비노트 챗봇서비스🎈")

# 챗봇 응답 생성 및 번역 함수
def get_chatbot_response(prompt):
    try:
        response = client.chat.completions.create(
        model="gpt-4",  # 또는 "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": """당신은 고급 영어 사전 도우미입니다. 각 단어에 대해 다음 정보를 구조화된 형식으로 제공하세요:

        1. 한국어
        2. 품사 (명사, 동사, 형용사 등)
        3. 발음 (IPA 표기법 사용)
        4. 정의 (번호로 구분, 영어와 한국어 포함 - 예) Beautiful(아름다운))
        5. 각 정의에 대한 예문(한국어 포함 - 예) The sunset was beautiful.(석양이 아름다웠다.))
        6. 관용구 또는 숙어 (해당되는 경우, 한국어 포함 - 예) Beauty is in the eye of the beholder.(아름다움은 보는 사람의 눈에 달려있다.))

        가독성을 높이기 위해 마크다운을 사용하여 응답을 형식화하세요. 제목에는 굵은 글씨를, 부제목에는 기울임꼴을 사용하세요.

        항상 영어 단어나 문장 뒤에 괄호를 사용하여 한국어 번역을 제공하세요. 예시:
        - Word(단어)
        - This is an example.(이것은 예시입니다.)
        - To kill two birds with one stone(일석이조)
             
        입력한 단어가 없는 단어이거나 오타인 경우 아래와 같이 한국어 번역을 제공하세요. 예시:
        - 오류: 입력한 단어가 영어 사전에 없는 단어이거나 오타가 있습니다.

        모든 응답에서 이 형식을 일관되게 유지하세요."""},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"


# 단어 저장(등록) 함수
def creat_word(word, definitionContents):
    if not word or not response:
        return False
    
    c.execute("INSERT INTO words (word, definitionContents, createdDate, updatedDate) VALUES (?, ?, ?, ?)",
              (word, definitionContents, datetime.now().date(), datetime.now().date()))
    conn.commit()

    return True

# 단어 저장(수정) 함수
def modify_word(word, definitionContents):
    if not word or not response:
        return False
    
    c.execute("UPDATE words SET definitionContents = ?, updatedDate = ? WHERE word = ?",
              (definitionContents, datetime.now().date(), word))
    conn.commit()

    return True

# 조건절에 오는 단어정보 가져오기 함수
def get_wordInfoByWord(word):
    c.execute("SELECT word FROM words WHERE word = ? LIMIT 1", (word,))
    return c.fetchone()

# 랜덤 단어 가져오기 함수
def get_random_word():
    c.execute("SELECT word, definitionContents FROM words WHERE updatedDate <= date('now', '-2 days') ORDER BY RANDOM() LIMIT 1")
    return c.fetchone()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "review_word" not in st.session_state:
    st.session_state.review_word = None
if "show_meaning" not in st.session_state:
    st.session_state.show_meaning = False
if 'word_saved' not in st.session_state:
    st.session_state.word_saved = False
if 'saved_word' not in st.session_state:
    st.session_state.saved_word = ""

# 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
input_text = "영어 단어를 입력하세요 (예: apple)"
prompt = st.chat_input(input_text)

if prompt:
    # 영어와 공백만 허용하는 정규 표현식
    if re.match(r'^[a-zA-Z\s]+$', prompt):
        st.session_state.review_word = None
        # 사용자 메시지 표시 및 저장
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 챗봇 응답 생성
        response = get_chatbot_response(prompt)

        # 챗봇 응답 표시 및 저장
        with st.chat_message("assistant"):
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        # 단어 저장 버튼
        if "입력한 단어가 영어 사전에 없는 단어이거나 오타가 있습니다." not in response:
            word = prompt 
            get_word = get_wordInfoByWord(word)

            if get_word == None :
                if creat_word(word, response):  # 데이터베이스에 저장(등록)
                    st.session_state.word_saved = True
                    st.session_state.saved_word = word
                    st.success(f"'{word}' 단어가 데이터베이스에 저장(등록)되었습니다.")
                else:
                    st.error("단어 저장에 실패했습니다.")
            else:
                if modify_word(word, response):  # 데이터베이스에 저장(수정)
                    st.session_state.word_saved = True
                    st.session_state.saved_word = word
                    st.success(f"'{word}' 단어가 데이터베이스에 저장(수정)되었습니다.")
                else:
                    st.error("단어 저장에 실패했습니다.")

    else:
        st.error("영어 단어만 입력해주세요.")

# 복습 기능
#if st.button("랜덤 단어 복습"):
#    word_data = get_random_word()
#    if word_data:
#        word, definition, translation = word_data
#        st.info(f"복습할 단어: {word}")
#        if st.button("뜻 보기"):
#            st.write(f"정의: {definition}")
#            st.write(f"번역: {translation}")
#    else:
#        st.warning("저장된 단어가 없습니다.")

if st.button("랜덤 단어 복습"):
    st.session_state.review_word = get_random_word()
    st.session_state.show_meaning = False

    if st.session_state.review_word == None:
        st.warning("2일 이전에 저장된 단어가 없습니다.")

if st.session_state.review_word:
    word, definitionContents = st.session_state.review_word
    st.info(f"복습할 단어: {word}")
    if st.button("뜻 보기"):
        st.session_state.show_meaning = True

    if st.session_state.show_meaning:
        st.write(f"{definitionContents}")

# 사이드바에 사용 설명 추가
#st.sidebar.title("사용 방법")
#st.sidebar.markdown("""
#1. 영어 단어의 뜻을 알고 싶으면: '[단어]의 뜻'
#2. 예문을 보고 싶으면: '[단어] 예문'
#3. 동의어를 알고 싶으면: '[단어] 동의어'
#4. 응답은 영어와 한글 번역으로 제공됩니다.
#5. '의 뜻'을 물어본 단어는 자동으로 저장됩니다.
#6. '랜덤 단어 복습' 버튼을 클릭하여 저장된 단어를 복습할 수 있습니다.
#)

# 데이터베이스 연결 종료
conn.close()