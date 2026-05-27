import streamlit as st
from ultralytics import YOLO
from PIL import Image
from collections import Counter
import numpy as np

st.set_page_config(page_title="YOLO日常モノ検出アプリ", layout="wide")

st.title("YOLO日常モノ検出アプリ")
st.write("写真をアップロードすると、YOLOが日常の物体を検出します。")

@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")  # 軽量モデル。勉強会デモ向け

model = load_model()

uploaded_file = st.file_uploader(
    "画像をアップロードしてください",
    type=["jpg", "jpeg", "png"]
)

conf = st.slider("信頼度しきい値", 0.1, 1.0, 0.3, 0.05)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("元画像")
        st.image(image, use_container_width=True)

    results = model.predict(image, conf=conf)

    result = results[0]
    plotted = result.plot()
    plotted_rgb = plotted[:, :, ::-1]

    with col2:
        st.subheader("検出結果")
        st.image(plotted_rgb, use_container_width=True)

    names = result.names
    boxes = result.boxes

    detected_names = []
    for cls_id in boxes.cls:
        detected_names.append(names[int(cls_id)])

    counter = Counter(detected_names)

    st.subheader("検出された物体一覧")

    if counter:
        for name, count in counter.items():
            st.write(f"- {name}: {count}個")
    else:
        st.warning("物体が検出されませんでした。信頼度しきい値を下げてください。")

    st.subheader("説明")
    st.write("""
    YOLOは画像の中から物体を探し、
    物体の種類、位置、信頼度を出力します。
    CNNが「画像全体が何か」を分類するのに対し、
    YOLOは「何がどこにあるか」まで検出できます。
    """)