"""
知识库生成配置文件
用于集中管理所有生成参数
"""

# ==================== 数据库配置 ====================
# 注意：实际的数据库凭证应该放在 .env 文件中
# 这里的配置仅作为默认值参考

# ==================== L1 领域生成配置 ====================
L1_CONFIG = {
    "max_domains": 100,  # L1领域数量上限
    "temperature": 0.7,  # 大模型temperature参数（0.0-1.0，越高越随机）
    "description_length": "2-3",  # 描述长度（句子数）
}

# ==================== L2 场景生成配置 ====================
L2_CONFIG = {
    "max_per_parent": 10,  # 每个L1领域生成的L2场景数量
    "temperature": 0.7,
    "description_length": "1-2",
}

# ==================== L3 子场景生成配置 ====================
L3_CONFIG = {
    "max_per_parent": 8,  # 每个L2场景生成的L3子场景数量
    "temperature": 0.7,
    "description_length": "1-2",
}

# ==================== L4 用户意图生成配置 ====================
L4_CONFIG = {
    "max_per_parent": 6,  # 每个L3子场景生成的L4意图数量
    "temperature": 0.6,  # L4更具体，可以降低随机性
    "description_length": "1",
}

# ==================== API配置 ====================
API_CONFIG = {
    "delay_between_calls": 1,  # API调用之间的延迟（秒）
    "timeout": 120,  # API请求超时时间（秒）
    "max_retries": 3,  # 失败重试次数
    "max_tokens": 2048,  # 单次请求最大token数
}

# ==================== 模型提供商配置 ====================
# 支持的提供商: silicon_flow, openrouter, ollama
MODEL_PROVIDERS = {
    "silicon_flow": {
        "api_url": "https://api.siliconflow.cn/v1/chat/completions",
        "default_model": "alibaba/Qwen2-7B-Instruct",
        "supports_json_mode": True,
    },
    "openrouter": {
        "api_url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "google/gemini-2.0-flash-exp:free",
        "supports_json_mode": True,
    },
    "ollama": {
        "api_url": "http://localhost:11434/v1/chat/completions",
        "default_model": "llama2",
        "supports_json_mode": False,
    },
}

# ==================== 批量生成配置 ====================
BATCH_CONFIG = {
    "enable_l2": True,  # 是否生成L2
    "enable_l3": True,  # 是否生成L3
    "enable_l4": True,  # 是否生成L4
    "stop_on_error": False,  # 遇到错误是否停止（False则跳过继续）
}

# ==================== 产品定位描述（用于提示词） ====================
PRODUCT_CONTEXT = """
A subscription-based iOS app targeting the North American market.
The app helps users make better life decisions by combining Eastern metaphysics 
(Five Elements, astrology, Eastern divination) with practical guidance.
Target audience: North American users who follow astrology, Eastern philosophy, 
or struggle with decision-making, primarily from YouTube and Instagram.
"""

# ==================== 预设的示例（可选） ====================
# 如果您想为某些层级提供示例以引导生成，可以在这里配置
EXAMPLES = {
    "l1_domains": [
        "Career & Professional Development",
        "Love & Romantic Relationships",
        "Family & Parenting",
    ],
    "l2_scenarios_for_career": [
        "Job Interview Preparation",
        "Career Change Decision",
        "Workplace Conflict Resolution",
    ],
}
