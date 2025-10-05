# vocab_app.py
# 英単語暗記用アプリ（Streamlit）
# 使い方:
# 1. Python 3.8+ と streamlit, pandas をインストール
#    pip install streamlit pandas
# 2. このファイルを保存して、
#    streamlit run vocab_app.py

import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import os

# デフォルトデータファイル名
DATA_FILE = "vocab.csv"

st.set_page_config(page_title="英単語暗記アプリ", layout="centered")

# --- ユーティリティ関数 ---

def load_data(path=DATA_FILE):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, parse_dates=["added", "next_review"])
            # 型補正
            if "box" not in df.columns:
                df["box"] = 1
            return df
        except Exception as e:
            st.error(f"データ読み込み失敗: {e}")
            return pd.DataFrame(columns=["word","meaning","example","box","added","next_review","correct","wrong"]) 
    else:
        return pd.DataFrame(columns=["word","meaning","example","box","added","next_review","correct","wrong"]) 


def save_data(df, path=DATA_FILE):
    df.to_csv(path, index=False)


def add_word(df, word, meaning, example=""):
    now = datetime.now()
    new = {
        "word": word.strip(),
        "meaning": meaning.strip(),
        "example": example.strip(),
        "box": 1,
        "added": now,
        "next_review": now,
        "correct": 0,
        "wrong": 0,
    }
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    return df


def schedule_next(box):
    # 単純なLeitner方式: ボックスが上がるほど次回レビュー日が延びる
    days = {1:1, 2:3, 3:7, 4:14, 5:30}
    return datetime.now() + timedelta(days=days.get(box, 1))


def pick_due_words(df, limit=20):
    now = datetime.now()
    if df.empty:
        return df
    due = df[df["next_review"].isna() | (df["next_review"] <= now)].copy()
    return due.sample(n=min(limit, len(due)), random_state=random.randint(1,10000))

# --- UI ---

st.title("📚 英単語暗記アプリ")
st.markdown("Leitner（ライトナー）方式を使ったシンプルな暗記アプリです。単語を追加して学習・確認できます。データはローカル CSV に保存されます。")

# サイドバー: データ操作
st.sidebar.header("データ管理")
if "df" not in st.session_state:
    st.session_state.df = load_data()

if st.sidebar.button("保存する（手動）"):
    save_data(st.session_state.df)
    st.sidebar.success("保存しました")

uploaded = st.sidebar.file_uploader("CSV をインポート（word,meaning,example が列にあること）", type=["csv"] )
if uploaded is not None:
    try:
        df_up = pd.read_csv(uploaded)
        # 最低限のカラム処理
        for c in ["word","meaning","example"]:
            if c not in df_up.columns:
                df_up[c] = ""
        df_up = df_up[["word","meaning","example"]]
        # 新しい単語を現在の DataFrame に追加
        for _, r in df_up.iterrows():
            if len(r["word"].strip())>0:
                st.session_state.df = add_word(st.session_state.df, r["word"], r["meaning"], r.get("example",""))
        save_data(st.session_state.df)
        st.sidebar.success("インポート完了")
    except Exception as e:
        st.sidebar.error(f"インポート失敗: {e}")

if st.sidebar.button("CSV エクスポート"):
    save_data(st.session_state.df)
    with open(DATA_FILE, "rb") as f:
        st.sidebar.download_button("ダウンロード", data=f, file_name=DATA_FILE, mime="text/csv")

if st.sidebar.checkbox("表示: すべての単語", value=False):
    st.sidebar.dataframe(st.session_state.df)

# メイン: タブ
tab = st.tabs(["単語追加","学習（確認）","ランダムクイズ","統計・管理"]) 

# ---- 単語追加タブ ----
with tab[0]:
    st.header("単語を追加")
    with st.form("add_form"):
        w = st.text_input("英単語 (word)")
        m = st.text_input("意味 (meaning)")
        e = st.text_area("例文 (任意)")
        submitted = st.form_submit_button("追加")
        if submitted:
            if w.strip() == "" or m.strip() == "":
                st.warning("単語と意味は必須です")
            else:
                st.session_state.df = add_word(st.session_state.df, w, m, e)
                save_data(st.session_state.df)
                st.success(f"単語 '{w}' を追加しました")

    st.markdown("---")
    st.subheader("既存単語の編集・削除")
    if st.session_state.df.empty:
        st.info("まだ単語がありません。左上のフォームから追加してください。")
    else:
        edit_idx = st.number_input("編集する行番号 (0-start)", min_value=0, max_value=max(0,len(st.session_state.df)-1), value=0, step=1)
        r = st.session_state.df.loc[edit_idx]
        with st.form("edit_form"):
            ew = st.text_input("英単語", value=r["word"]) 
            em = st.text_input("意味", value=r["meaning"]) 
            ee = st.text_area("例文", value=r.get("example",""))
            ebox = st.selectbox("Box", options=[1,2,3,4,5], index=int(r.get("box",1))-1)
            save_btn = st.form_submit_button("更新")
            del_btn = st.form_submit_button("削除")
            if save_btn:
                st.session_state.df.at[edit_idx, "word"] = ew
                st.session_state.df.at[edit_idx, "meaning"] = em
                st.session_state.df.at[edit_idx, "example"] = ee
                st.session_state.df.at[edit_idx, "box"] = ebox
                save_data(st.session_state.df)
                st.success("更新しました")
            if del_btn:
                st.session_state.df = st.session_state.df.drop(index=edit_idx).reset_index(drop=True)
                save_data(st.session_state.df)
                st.success("削除しました")

# ---- 学習（確認）タブ ----
with tab[1]:
    st.header("学習（確認）")
    due = pick_due_words(st.session_state.df, limit=30)
    if due.empty:
        st.info("今日レビューする単語はありません。新しい単語を追加するか、ボックスを下げてください。")
    else:
        st.write(f"レビュー候補: {len(due)} 単語")
        # show one by one
        if "study_idx" not in st.session_state:
            st.session_state.study_idx = 0
            st.session_state.study_order = due.index.tolist()
        if st.session_state.study_idx >= len(st.session_state.study_order):
            st.success("レビュー完了！")
            if st.button("最初からやり直す"):
                st.session_state.study_idx = 0
        else:
            cur_idx = st.session_state.study_order[st.session_state.study_idx]
            cur = st.session_state.df.loc[cur_idx]
            st.subheader(f"{st.session_state.study_idx+1} / {len(st.session_state.study_order)}")
            st.markdown(f"**単語:** {cur['word']}")
            show_answer = st.checkbox("意味を表示する", value=False)
            if show_answer:
                st.markdown(f"**意味:** {cur['meaning']}")
                if cur.get("example",""):
                    st.markdown(f"例文: {cur['example']}")
            col1, col2 = st.columns(2)
            if col1.button("正解 (覚えた)"):
                # 正解: box +1 (最大5), next_review 延長
                new_box = min(5, int(cur.get("box",1))+1)
                st.session_state.df.at[cur_idx, "box"] = new_box
                st.session_state.df.at[cur_idx, "next_review"] = schedule_next(new_box)
                st.session_state.df.at[cur_idx, "correct"] = int(cur.get("correct",0)) + 1
                save_data(st.session_state.df)
                st.session_state.study_idx += 1
                st.experimental_rerun()
            if col2.button("不正解 (復習必要)"):
                # 間違い: box を 1 に戻す（または -1）
                new_box = max(1, int(cur.get("box",1)) - 1)
                st.session_state.df.at[cur_idx, "box"] = new_box
                st.session_state.df.at[cur_idx, "next_review"] = schedule_next(new_box)
                st.session_state.df.at[cur_idx, "wrong"] = int(cur.get("wrong",0)) + 1
                save_data(st.session_state.df)
                st.session_state.study_idx += 1
                st.experimental_rerun()

# ---- ランダムクイズタブ ----
with tab[2]:
    st.header("ランダムクイズ")
    mode = st.radio("出題形式", options=["英単語 -> 意味 (記述)", "英単語 -> 意味 (選択)", "意味 -> 単語 (選択)"])
    if st.session_state.df.empty:
        st.info("単語を追加してください")
    else:
        quiz_count = st.slider("問題数", 1, 20, 5)
        pool = st.session_state.df.sample(n=min(len(st.session_state.df), 200), replace=False)
        questions = pool.sample(n=min(quiz_count, len(pool)), random_state=random.randint(1,10000))
        score = 0
        for i, (_, q) in enumerate(questions.reset_index().iterrows()):
            st.write(f"### 問{i+1}")
            if mode == "英単語 -> 意味 (記述)":
                st.write(q['word'])
                ans = st.text_input(f"あなたの答え (問{i+1})", key=f"q{i}")
                if st.button(f"回答送信 (問{i+1})", key=f"btn{i}"):
                    if ans.strip().lower() == q['meaning'].strip().lower():
                        st.success("正解！")
                        score += 1
                    else:
                        st.error(f"不正解。正しい意味: {q['meaning']}")
            elif mode == "英単語 -> 意味 (選択)":
                st.write(q['word'])
                # 選択肢を作る
                wrongs = st.session_state.df[st.session_state.df.index != q['index']].sample(n=min(3, max(0,len(st.session_state.df)-1))).meaning.tolist()
                opts = wrongs + [q['meaning']]
                random.shuffle(opts)
                pick = st.radio("選択肢", options=opts, key=f"mc{i}")
                if st.button(f"回答送信 (問{i+1})", key=f"btnmc{i}"):
                    if pick == q['meaning']:
                        st.success("正解！")
                        score += 1
                    else:
                        st.error(f"不正解。正しい意味: {q['meaning']}")
            else: # 意味 -> 単語 (選択)
                st.write(q['meaning'])
                wrongs = st.session_state.df[st.session_state.df.index != q['index']].sample(n=min(3, max(0,len(st.session_state.df)-1))).word.tolist()
                opts = wrongs + [q['word']]
                random.shuffle(opts)
                pick = st.radio("選択肢", options=opts, key=f"mc2{i}")
                if st.button(f"回答送信 (問{i+1})", key=f"btnmc2{i}"):
                    if pick == q['word']:
                        st.success("正解！")
                        score += 1
                    else:
                        st.error(f"不正解。正しい単語: {q['word']}")
        st.markdown("---")
        st.write("※このクイズは簡易的な実装です。より高度な採点やヒント機能を追加できます。")

# ---- 統計・管理タブ ----
with tab[3]:
    st.header("統計・管理")
    df = st.session_state.df
    st.write(f"総単語数: {len(df)}")
    if not df.empty:
        box_counts = df['box'].value_counts().reindex([1,2,3,4,5], fill_value=0)
        st.write("ボックス内訳:")
        st.table(box_counts.rename("count").reset_index().rename(columns={"index":"box"}))
        if 'correct' in df.columns:
            total_correct = int(df['correct'].sum())
            total_wrong = int(df['wrong'].sum())
            st.write(f"正答回数合計: {total_correct} / 間違い回数合計: {total_wrong}")
        # 次回レビューが近いもの
        due_soon = df[df['next_review'] <= (datetime.now() + timedelta(days=1))] if 'next_review' in df.columns else pd.DataFrame()
        st.write(f"明日までにレビュー予定の単語: {len(due_soon)}")
        if len(due_soon) > 0:
            st.table(due_soon[['word','meaning','box','next_review']].sort_values('next_review'))

    if st.button("サンプル単語を追加 (デモ用)"):
        samples = [
            ("apple","りんご","I eat an apple."),
            ("study","勉強する","I study English every day."),
            ("important","重要な","This is important."),
            ("achieve","達成する","She achieved her goal."),
        ]
        for w,m,e in samples:
            st.session_state.df = add_word(st.session_state.df, w, m, e)
        save_data(st.session_state.df)
        st.success("サンプルを追加しました")

    if st.button("データを初期化（全削除）"):
        if st.confirm("本当に全ての単語を削除しますか？ この操作は元に戻せません。"):
            st.session_state.df = pd.DataFrame(columns=["word","meaning","example","box","added","next_review","correct","wrong"]) 
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.success("データを初期化しました")

# 最後に自動保存（軽い操作）
save_data(st.session_state.df)

st.sidebar.markdown("---")
st.sidebar.caption("このアプリはローカル CSV にデータを保存します。バックアップをとってください。改造・機能追加は歓迎です！")

# EOF
