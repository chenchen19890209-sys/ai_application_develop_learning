"""
生成器的多种使用方式 - 不仅限于for循环

很多人以为生成器只能用在 for 循环中，其实还有很多其他用法！
"""

# ==================== 第一部分：基础用法（大家熟知的）====================

print("=" * 70)
print("📋 用法1：在 for 循环中使用（最常见）")
print("=" * 70)

def count_up_to(n):
    """生成1到n的数字"""
    for i in range(1, n + 1):
        yield i

# ✅ 在 for 循环中使用
print("for 循环:")
for num in count_up_to(5):
    print(f"  {num}", end=" ")
print()


# ==================== 第二部分：手动控制（next函数）====================

print("\n" + "=" * 70)
print("🎮 用法2：手动调用 next() - 精确控制")
print("=" * 70)

gen = count_up_to(5)

print("手动控制生成器:")
print(f"  第1次 next(): {next(gen)}")
print(f"  第2次 next(): {next(gen)}")
print(f"  第3次 next(): {next(gen)}")

# 可以中途停止，下次继续
print("  ...暂停...")
print(f"  第4次 next(): {next(gen)}")
print(f"  第5次 next(): {next(gen)}")


# ==================== 第三部分：转换为其他数据结构====================

print("\n" + "=" * 70)
print("🔄 用法3：转换为列表、元组、集合等")
print("=" * 70)

gen = (x ** 2 for x in range(10))

# 转换为列表
numbers_list = list(gen)
print(f"转换为列表: {numbers_list}")

# 注意：生成器已经耗尽了，需要重新创建
gen = (x ** 2 for x in range(10))

# 转换为元组
numbers_tuple = tuple(gen)
print(f"转换为元组: {numbers_tuple}")

# 转换为集合（自动去重）
gen = (x % 3 for x in range(10))
numbers_set = set(gen)
print(f"转换为集合: {numbers_set}")

# 转换为字典
gen = ((x, x ** 2) for x in range(5))
numbers_dict = dict(gen)
print(f"转换为字典: {numbers_dict}")


# ==================== 第四部分：解包赋值====================

print("\n" + "=" * 70)
print("📦 用法4：解包赋值（Unpacking）")
print("=" * 70)

def get_coordinates():
    """生成坐标点"""
    yield 10
    yield 20
    yield 30

# 直接解包
x, y, z = get_coordinates()
print(f"解包赋值: x={x}, y={y}, z={z}")

# 部分解包
gen = get_coordinates()
first = next(gen)
remaining = list(gen)
print(f"部分解包: first={first}, remaining={remaining}")


# ==================== 第五部分：作为函数参数====================

print("\n" + "=" * 70)
print("📞 用法5：直接作为函数参数")
print("=" * 70)

# sum() 函数可以直接接收生成器
total = sum(x ** 2 for x in range(10))
print(f"sum() 直接使用生成器: {total}")

# max() 和 min()
gen = (x ** 2 for x in range(10))
print(f"max() 直接使用生成器: {max(gen)}")

gen = (x ** 2 for x in range(10))
print(f"min() 直接使用生成器: {min(gen)}")

# any() 和 all()
gen = (x > 5 for x in range(10))
print(f"any() 检查是否有大于5的: {any(gen)}")

gen = (x >= 0 for x in range(10))
print(f"all() 检查是否都>=0: {all(gen)}")

# sorted()
gen = (x % 7 for x in range(20))
print(f"sorted() 排序: {sorted(gen)}")


# ==================== 第六部分：链式组合（管道模式）====================

print("\n" + "=" * 70)
print("🔗 用法6：链式组合 - 数据管道")
print("=" * 70)

def generate_numbers():
    """生成数字"""
    for i in range(1, 11):
        yield i

def filter_even(numbers):
    """过滤偶数"""
    for num in numbers:
        if num % 2 == 0:
            yield num

def double_numbers(numbers):
    """翻倍"""
    for num in numbers:
        yield num * 2

# 链式组合：像管道一样连接
pipeline = double_numbers(filter_even(generate_numbers()))

print("数据管道: 生成 → 过滤偶数 → 翻倍")
print(f"  结果: {list(pipeline)}")
# 输出: [4, 8, 12, 16, 20]


# ==================== 第七部分：条件判断====================

print("\n" + "=" * 70)
print("❓ 用法7：在条件判断中使用")
print("=" * 70)

def has_positive(numbers):
    """检查是否有正数"""
    return any(x > 0 for x in numbers)

test_data = [-1, -2, 3, -4, 5]
print(f"数据: {test_data}")
print(f"是否有正数? {has_positive(test_data)}")

# 注意：生成器表达式可以直接用在 if 语句中
if any(x > 10 for x in range(20)):
    print("✅ 存在大于10的数")


# ==================== 第八部分：zip 和 enumerate====================

print("\n" + "=" * 70)
print("🔀 用法8：与 zip、enumerate 配合")
print("=" * 70)

names = ("张三", "李四", "王五")
scores = (90, 85, 92)

# zip 配对
paired = zip(names, scores)
print("zip 配对:")
for name, score in paired:
    print(f"  {name}: {score}分")

# enumerate 编号
gen = (x ** 2 for x in range(5))
print("\nenumerate 编号:")
for index, value in enumerate(gen):
    print(f"  [{index}] = {value}")


# ==================== 第九部分：文件处理====================

print("\n" + "=" * 70)
print("📄 用法9：文件处理中的妙用")
print("=" * 70)

# 创建一个测试文件
with open("test_data.txt", "w", encoding="utf-8") as f:
    f.write("苹果,5\n")
    f.write("香蕉,3\n")
    f.write("橙子,8\n")
    f.write("葡萄,12\n")

# 逐行读取并处理
def read_fruit_prices(filename):
    """读取水果价格"""
    with open(filename, encoding="utf-8") as f:
        for line in f:
            name, price = line.strip().split(",")
            yield (name, int(price))

# 找出价格大于5的水果
expensive_fruits = [
    name for name, price in read_fruit_prices("test_data.txt")
    if price > 5
]
print(f"价格>5的水果: {expensive_fruits}")

# 计算平均价格
prices = (price for _, price in read_fruit_prices("test_data.txt"))
avg_price = sum(prices) / 4
print(f"平均价格: {avg_price:.2f}")


# ==================== 第十部分：递归生成器====================

print("\n" + "=" * 70)
print("🔄 用法10：递归生成器")
print("=" * 70)

def flatten(nested_list):
    """
    扁平化嵌套列表
    
    例如: [1, [2, 3], [4, [5, 6]]] → [1, 2, 3, 4, 5, 6]
    """
    for item in nested_list:
        if isinstance(item, list):
            # 递归处理子列表
            yield from flatten(item)
        else:
            yield item

nested = [1, [2, 3], [4, [5, 6]], 7]
print(f"嵌套列表: {nested}")
print(f"扁平化后: {list(flatten(nested))}")


# ==================== 第十一部分：协程（高级用法）====================

print("\n" + "=" * 70)
print("🤖 用法11：协程 - 双向通信")
print("=" * 70)

def calculator():
    """
    一个简单的计算器协程
    
    可以接收操作指令并返回结果
    """
    result = 0
    while True:
        # 接收操作
        operation = yield result
        
        if operation is None:
            break
        
        op_type, value = operation
        
        if op_type == "add":
            result += value
        elif op_type == "multiply":
            result *= value
        elif op_type == "reset":
            result = 0

# 使用协程
calc = calculator()
next(calc)  # 启动协程

print("计算器协程:")
print(f"  初始值: {calc.send(('add', 10))}")      # 0 + 10 = 10
print(f"  乘以3: {calc.send(('multiply', 3))}")   # 10 * 3 = 30
print(f"  加5: {calc.send(('add', 5))}")          # 30 + 5 = 35
print(f"  重置: {calc.send(('reset', 0))}")       # 0


# ==================== 第十二部分：实际应用案例 ====================

print("\n" + "=" * 70)
print("🌟 用法12：AI开发中的实际应用")
print("=" * 70)

# 应用1：流式处理LLM响应
def simulate_llm_stream():
    """模拟LLM流式输出"""
    response = "人工智能是计算机科学的一个分支"
    for char in response:
        yield char
        import time
        time.sleep(0.05)  # 模拟网络延迟

print("流式输出LLM回答:")
print("  ", end="")
for token in simulate_llm_stream():
    print(token, end="", flush=True)
print()

# 应用2：分批处理训练数据
def batch_generator(data, batch_size):
    """生成训练批次"""
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

train_data = list(range(25))
batches = batch_generator(train_data, batch_size=5)

print("\n分批处理训练数据:")
for i, batch in enumerate(batches, 1):
    print(f"  批次{i}: {batch}")

# 应用3：数据增强管道
def augment_data(images):
    """数据增强生成器"""
    for img in images:
        # 原始图像
        yield img
        # 翻转图像（模拟）
        yield f"{img}_flipped"
        # 旋转图像（模拟）
        yield f"{img}_rotated"

original_images = ["img1", "img2"]
augmented = list(augment_data(original_images))
print(f"\n数据增强: {augmented}")


# ==================== 总结 ====================

print("\n" + "=" * 70)
print("🎯 生成器的所有用法总结")
print("=" * 70)
print("""
生成器可以用在以下场景：

1. ✅ for 循环（最常见）
   for item in generator:
       process(item)

2. ✅ 手动调用 next()
   value = next(generator)

3. ✅ 转换为数据结构
   list(generator)
   tuple(generator)
   set(generator)
   dict(generator)

4. ✅ 解包赋值
   a, b, c = generator()

5. ✅ 作为函数参数
   sum(x for x in range(10))
   max(generator)
   any(generator)
   sorted(generator)

6. ✅ 链式组合（管道模式）
   func3(func2(func1(generator)))

7. ✅ 条件判断
   if any(x > 0 for x in data):

8. ✅ 与内置函数配合
   zip(gen1, gen2)
   enumerate(generator)

9. ✅ 文件处理
   for line in file_generator():

10. ✅ 递归（yield from）
    yield from recursive_generator()

11. ✅ 协程（send/receive）
    value = generator.send(data)

12. ✅ AI应用
    • 流式输出
    • 分批训练
    • 数据增强
    • 数据管道

核心优势：
• 省内存（惰性求值）
• 可组合（管道模式）
• 灵活（多种使用方式）
""")

# 清理测试文件
import os
if os.path.exists("test_data.txt"):
    os.remove("test_data.txt")

print("\n✅ 演示完成！")
