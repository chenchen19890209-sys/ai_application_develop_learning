"""
file_exception_demo.py
文件操作、异常处理和正则表达式综合演示

功能：
1. 文件读写（文本、CSV、JSON）
2. 异常处理（try/except/else/finally、自定义异常）
3. 正则表达式（搜索、匹配、替换）
4. 综合实战：数据清洗Pipeline

学习目标：
1. 掌握with语句安全打开文件
2. 学会捕获和处理不同类型的异常
3. 熟练使用正则表达式处理文本数据
"""
import os  # 文件路径检查
import re  # 正则表达式
import json  # JSON读写
import csv  # CSV读写
from pathlib import Path  # 现代路径处理


# ==================== 第1部分：文件读写 ====================

def demo_file_io():
    """演示文件的基本读写操作"""
    print("=" * 50)
    print("📁 1. 文件读写")
    print("-" * 50)

    # 获取当前文件所在目录，用于存放演示文件
    demo_dir = Path(__file__).parent

    # —— 写入文件 ——
    # 'w'模式：只写，文件不存在则创建，存在则覆盖
    txt_path = demo_dir / "demo.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("第1行: Hello, Python!\n")  # write()不自动加换行
        f.write("第2行: 你好，世界！\n")
        f.write("第3行: AI大模型应用开发\n")
    print(f"✅ 已写入: {txt_path}")

    # —— 读取文件 ——
    # 方式1: read()一次读取全部（小文件适用）
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()  # 整个文件内容作为一个字符串
    print(f"\nread()全部内容:\n{content}")

    # 方式2: 逐行读取（大文件推荐，内存友好）
    print("readline()逐行:")
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:  # 文件对象本身就是可迭代的
            print(f"  {line.strip()}")  # strip()去除行末尾的\n

    # 方式3: readlines()读取所有行到列表
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()  # 每行作为列表的一个元素
    print(f"\nreadlines()共{len(lines)}行: {lines}")

    # —— 追加模式 ——
    # 'a'模式：追加，文件不存在则创建
    with open(txt_path, "a", encoding="utf-8") as f:
        f.write("第4行: 追加的内容\n")
    print(f"✅ 已追加第4行")

    # 清理演示文件
    os.remove(txt_path)
    print(f"🗑️ 已清理: {txt_path}")


def demo_json_csv():
    """演示JSON和CSV文件的读写"""
    print("\n" + "=" * 50)
    print("📁 2. JSON和CSV文件处理")
    print("-" * 50)

    demo_dir = Path(__file__).parent

    # —— JSON写入 ——
    data = {
        "students": [
            {"name": "张三", "score": 85, "grade": "良好"},
            {"name": "李四", "score": 92, "grade": "优秀"},
            {"name": "王五", "score": 78, "grade": "中等"},
        ],
        "total": 3
    }
    json_path = demo_dir / "demo.json"
    with open(json_path, "w", encoding="utf-8") as f:
        # indent=2: 缩进2空格，ensure_ascii=False: 保留中文
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON已写入: {json_path}")

    # —— JSON读取 ——
    with open(json_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)  # json.load()直接解析为Python字典
    print(f"JSON读取: {len(loaded['students'])}个学生")
    for s in loaded["students"]:
        print(f"  {s['name']}: {s['score']}分")

    # —— CSV写入 ——
    csv_path = demo_dir / "demo.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        # utf-8-sig: 带BOM的UTF-8（Excel打开不乱码）
        writer = csv.writer(f)
        writer.writerow(["姓名", "成绩", "等级"])  # 写表头
        writer.writerow(["张三", 85, "良好"])
        writer.writerow(["李四", 92, "优秀"])
        writer.writerow(["王五", 78, "中等"])
    print(f"\n✅ CSV已写入: {csv_path}")

    # —— CSV读取 ——
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)  # DictReader按列名读取为字典
        print("CSV读取:")
        for row in reader:
            print(f"  {row['姓名']}: {row['成绩']}分 - {row['等级']}")

    # 清理
    os.remove(json_path)
    os.remove(csv_path)
    print(f"🗑️ 已清理演示文件")


# ==================== 第2部分：异常处理 ====================

def demo_exceptions():
    """演示异常处理的完整模式"""
    print("\n" + "=" * 50)
    print("⚠️ 3. 异常处理")
    print("-" * 50)

    # 基本try/except — 捕获特定异常
    print("try/except — 除零错误:")
    try:
        result = 10 / 0  # ZeroDivisionError
    except ZeroDivisionError as e:
        # e是异常对象，包含错误信息
        print(f"  ❌ 捕获ZeroDivisionError: {e}")

    # 多重except — 不同异常分别处理
    print("\n多重except:")
    values = ["10", "0", "abc"]
    for v in values:
        try:
            result = 10 / int(v)
            print(f"  10/{v} = {result}")
        except ZeroDivisionError:
            print(f"  10/{v}: ❌ 不能除以零")
        except ValueError:
            print(f"  10/'{v}': ❌ 不是有效数字")
        except Exception as e:
            print(f"  10/{v}: ❌ 未知错误: {e}")

    # else — 没有异常时执行
    print("\ntry/except/else:")
    try:
        num = int("42")  # 正常情况
    except ValueError:
        print("  ❌ 转换失败")
    else:
        print(f"  ✅ 转换成功: {num}")  # 只有没异常才执行

    # finally — 无论是否有异常都执行（清理资源）
    print("\ntry/except/finally:")
    file_obj = None  # 初始化为None
    try:
        file_obj = open("nonexistent.txt", "r")
    except FileNotFoundError:
        print("  ❌ 文件不存在")
    finally:
        if file_obj:
            file_obj.close()  # 确保文件被关闭
            print("  📁 文件已关闭")

    # 自定义异常
    class InvalidScoreError(Exception):
        """成绩无效异常"""
        def __init__(self, score: float):
            self.score = score
            super().__init__(f"成绩 {score} 不在有效范围 [0, 100] 内")

    def validate_score(score: float) -> float:
        """验证分数是否在有效范围内"""
        if not 0 <= score <= 100:
            raise InvalidScoreError(score)  # raise抛出异常
        return score

    print("\n自定义异常:")
    for s in [85, -10, 95, 150]:
        try:
            validate_score(s)
            print(f"  ✅ {s} 有效")
        except InvalidScoreError as e:
            print(f"  ❌ {e}")

    # Python异常处理建议:
    # 1. 捕获具体异常而不是裸Exception
    # 2. finally用于清理资源（或用with语句自动处理）
    # 3. 自定义异常让代码意图更清晰


# ==================== 第3部分：正则表达式 ====================

def demo_regex():
    """演示正则表达式的常用模式"""
    print("\n" + "=" * 50)
    print("🔍 4. 正则表达式")
    print("-" * 50)

    text = """
    联系方式:
    - 邮箱1: zhangsan@example.com
    - 邮箱2: lisi@company.cn
    - 手机: 13812345678
    - 座机: 010-12345678
    - 手机: 15900001111
    - IP: 192.168.1.1
    - 日期: 2024-01-15
    """
    print(f"原始文本:{text}")

    # re.search() — 搜索第一个匹配项
    print("\nre.search() 搜索第一个邮箱:")
    # \w = 字母数字下划线，+ = 一个及以上，\. = 转义的点号
    match = re.search(r"[\w.]+@[\w.]+\.\w+", text)
    if match:
        print(f"  找到: {match.group()}")  # group()获取匹配内容

    # re.findall() — 找到所有匹配项
    print("\nre.findall() 找到所有邮箱:")
    emails = re.findall(r"[\w.]+@[\w.]+\.\w+", text)
    for e in emails:
        print(f"  - {e}")

    # re.findall() — 找到所有手机号（1开头的11位数字）
    print("\nre.findall() 找到所有手机号:")
    phones = re.findall(r"1[3-9]\d{9}", text)  # [3-9]第二位，\d{9}再9位数字
    for p in phones:
        print(f"  - {p}")

    # re.sub() — 替换
    print("\nre.sub() 手机号脱敏:")
    # \1 引用第一个分组（前3位），后面8位用*代替
    masked = re.sub(r"(1[3-9]\d)\d{8}", r"\1********", text)
    print(masked)

    # 分组（用括号捕获）
    print("\n分组提取:")
    date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if date_match:
        year, month, day = date_match.groups()  # groups()返回所有分组
        print(f"  日期匹配: {date_match.group()}")
        print(f"  分组: 年={year}, 月={month}, 日={day}")

    # re.compile() — 预编译正则（多次使用效率更高）
    print("\nre.compile() 预编译（高效）:")
    phone_pattern = re.compile(r"1[3-9]\d{9}")
    test_nums = ["13812345678", "12345678901", "15900001111", "88888888"]
    for num in test_nums:
        if phone_pattern.match(num):  # match从字符串开头匹配
            print(f"  ✅ {num}")
        else:
            print(f"  ❌ {num}")

    # 常用正则速查
    print("""
    ┌─────────────────────────────────────────┐
    │ 常用正则速查                             │
    ├─────────────────────────────────────────┤
    │ \d  数字          \w  字母数字下划线     │
    │ \s  空白字符      .   任意字符（换行除外）│
    │ +   1个以上       *   0个以上           │
    │ {n} 恰好n个      {n,}至少n个            │
    │ [abc] 字符集合    [^abc] 排除集合       │
    │ (abc) 分组       (?:abc) 非捕获分组     │
    │ ^ 行首           $ 行尾                │
    └─────────────────────────────────────────┘
    """)


# ==================== 第4部分：综合实战 ====================

def demo_data_cleaning_pipeline():
    """综合实战：数据清洗Pipeline"""
    print("\n" + "=" * 50)
    print("🧹 5. 综合实战: 数据清洗Pipeline")
    print("=" * 50)

    # 模拟脏数据
    raw_data = [
        "张三,85,zhangsan@mail.com",
        "李四, 92, lisi@company.cn",  # 有空格
        "王五,abc,wangwu@test.com",     # 分数是文本！
        "赵六,95,zhaoliu",              # 邮箱无@
        "钱七,-10,qianqi@123.com",      # 分数为负数
    ]
    print("原始脏数据:")
    for d in raw_data:
        print(f"  {d}")

    # 数据清洗Pipeline
    clean_data = []  # 存放清洗后的数据
    errors = []      # 存放错误记录

    for i, line in enumerate(raw_data, 1):
        try:
            # 步骤1: 按逗号分割（处理空格）
            parts = [p.strip() for p in line.split(",")]

            if len(parts) != 3:
                # raise 用于主动抛出异常，中断当前流程并跳转到 except 块
                raise ValueError(f"列数不对(期望3列，实际{len(parts)}列)")

            name, score_str, email = parts

            # 步骤2: 分数验证
            try:
                score = float(score_str)
            except ValueError:
                raise ValueError(f"分数不是数字: '{score_str}'")

            if not 0 <= score <= 100:
                raise ValueError(f"分数超出范围: {score}")

            # 步骤3: 邮箱验证（用正则）
            if not re.match(r"[\w.]+@[\w.]+\.\w+", email):
                raise ValueError(f"邮箱格式错误: '{email}'")

            # 步骤4: 确定等级
            if score >= 90:
                grade = "优秀"
            elif score >= 80:
                grade = "良好"
            elif score >= 70:
                grade = "中等"
            elif score >= 60:
                grade = "及格"
            else:
                grade = "不及格"

            # 数据通过所有验证
            clean_data.append({
                "name": name,
                "score": score,
                "email": email,
                "grade": grade
            })
            print(f"  ✅ 第{i}行: {name} 清洗通过")

        except Exception as e:
            errors.append({"line": i, "raw": line, "error": str(e)})
            print(f"  ❌ 第{i}行: {e}")

    # 输出结果
    print(f"\n清洗结果: {len(clean_data)}条通过, {len(errors)}条失败")

    if clean_data:
        print("\n✅ 有效数据:")
        for s in clean_data:
            print(f"  {s['name']}: {s['score']}分 - {s['grade']} ({s['email']})")

    if errors:
        print("\n❌ 错误记录:")
        for err in errors:
            print(f"  第{err['line']}行: {err['error']}")


def main():
    """主函数 — 按顺序运行所有演示"""
    print("=" * 60)
    print("Day 05: 文件、异常与正则表达式")
    print("=" * 60)

    try:
        demo_file_io()
        demo_json_csv()
        demo_exceptions()
        demo_regex()
        demo_data_cleaning_pipeline()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        print("💡 Python基础阶段到此结束，明天开始LLM核心能力学习！")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()