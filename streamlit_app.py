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
conn = sqlite3.connect('english_dictionary.db')
c = conn.cursor()

# 테이블 생성 (이미 존재하지 않는 경우)
c.execute('''CREATE TABLE IF NOT EXISTS words
             (id INTEGER PRIMARY KEY, word TEXT, definition TEXT, translation TEXT, date_added DATE)''')

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
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful English dictionary assistant. Provide definitions, examples, and synonyms for English words."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        english_response = response.choices[0].message.content
        korean_response = translator.translate(english_response)
        return english_response, korean_response
    except Exception as e:
        return f"An error occurred: {str(e)}", "오류가 발생했습니다."

# 단어 저장 함수
def save_word(word, definition, translation):
    c.execute("INSERT INTO words (word, definition, translation, date_added) VALUES (?, ?, ?, ?)",
              (word, definition, translation, datetime.now().date()))
    conn.commit()

# 랜덤 단어 가져오기 함수
def get_random_word():
    c.execute("SELECT word, definition, translation FROM words ORDER BY RANDOM() LIMIT 1")
    return c.fetchone()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "review_word" not in st.session_state:
    st.session_state.review_word = None
if "show_meaning" not in st.session_state:
    st.session_state.show_meaning = False

# 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "translation" in message:
            st.markdown("???? 한글 번역:")
            st.markdown(message["translation"])

# 사용자 입력 처리
#input_text = "영어 단어를 입력하세요 (예: 'apple의 뜻', 'book 예문', 'computer 동의어')"
input_text = "영어 단어를 입력하세요 (예: apple)"
prompt = st.chat_input(input_text)

if prompt:
    # 영어와 공백만 허용하는 정규 표현식
    if re.match(r'^[a-zA-Z\s]+$', prompt):
        st.session_state.review_word = None
        # 사용자 메시지 표시 및 저장
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 챗봇 응답 생성 및 번역
        english_response, korean_response = get_chatbot_response(prompt)

        # 챗봇 응답 표시 및 저장
        with st.chat_message("assistant"):
            st.markdown(english_response)
            st.markdown("🌐 한글 번역:")
            st.markdown(korean_response)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": english_response,
            "translation": korean_response
        })

        # 단어 저장
        if "Definition:" in english_response:
            word = prompt
            save_word(word, english_response, korean_response)
            st.success(f"'{word}' 단어가 데이터베이스에 저장되었습니다.")
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
        st.warning("저장된 단어가 없습니다.")

if st.session_state.review_word:
    word, definition, translation = st.session_state.review_word
    st.info(f"복습할 단어: {word}")
    if st.button("뜻 보기"):
        st.session_state.show_meaning = True

    translation = translation.replace("정의:", "");

    if st.session_state.show_meaning:
        st.write("정의:")
        st.write(f"{definition}")
        st.write("번역:")
        st.write(f"{translation}")

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