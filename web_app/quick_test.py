import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

# 去掉引号
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost').strip('"'),
    'user': os.getenv('DB_USER', 'root').strip('"'),
    'password': os.getenv('DB_PASSWORD', '').strip('"'),
    'database': os.getenv('DB_NAME', 'mysql').strip('"')
}

print("=== 快速测试 L1 查询 ===\n")
print(f"连接到: {DB_CONFIG['database']}")

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("\n查询 L1 领域...")
    cursor.execute("SELECT id, name, description_en FROM knowledge_base WHERE level = 1")
    l1_list = cursor.fetchall()
    
    print(f"✅ 找到 {len(l1_list)} 个 L1 领域:\n")
    for i, (id, name, desc) in enumerate(l1_list[:5], 1):
        print(f"{i}. ID {id}: {name}")
        if desc:
            print(f"   描述: {desc[:80]}...")
    
    print(f"\n... 还有 {len(l1_list) - 5} 个" if len(l1_list) > 5 else "")
    
    conn.close()
    print("\n✅ 数据库查询正常！")
    
except Exception as e:
    print(f"❌ 错误: {e}")
