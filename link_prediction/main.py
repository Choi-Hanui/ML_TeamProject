# python -m link_prediction.main

# main.py
import torch
from link_prediction.cgcnn import CGCNN  # 모델 클래스와 디바이스 가져오기
from link_prediction.similarity import calculate_similarity  # 유사도 계산 함수
from link_prediction.cgcnn import load_graph_from_lists,find_closest_name,train  # 그래프 로드 함수
device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def find_closest_couple(target_name, node_names, gender_map, target_gender):
    """
    Find the closest match to `target_name` in `node_names` using difflib,
    restricted to nodes of a specific gender.
    
    Parameters:
    - target_name: The name to find a match for.
    - node_names: List of available node names.
    - gender_map: A dictionary mapping node names to their genders.
    - target_gender: The gender ('M' or 'F') to filter node names.
    
    Returns:
    - Closest node name of the specified gender or None.
    """
    # Filter node names by target gender
    filtered_names = [name for name in node_names if gender_map.get(name, '') == target_gender]
    
    # Find closest match among filtered names
    matches = difflib.get_close_matches(target_name.lower(), filtered_names, n=1, cutoff=0.6)
    return matches[0] if matches else None


# 모델 파라미터 설정
node_features = 2  # 노드 특징 차원
edge_features = 2  # 엣지 특징 차원
hidden_channels = 64  # 은닉 채널 수

# 모델 초기화 및 로드
model = CGCNN(node_features=node_features, edge_features=edge_features, hidden_channels=hidden_channels).to(device)
iftrain=True
if iftrain:
    print('train_start')
    train(2001)
model_load_path = "./trained_model1000step.pth"
model.load_state_dict(torch.load(model_load_path, map_location=device,weights_only=True))
model.eval()  # 평가 모드로 전환
print(f"Model loaded from {model_load_path}")

# 테스트 데이터 로드
edge_list_path = './graphs/APairOfBlueEyes combined graph.edgelist'
node_list_path = './graphs/APairOfBlueEyes gender.nodelist'
test_graph, mapping = load_graph_from_lists(edge_list_path, node_list_path)
test_graph = test_graph.to(device)


lower_mapping = {node.lower(): node for node in mapping.keys() if isinstance(node, str)}
node_names_lower = list(lower_mapping.keys())
raw_labels = {
        "APairOfBlueEyes": ("swancourt", "knight"), # 엘프리다 스완코트 & 헨리 나이트 & 스티븐 스미스  왜 학습이 되징..?  엥...? 뭐냥 이거
        #"APairOfBlueEyes": ("swancourt", "smith"), # 엘프리다 스완코트 & 헨리 나이트 & 스티븐 스미스 셋이 삼각관계인데 누구와도 이루어지지 못하고 죽습니다
    }

# Find closest matches for raw_labels
raw_label_0, raw_label_1 = raw_labels["APairOfBlueEyes"]
closest_0 = find_closest_name(raw_label_0, node_names_lower)
closest_1 = find_closest_name(raw_label_1, node_names_lower)

# Replace with closest matches and log changes
if closest_0 and closest_1:
    #print(f"In {name}, replacing '{raw_label_0}' with '{closest_0}' and '{raw_label_1}' with '{closest_1}'")
    label = torch.tensor([mapping[lower_mapping[closest_0]], mapping[lower_mapping[closest_1]]])
    
else:
    print(f"Warning: Could not find a match for one or both labels in {name}. Skipping this graph.")


print(test_graph.x)

# 모델로 노드 특성 추출
with torch.no_grad():
    output_vectors = model(test_graph.x, test_graph.edge_index, test_graph.edge_attr)

# 노드 간 유사도 계산
similarity_matrix = calculate_similarity(output_vectors,label)
print(label)
print(similarity_matrix)

predicted_nodes =similarity_matrix.argmax(dim=1)

'''

# 유사도가 가장 높은 노드 쌍 예측
i, j = torch.triu_indices(similarity_matrix.size(0), similarity_matrix.size(1), 1)  # 상삼각 행렬의 인덱스 추출
predicted_indices = similarity_matrix[i, j].argmax()  # 유사도가 가장 높은 인덱스 찾기
predicted_nodes = (i[predicted_indices].item(), j[predicted_indices].item())  # 가장 높은 유사도를 갖는 노드 쌍
'''
# 예측 결과 출력
reverse_mapping = {v: k for k, v in mapping.items()}  # 숫자 인덱스를 노드 이름으로 매핑
predicted_node_names = (reverse_mapping[predicted_nodes[0].item()], reverse_mapping[predicted_nodes[1].item()])

print(f"Predicted Node Names: {predicted_node_names}")
print('May be '+closest_0+' fall in love to '+predicted_node_names[0])
print('May be '+closest_1+' fall in love to '+predicted_node_names[1])