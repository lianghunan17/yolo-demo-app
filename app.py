import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2
from collections import Counter
import json
from pathlib import Path

st.set_page_config(
    page_title="YOLO日常モノ検出アプリ",
    layout="wide"
)

st.title("YOLO日常モノ検出アプリ")
st.write("画像をアップロードすると、YOLOが日常の物体を検出します。日本語名で絞り込みもできます。")

# -------------------------
# ラベルファイル読み込み
# -------------------------
@st.cache_data
def load_labels():
    label_path = Path("labels_ja.json")

    if not label_path.exists():
        st.error("labels_ja.json が見つかりません。")
        st.stop()

    with open(label_path, "r", encoding="utf-8") as f:
        labels = json.load(f)

    return labels

LABELS = load_labels()

# 英語 → 日本語
def to_ja(label_en: str) -> str:
    if label_en in LABELS:
        return LABELS[label_en].get("ja", label_en)
    return label_en

# 日本語・別名 → 英語
def build_alias_map(labels: dict) -> dict:
    alias_map = {}

    for en, data in labels.items():
        ja = data.get("ja", en)
        aliases = data.get("aliases", [])

        # 英語自体でも検索できるようにする
        alias_map[en.lower()] = en

        # 日本語正式名
        alias_map[ja.lower()] = en

        # 別名
        for alias in aliases:
            alias_map[alias.lower()] = en

    return alias_map

ALIAS_MAP = build_alias_map(LABELS)

@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

model = load_model()

st.sidebar.header("検出設定")

target_input = st.sidebar.text_input(
    "検出したい物を入力（例：人、犬、カップ、スマホ、PC）",
    value=""
)

conf = st.sidebar.slider(
    "信頼度しきい値",
    min_value=0.1,
    max_value=1.0,
    value=0.3,
    step=0.05
)

uploaded_file = st.file_uploader(
    "画像をアップロードしてください",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image_np = np.array(image)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("元画像")
        st.image(image, use_container_width=True)

    results = model.predict(image, conf=conf)
    result = results[0]

    output_img = image_np.copy()

    detected_list = []
    filtered_list = []

    target_input = target_input.strip().lower()

    if target_input:
        target_en = ALIAS_MAP.get(target_input)
    else:
        target_en = None

    box_id = 1

    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf_score = float(box.conf[0])
        label_en = result.names[cls_id]
        label_ja = to_ja(label_en)

        detected_list.append(label_ja)

        # 入力あり、かつ対象外なら描画しない
        if target_en and label_en != target_en:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        cv2.rectangle(
            output_img,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )

        # 日本語描画は環境依存があるため、画像上は番号表示
        cv2.putText(
            output_img,
            f"{box_id}: {conf_score:.2f}",
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        filtered_list.append({
            "No": box_id,
            "英語名": label_en,
            "日本語名": label_ja,
            "信頼度": round(conf_score, 3)
        })

        box_id += 1

    with col2:
        st.subheader("検出結果")
        st.image(output_img, use_container_width=True)

    st.subheader("検出された物体一覧")

    if detected_list:
        counter = Counter(detected_list)

        for name, count in counter.items():
            st.write(f"- {name}: {count}個")
    else:
        st.warning("物体が検出されませんでした。")

    st.subheader("絞り込み結果")

    if target_input:
        if target_en is None:
            st.warning(f"「{target_input}」は対応ラベルにありません。")
            st.info("例：人、犬、猫、カップ、スマホ、PC、椅子、車 など")
        elif filtered_list:
            st.table(filtered_list)
        else:
            st.warning(f"「{target_input}」は検出されませんでした。")
    else:
        st.info("左側に検出したい物を入力すると、その物だけ表示できます。")

    st.subheader("説明")
    st.write("""
    このアプリでは、YOLOを使って画像内の物体を検出しています。
    英語ラベルは labels_ja.json で日本語に変換しています。
    画像上の番号と、下の表の番号が対応しています。
    """)