from pyvis.network import Network
from src.constants import COLOR_MAP

def create_schema_visualization(df):
    """創建知識圖譜schema的視覺化"""
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # 獲取所有唯一的節點類型和關係類型
    node_types = set(df['x_type'].unique()) | set(df['y_type'].unique())
    relations = df.groupby(['x_type', 'y_type', 'relation']).size().reset_index()
    
    # 添加節點
    for node_type in node_types:
        color = COLOR_MAP.get(node_type, '#CCCCCC')
        net.add_node(node_type, label=node_type, color=color, size=30)
    
    # 添加邊
    for _, row in relations.iterrows():
        net.add_edge(row['x_type'], row['y_type'], 
                    title=row['relation'], 
                    label=row['relation'],
                    value=row[0])
    
    return net 