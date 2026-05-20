"""
control_flow.py
Python控制流程综合演示 — 条件判断、循环、模式匹配

功能：
1. 条件判断（if-elif-else）演示
2. for循环和while循环演示
3. break/continue/pass控制语句
4. match/case模式匹配（Python 3.11新特性）
5. 实战：猜数字游戏
6. 实战：成绩等级判定系统

学习目标：
1. 掌握所有控制流程语法
2. 理解不同循环的适用场景
3. 学会用match/case替代复杂的if-elif-else
4. 能独立完成猜数字游戏的编写
"""
import random  # 生成随机数，用于猜数字游戏


# ==================== 第1部分：条件判断演示 ====================

def demo_if_elif_else():
    """演示if-elif-else条件判断的用法"""
    print("\n" + "=" * 50)
    print("📋 1. 条件判断（if-elif-else）")
    print("-" * 50)

    # 简单if — 当条件为True时执行代码块
    age = 20
    if age >= 18:
        print(f"年龄{age}岁: 已成年")  # Python用缩进（4个空格）表示代码块

    # if-else — 两个分支，必走一个
    score = 75
    if score >= 60:
        print(f"成绩{score}分: 及格")
    else:
        print(f"成绩{score}分: 不及格")

    # if-elif-else — 多个条件，从上到下依次判断，命中一个即停止
    score = 85
    if score >= 90:
        level = "优秀"
    elif score >= 80:
        level = "良好"  # 85分会命中这个分支
    elif score >= 70:
        level = "中等"
    elif score >= 60:
        level = "及格"
    else:
        level = "不及格"  # 以上条件都不满足时执行
    print(f"成绩{score}分: {level}")

    # 逻辑运算符 and/or/not — 组合多个条件
    age = 25
    has_ticket = True
    if age >= 18 and has_ticket:  # and: 两个条件都成立
        print("可以入场观影")
    if age < 18 or not has_ticket:  # or: 至少一个成立；not: 取反
        print("不能入场")

    # 三元表达式 — 一行写的条件判断（变量 = 值1 if 条件 else 值2）
    temperature = 35
    weather = "炎热" if temperature > 30 else "舒适"
    print(f"{temperature}°C — {weather}")


# ==================== 第2部分：for循环演示 ====================

def demo_for_loop():
    """演示for循环的多种用法"""
    print("\n" + "=" * 50)
    print("📋 2. for循环")
    print("-" * 50)

    # range(stop) — 从0开始，不包含stop
    print("range(5):", [i for i in range(5)])  # [0, 1, 2, 3, 4]

    # range(start, stop) — 从start开始，不包含stop
    print("range(2, 6):", [i for i in range(2, 6)])  # [2, 3, 4, 5]

    # range(start, stop, step) — step为步长
    print("range(1, 10, 2):", [i for i in range(1, 10, 2)])  # [1, 3, 5, 7, 9]

    # 遍历列表 — 直接获取每个元素
    fruits = ["苹果", "香蕉", "橙子", "葡萄"]
    print("水果列表:")
    for fruit in fruits:
        print(f"  - {fruit}")

    # enumerate — 同时获取索引和值
    print("带序号的水果:")
    for index, fruit in enumerate(fruits, start=1):  # start指定起始序号
        print(f"  {index}. {fruit}")

    # 遍历字典
    student = {"name": "张三", "age": 20, "score": 85}
    print("学生信息:")
    for key, value in student.items():  # items()返回(键, 值)对
        print(f"  {key}: {value}")

    # zip — 并行遍历多个列表
    names = ["张三", "李四", "王五"]
    scores = [85, 92, 78]
    print("多列表并行遍历:")
    for name, score in zip(names, scores):  # zip将多个列表打包成元组
        print(f"  {name}: {score}分")


# ==================== 第3部分：while循环演示 ====================

def demo_while_loop():
    """演示while循环和break/continue/pass的用法"""
    print("\n" + "=" * 50)
    print("📋 3. while循环与控制语句")
    print("-" * 50)

    # 基本while循环 — 条件为True时一直执行
    count = 0
    while count < 3:
        print(f"  计数: {count}")
        count += 1  # ⚠️ 必须更新条件变量，否则无限循环

    # break — 立即终止循环
    print("\nbreak演示（找到5的倍数就停止）:")
    for i in range(1, 20):
        if i % 5 == 0:
            print(f"  找到: {i}，停止搜索")
            break  # 跳出整个循环

    # continue — 跳过本次循环，继续下一次
    print("\ncontinue演示（跳过偶数）:")
    for i in range(1, 11):
        if i % 2 == 0:
            continue  # 偶数跳过，不执行后面的print
        print(f"  {i}", end=" ")  # 输出: 1 3 5 7 9
    print()

    # pass — 占位符，什么都不做
    def future_feature():
        pass  # 函数体还不能为空，先用pass占位

    print("\npass: 函数占位符已定义（还未实现）")


# ==================== 第4部分：match/case模式匹配 ====================

def demo_match_case():
    """演示Python 3.11的match/case模式匹配"""
    print("\n" + "=" * 50)
    print("📋 4. match/case模式匹配（Python 3.11+）")
    print("-" * 50)

    # 基础用法：匹配具体值
    def http_status_text(code):
        """将HTTP状态码转为中文描述"""
        match code:
            case 200:
                return "成功"
            case 301 | 302:  # | 表示"或"（匹配301或302）
                return "重定向"
            case 400:
                return "请求错误"
            case 404:
                return "未找到"
            case 500:
                return "服务器内部错误"
            case _:  # _ 是通配符，匹配所有未列出的值（类似else）
                return f"未知状态码({code})"

    for code in [200, 302, 404, 500, 999]:
        print(f"  HTTP {code}: {http_status_text(code)}")

    # 进阶用法：匹配数据结构
    def describe_point(point):
        """用match匹配坐标点"""
        match point:
            case (0, 0):
                return "原点"
            case (0, y):
                return f"Y轴上，y={y}"
            case (x, 0):
                return f"X轴上，x={x}"
            case (x, y) if x == y:  # 带条件守卫（if子句）
                return f"对角线上 ({x}, {y})"
            case (x, y):
                return f"坐标 ({x}, {y})"

    print("\n坐标匹配:")
    for pt in [(0, 0), (0, 5), (3, 0), (5, 5), (3, 7)]:
        print(f"  {pt}: {describe_point(pt)}")

    # 匹配类型和结构
    def process_command(cmd):
        """用match处理不同类型的命令"""
        match cmd:
            case {"action": "move", "x": x, "y": y}:
                return f"移动到 ({x}, {y})"
            case {"action": "attack", "target": target}:
                return f"攻击 {target}"
            case {"action": "defend"}:
                return "进入防御状态"
            case str():  # 匹配字符串类型
                return f"未知文本命令: {cmd}"
            case _:
                return "无法识别的命令格式"

    print("\n命令处理:")
    commands = [
        {"action": "move", "x": 10, "y": 20},
        {"action": "attack", "target": "Boss"},
        {"action": "defend"},
        "hello",
        123
    ]
    for cmd in commands:
        print(f"  {cmd} → {process_command(cmd)}")


# ==================== 第5部分：实战 — 猜数字游戏 ====================

def guessing_game():
    """猜数字游戏 — 综合运用条件判断、循环和异常处理"""
    print("\n" + "=" * 50)
    print("🎮 5. 猜数字游戏")
    print("-" * 50)

    # 生成1-100的随机整数作为答案
    answer = random.randint(1, 100)
    attempts = 0  # 记录猜测次数
    max_attempts = 7  # 最多猜7次

    print(f"我已经想好了一个1-100之间的数字，你最多猜{max_attempts}次！")

    while attempts < max_attempts:
        # 获取用户输入
        try:
            guess = int(input(f"\n第{attempts + 1}次猜测（剩余{max_attempts - attempts}次）: "))
        except ValueError:
            print("❌ 请输入有效的数字！")
            continue  # 输入无效，跳过本次循环

        # 验证输入范围
        if guess < 1 or guess > 100:
            print("❌ 请输入1-100之间的数字！")
            continue

        attempts += 1  # 有效猜测，次数+1

        # 判断结果
        if guess == answer:
            print(f"\n🎉 恭喜猜中！答案就是 {answer}")
            print(f"你用了 {attempts} 次猜中")
            # 根据次数给出评价
            if attempts <= 3:
                print("评价: ⭐⭐⭐ 太厉害了！")
            elif attempts <= 5:
                print("评价: ⭐⭐ 不错哦！")
            else:
                print("评价: ⭐ 继续加油！")
            return  # 猜中了，结束函数
        elif guess < answer:
            print("📈 太小了！再大一点")
        else:
            print("📉 太大了！再小一点")

    # 用完了所有机会
    print(f"\n😢 很遗憾，{max_attempts}次机会用完了！答案是 {answer}")


# ==================== 第6部分：实战 — 成绩等级判定系统 ====================

def get_grade(score):
    """根据分数返回等级（使用if-elif-else链）"""
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 70:
        return "中等"
    elif score >= 60:
        return "及格"
    else:
        return "不及格"


def grade_system():
    """成绩等级判定系统 — 综合运用函数、循环和数据结构"""
    print("\n" + "=" * 50)
    print("📊 6. 成绩等级判定系统")
    print("-" * 50)

    students = []  # 存储所有学生信息

    print("请输入学生姓名和成绩（输入 'quit' 结束录入）:")

    while True:
        name = input("\n学生姓名: ").strip()

        # 退出条件
        if name.lower() == "quit":
            break
        if not name:  # 空输入跳过
            continue

        # 获取成绩
        try:
            score = float(input(f"{name}的成绩（0-100）: "))
        except ValueError:
            print("❌ 请输入有效的数字！")
            continue

        # 验证成绩范围
        if score < 0 or score > 100:
            print("❌ 成绩必须在0-100之间！")
            continue

        # 记录学生信息
        students.append({
            "name": name,
            "score": score,
            "grade": get_grade(score)  # 调用等级判定函数
        })
        print(f"✅ {name}: {score}分 — {get_grade(score)}")

    # 如果录入了学生，显示统计
    if not students:
        print("\n没有录入任何学生信息")
        return

    # 提取所有分数用于统计
    scores = [s["score"] for s in students]  # 列表推导式（明天的内容！）

    print("\n" + "=" * 50)
    print("📊 班级统计")
    print("=" * 50)
    print(f"班级人数: {len(students)}")
    print(f"平均分: {sum(scores) / len(scores):.2f}")  # :.2f 保留2位小数
    print(f"最高分: {max(scores)}")
    print(f"最低分: {min(scores)}")

    # 按等级分组
    print("\n成绩分布:")
    for grade in ["优秀", "良好", "中等", "及格", "不及格"]:
        count = sum(1 for s in students if s["grade"] == grade)
        bar = "█" * count  # 简单的柱状图
        print(f"  {grade}: {count}人 {bar}")

    # 显示所有学生详情
    print("\n学生详情:")
    for s in sorted(students, key=lambda x: x["score"], reverse=True):
        print(f"  {s['name']}: {s['score']}分 — {s['grade']}")


# ==================== 第7部分：循环嵌套演示 ====================

def demo_nested_loops():
    """演示循环嵌套 — 九九乘法表"""
    print("\n" + "=" * 50)
    print("📋 7. 循环嵌套 — 九九乘法表")
    print("-" * 50)

    # 外层循环控制行（被乘数）
    for i in range(1, 10):
        # 内层循环控制列（乘数）
        for j in range(1, i + 1):
            # end="\t" 用制表符分隔，不换行
            print(f"{j}×{i}={i*j:2d}", end="\t")
        print()  # 每行结束后换行


def main():
    """主函数 — 按顺序运行所有演示"""
    print("=" * 60)
    print("Day 02: Python控制流程 — 综合演示")
    print("=" * 60)

    try:
        demo_if_elif_else()
        demo_for_loop()
        demo_while_loop()
        demo_match_case()
        demo_nested_loops()
        guessing_game()
        grade_system()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()