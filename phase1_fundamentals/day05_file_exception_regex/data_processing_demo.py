"""
data_processing_demo.py
NumPy与Pandas数据处理综合演示

功能：
1. NumPy数组创建、索引、切片、向量化运算
2. Pandas DataFrame的创建、读取、操作
3. 数据清洗（缺失值、异常值处理）
4. 数据分析和聚合
5. 实战：完整的CSV数据分析流程

学习目标：
1. 掌握NumPy数组的基本操作
2. 学会用Pandas进行数据分析
3. 能独立完成从读取到分析的数据处理Pipeline
"""
import numpy as np  # 科学计算库，高效数组操作
import pandas as pd  # 数据分析库，DataFrame
from pathlib import Path


# ==================== 第1部分：NumPy基础 ====================

def demo_numpy():
    """演示NumPy的核心功能"""
    print("=" * 50)
    print("🔢 1. NumPy基础")
    print("-" * 50)

    # 创建数组 — 多种方式
    arr_from_list = np.array([1, 2, 3, 4, 5])          # 从列表创建
    zeros = np.zeros((2, 3))                             # 2x3全0矩阵
    ones = np.ones((3, 2))                               # 3x2全1矩阵
    sequence = np.arange(0, 10, 2)                       # 类似range: 0,2,4,6,8
    linspace = np.linspace(0, 1, 5)                      # 等间距: 0, 0.25, 0.5, 0.75, 1.0
    random_arr = np.random.randn(10)                      # 10个正态分布随机数

    print(f"从列表创建: {arr_from_list}")
    print(f"np.arange(0,10,2): {sequence}")
    print(f"np.linspace(0,1,5): {linspace}")
    print(f"\n全0矩阵 (2x3):\n{zeros}")
    print(f"\n正态分布随机数 (前5个): {random_arr[:5].round(3)}")

    # 数组信息
    print(f"\n形状: {zeros.shape}")   # 各维度大小
    print(f"维度: {zeros.ndim}")      # 几维数组
    print(f"元素类型: {zeros.dtype}")  # 数据类型
    print(f"元素总数: {zeros.size}")   # 总元素个数

    # 向量化运算 — NumPy的核心优势，无需for循环
    a = np.array([1, 2, 3, 4, 5])
    b = np.array([10, 20, 30, 40, 50])

    print(f"\n向量化运算:")
    print(f"  a + b = {a + b}")       # 对应元素相加
    print(f"  a * b = {a * b}")       # 对应元素相乘
    print(f"  a ** 2 = {a ** 2}")     # 每个元素平方
    print(f"  a > 3 = {a > 3}")       # 布尔判断: [F F F T T]
    print(f"  sum(a) = {np.sum(a)}")  # 求和
    print(f"  mean(a) = {np.mean(a):.1f}")  # 平均值

    # 索引与切片
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    print(f"\n3x3矩阵:\n{arr}")
    print(f"第2行: {arr[1]}")                      # [4 5 6]
    print(f"第3列: {arr[:, 2]}")                   # [3 6 9]
    print(f"子矩阵(行0:2,列1:3):\n{arr[0:2, 1:3]}")  # [[2 3],[5 6]]

    # 布尔索引 — 按条件筛选
    print(f"\n布尔索引 (arr > 5): {arr[arr > 5]}")  # [6 7 8 9]

    # 广播机制 — 不同形状的数组也能运算
    print(f"\n广播: arr + [10, 20, 30] = \n{arr + [10, 20, 30]}")

    # 常用统计函数
    data = np.random.randn(1000)  # 1000个随机数做演示
    print(f"\n统计函数 (1000个正态分布样本):")
    print(f"  均值: {data.mean():.3f}")
    print(f"  标准差: {data.std():.3f}")
    print(f"  最大值: {data.max():.3f}")
    print(f"  最小值: {data.min():.3f}")
    print(f"  中位数: {np.median(data):.3f}")


# ==================== 第2部分：Pandas基础 ====================

def demo_pandas():
    """演示Pandas的核心功能"""
    print("\n" + "=" * 50)
    print("🐼 2. Pandas基础")
    print("-" * 50)

    # 创建DataFrame — 二维表格数据结构
    df = pd.DataFrame({
        "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
        "年龄": [22, 23, 21, 22, 24],
        "成绩": [85, 92, 78, 95, 88],
        "城市": ["北京", "上海", "北京", "深圳", "上海"],
    })
    print(f"DataFrame:\n{df}\n")

    # 基本查看方法
    print(f"前3行 (head(3)):\n{df.head(3)}\n")
    print(f"列信息 (info):")
    df.info()  # 显示每列的数据类型和非空数量
    print(f"\n统计摘要 (describe):\n{df.describe()}")

    # 按列访问 — 返回Series（一维带标签数组）
    print(f"\n按列访问:")
    print(f"成绩列:\n{df['成绩']}")
    print(f"成绩均值: {df['成绩'].mean():.1f}")

    # 按行过滤 — 布尔索引
    print(f"\n过滤(成绩>=90):")
    excellent = df[df["成绩"] >= 90]  # 返回过滤后的DataFrame
    print(excellent)

    # 多重条件 — 用 & (and) | (or) ~ (not)
    print(f"\n多条件(成绩>=85 AND 城市=='北京'):")
    beijing_high = df[(df["成绩"] >= 85) & (df["城市"] == "北京")]
    print(beijing_high)

    # 新增/修改列
    df["等级"] = df["成绩"].apply(  # apply对每行应用函数
        lambda s: "优秀" if s >= 90 else ("良好" if s >= 80 else "中等")
    )
    print(f"\n新增'等级'列:\n{df}")

    # 排序
    print(f"\n按成绩降序:\n{df.sort_values('成绩', ascending=False)}")

    # 分组聚合 — SQL中的GROUP BY
    print(f"\n按城市分组，计算平均成绩:")
    grouped = df.groupby("城市")["成绩"].agg(["mean", "count", "max"])
    print(grouped)


# ==================== 第3部分：Pandas数据读写 ====================

def demo_pandas_io():
    """演示Pandas的文件读写功能"""
    print("\n" + "=" * 50)
    print("🐼 3. Pandas数据读写")
    print("-" * 50)

    demo_dir = Path(__file__).parent

    # 创建演示数据
    df = pd.DataFrame({
        "日期": pd.date_range("2024-01-01", periods=5, freq="D"),
        "产品": ["A", "B", "A", "C", "B"],
        "销量": [100, 150, 120, 80, 200],
        "单价": [9.9, 15.0, 9.9, 25.0, 15.0],
    })
    df["金额"] = df["销量"] * df["单价"]  # 新增计算列
    print(f"原始数据:\n{df}")

    # 写入CSV
    csv_path = demo_dir / "demo_pandas.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")  # index=False不写行号
    print(f"\n✅ 写入CSV: {csv_path}")

    # 读取CSV
    df_read = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"✅ 读取CSV: {len(df_read)}行, 列: {list(df_read.columns)}")

    # 写入Excel
    excel_path = demo_dir / "demo_pandas.xlsx"
    try:
        # openpyxl需要额外安装: pip install openpyxl
        df.to_excel(excel_path, index=False, sheet_name="销售数据")
        print(f"✅ 写入Excel: {excel_path}")
        os.remove(excel_path)
    except ImportError:
        print("⚠️ 需要 openpyxl 才能写Excel: pip install openpyxl")

    # 清理
    os.remove(csv_path)
    print(f"🗑️ 已清理演示文件")


# ==================== 第4部分：综合数据分析实战 ====================

def demo_data_analysis():
    """综合实战：完整的数据分析流程"""
    print("\n" + "=" * 50)
    print("📊 4. 综合实战: 数据分析完整流程")
    print("=" * 50)

    # 创建模拟数据：公司员工信息
    np.random.seed(42)  # 固定随机种子，确保结果可复现
    n = 20  # 20个员工

    df = pd.DataFrame({
        "姓名": [f"员工{i:02d}" for i in range(1, n + 1)],
        "部门": np.random.choice(["技术部", "产品部", "市场部", "人事部"], n),
        "年龄": np.random.randint(22, 45, n),
        "工龄": np.round(np.random.uniform(0.5, 15, n), 1),  # uniform均匀分布
        "月薪": np.random.randint(8000, 35000, n),
        "绩效分": np.round(np.random.uniform(60, 100, n), 1),
    })
    # 模拟几个缺失值和异常值
    df.loc[3, "绩效分"] = np.nan       # 缺失值
    df.loc[7, "月薪"] = np.nan         # 缺失值
    df.loc[15, "年龄"] = np.nan        # 缺失值
    print(f"原始数据 (含缺失值):\n{df.head(10)}\n")

    # 步骤1: 数据概览
    print(f"数据集大小: {df.shape}")  # (行数, 列数)
    print(f"缺失值数量:\n{df.isnull().sum()}\n")  # 每列的缺失值数

    # 步骤2: 处理缺失值
    # 数值列：用中位数填充（比均值更抗异常值）
    df["年龄"].fillna(df["年龄"].median(), inplace=True)
    df["月薪"].fillna(df["月薪"].median(), inplace=True)
    df["绩效分"].fillna(df["绩效分"].mean(), inplace=True)  # 绩效用均值
    print(f"填充缺失后:\n{df.head(10)}\n")

    # 步骤3: 派生新特征
    df["月薪等级"] = pd.cut(  # cut将连续值分箱
        df["月薪"],
        bins=[0, 10000, 20000, 50000],
        labels=["初级", "中级", "高级"]
    )
    df["年薪"] = df["月薪"] * 12  # 计算年薪

    # 步骤4: 统计分析
    print("=" * 40)
    print("统计分析:")
    print("=" * 40)

    # 按部门汇总
    print("\n按部门汇总:")
    dept_stats = df.groupby("部门").agg({
        "姓名": "count",          # 人数
        "年龄": "mean",           # 平均年龄
        "月薪": ["mean", "max", "min"],  # 多个统计量
        "绩效分": "mean",
    }).round(1)
    dept_stats.columns = [f"{c[0]}_{c[1]}" for c in dept_stats.columns]  # 展平多层列名
    dept_stats = dept_stats.rename(columns={"姓名_count": "人数"})
    print(dept_stats)

    # 按月薪等级统计
    print(f"\n月薪等级分布:")
    print(df["月薪等级"].value_counts())  # 计数

    # 找出绩效最好的员工
    top_performers = df.nlargest(3, "绩效分")[["姓名", "部门", "绩效分", "月薪"]]
    print(f"\n绩效Top3:")
    print(top_performers)

    # 步骤5: 用NumPy做进一步计算
    print(f"\nNumPy进阶统计:")
    salaries = df["月薪"].values  # .values转为NumPy数组
    print(f"  月薪均值: {np.mean(salaries):.0f}")
    print(f"  月薪标准差: {np.std(salaries):.0f}")
    print(f"  月薪中位数: {np.median(salaries):.0f}")

    # 相关系数（月薪和绩效分的关联度）
    corr = df["月薪"].corr(df["绩效分"])  # Pandas的corr方法
    print(f"  月薪-绩效分相关系数: {corr:.3f}")

    print(f"\n✅ 数据分析流程完成！")
    print(f"  数据规模: {df.shape[0]}行 × {df.shape[1]}列")
    print(f"  部门数: {df['部门'].nunique()}")


def main():
    """主函数 — 按顺序运行所有演示"""
    print("=" * 60)
    print("Day 05: NumPy与Pandas数据处理")
    print("=" * 60)

    try:
        demo_numpy()
        demo_pandas()
        demo_pandas_io()
        demo_data_analysis()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import os  # 需要在这里导入因为demo_pandas_io里用了os
    main()