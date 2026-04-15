"""
Module 2 — 商业优先级权重定义
============================

为不同酒店维度分配商业重要性权重，影响最终的缺口评分。
权重范围：5-20 分，反映该维度对客户体验和商业价值的重要程度。
"""

# 商业优先级权重表 - 根据客户影响和商业价值定义
BUSINESS_WEIGHTS = {
    # ── 硬件设施 ──────────────────────────────────────────────────
    "wifi_speed": 18,          # WiFi速度 - 现代旅客必需品，高优先级
    "soundproofing": 15,       # 隔音效果 - 影响睡眠质量，重要
    "air_conditioning": 16,     # 空调供暖 - 基础舒适度需求
    "elevator": 8,             # 电梯 - 便利性需求，中等优先级
    "power_outlets": 12,       # 电源插座 - 现代设备充电需求
    "water_pressure": 14,      # 水压淋浴 - 基础卫生需求

    # ── 服务体验 ──────────────────────────────────────────────────
    "front_desk_efficiency": 17,    # 前台效率 - 直接影响入住体验
    "room_cleanliness": 20,          # 房间清洁 - 最基础且关键的需求
    "restaurant_quality": 11,        # 餐厅质量 - 可选服务，中等重要
    "breakfast_quality": 13,         # 早餐质量 - 常见服务，中等重要
    "luggage_storage": 6,            # 行李存储 - 便利性服务，较低优先级
    "staff_friendliness": 16,        # 员工友善度 - 服务体验核心要素

    # ── 周边环境 ──────────────────────────────────────────────────
    "transport_access": 19,          # 交通便利性 - 地理位置核心要素
    "noise_level": 14,               # 外部噪音 - 影响休息质量
    "nearby_dining": 9,              # 附近餐饮 - 便利性需求
    "location_convenience": 20,      # 地理位置便利性 - 选择酒店的关键因素

    # ── 酒店政策 ──────────────────────────────────────────────────
    "checkout_time": 7,              # 退房时间 - 便利性政策
    "breakfast_hours": 8,            # 早餐时间 - 服务政策
    "parking": 10,                   # 停车政策 - 自驾客户重要需求
    "pet_policy": 5,                 # 宠物政策 - 特定客户群体需求
}


def get_business_priority(dimension: str) -> float:
    """
    获取指定维度的商业优先级权重

    Args:
        dimension: 维度名称

    Returns:
        权重分数 (5-20分)，未知维度返回默认值10分
    """
    return BUSINESS_WEIGHTS.get(dimension, 10.0)


def get_category_avg_weight(category: str) -> float:
    """
    获取指定类别的平均商业权重（用于类别级分析）

    Args:
        category: 类别名称 (hardware/service/surroundings/policy)

    Returns:
        该类别下所有维度的平均权重
    """
    # 导入维度分类定义
    try:
        from module1.dimensions import DIMENSIONS
        category_dims = [
            dim for dim, meta in DIMENSIONS.items()
            if meta["category"] == category
        ]
        if not category_dims:
            return 10.0

        weights = [BUSINESS_WEIGHTS.get(dim, 10.0) for dim in category_dims]
        return sum(weights) / len(weights)
    except ImportError:
        # 如果无法导入，返回默认值
        return 10.0


# 权重分布统计信息（便于调试和调优）
def get_weight_stats():
    """获取权重分布的统计信息"""
    weights = list(BUSINESS_WEIGHTS.values())
    return {
        "min_weight": min(weights),
        "max_weight": max(weights),
        "avg_weight": sum(weights) / len(weights),
        "total_dimensions": len(weights),
        "high_priority": len([w for w in weights if w >= 16]),  # >= 16分
        "medium_priority": len([w for w in weights if 10 <= w < 16]),  # 10-15分
        "low_priority": len([w for w in weights if w < 10]),  # < 10分
    }