"""因子计算 (契约占位, Sprint 3 实现)。

负责把"因子定义"作用到行情 DataFrame 上, 产出因子信号序列。
支持三类来源: 模板因子 / 因子组合器(Stack) / 用户 Python 因子(经沙箱)。
"""

# 计划接口 (签名待定稿, Sprint 3 实现):
#
# def compute_template_factor(df, factor_type, params) -> "pd.Series": ...
# def compute_factor_stack(df, items) -> "pd.Series":  # items: [(series, weight), ...]
# 约定: 输入行情 DataFrame, 输出与其索引对齐的因子信号 Series。
