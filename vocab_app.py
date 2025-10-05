import streamlit as st
import random

# ======================
# 認証（パスワード制限）
# ======================

def check_password():
    """Secretsに保存されたパスワードで認証"""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # メモリ上から削除
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        st.error("パスワードが違います。")
        st.stop()


check_password()  # ← パスワード認証が通るまでここで止まる


# ======================
# 英単語暗記アプリ本体
# ======================

st.title("📘 英単語暗記アプリ")

# 単語リスト（例：自分で増やせます）
words = {
    "apple": "りんご",
    "book": "本",
    "computer": "コンピュータ",
    "dog": "犬",
    "beautiful": "美しい",
    "knowledge": "知識",
    "courage": "勇気",
    "discover": "発見する",
    "freedom": "自由",
    "honest": "正直な"
}

# ランダムに1単語選択
if "current_word" not in st.session_state:
    st.session_state.current_word = random.choice(list(words.keys()))

st.subheader("次の英単語の意味は？")
st.markdown(f"### **{st.session_state.current_word}**")

# 回答欄
answer = st.text_input("日本語の意味を入力してください")

if answer:
    correct = words[st.session_state.current_word]
    if answer.strip() == correct:
        st.success("🎉 正解！")
    else:
        st.error(f"❌ 不正解。正解は「{correct}」です。")

    if st.button("次の単語へ"):
        st.session_state.current_word = random.choice(list(words.keys()))
        st.rerun()

else:
    # ボタンが押されたときの入力欄初期化
    st.session_state.answer = ""
