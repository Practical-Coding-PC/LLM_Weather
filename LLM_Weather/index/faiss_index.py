import faiss
import numpy as np
import os

# FAISS 인덱스 저장 경로 (절대 경로 사용)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일의 절대 경로
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "faiss_index.bin")

# 인덱스 저장 디렉토리가 없으면 생성
os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)

EMBEDDING_DIM = 384  # MiniLM의 임베딩 차원 (다른 모델을 사용하면 이 값을 수정)

# 기존 FAISS 인덱스 불러오기 (없으면 새로 생성)
if os.path.exists(FAISS_INDEX_PATH):
    index = faiss.read_index(FAISS_INDEX_PATH)
else:
    index = faiss.IndexFlatIP(EMBEDDING_DIM)

# 메타데이터 저장 (임시 저장소, 실제 운영에서는 DB 사용 가능)
docs_store = []

def save_index():
    """ 현재 FAISS 인덱스를 파일로 저장하는 함수 """
    faiss.write_index(index, FAISS_INDEX_PATH)

def add_embedding(embedding, metadata):
    """ 새로운 벡터(임베딩)를 FAISS에 추가하고 저장 """
    vector = np.array([embedding], dtype=np.float32)
    index.add(vector)
    docs_store.append(metadata)
    save_index()  # 인덱스를 파일에 저장

def load_rag_data():
    """ RAG_test.txt 파일에서 데이터를 불러와 FAISS에 추가하는 함수 """
    file_path = os.path.join(os.path.dirname(__file__), "../RAG_test.txt")

    if not os.path.exists(file_path):
        print("⚠️ RAG_test.txt 파일이 존재하지 않습니다.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    added_count = 0
    for line in lines:
        line = line.strip()
        if line:  # 빈 줄은 제외
            embedding = get_embedding(line)
            add_embedding(embedding, {"text": line})  # 문서를 FAISS에 추가
            added_count += 1
            print(f"✅ FAISS에 추가됨: {line}")  # 디버깅 로그 추가

    print(f"✅ 총 {added_count}개의 문서가 FAISS 인덱스에 추가되었습니다.")

def search(query_embedding, k=3):
    """
    입력 벡터(질문 또는 답변)를 FAISS에서 검색하여 관련 문서 반환
    :param query_embedding: 검색할 벡터
    :param k: 검색할 유사 문서 개수
    :return: 검색된 문서 리스트
    """
    query_vector = np.array([query_embedding], dtype=np.float32)
    distances, indices = index.search(query_vector, k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(docs_store):  # 인덱스 범위를 벗어나지 않도록 체크
            results.append(docs_store[idx])
    print("#######################success!")
    return results


# RAG 데이터 로드 실행
load_rag_data()
