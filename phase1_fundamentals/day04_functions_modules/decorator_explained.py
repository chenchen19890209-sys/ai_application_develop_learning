"""
装饰器详解 - 用最简单的方式理解装饰器

装饰器的本质：在不修改原函数的情况下，给函数添加额外功能
"""

# ==================== 第一部分：不用装饰器会怎样？====================

print("=" * 60)
print("场景1：如果我们想统计每个函数的执行时间")
print("=" * 60)

import time

# 假设我们有3个函数，都想知道它们执行了多久

def say_hello():
    """普通问候函数"""
    print("你好！")
    time.sleep(1)  # 模拟耗时操作

def calculate_sum():
    """计算求和函数"""
    total = sum(range(1000))
    print(f"1到999的和是: {total}")
    time.sleep(0.5)

def greet_person(name):
    """带参数的问候函数"""
    print(f"你好，{name}！")
    time.sleep(0.8)

# ❌ 笨办法：在每个函数里手动加计时代码
def say_hello_with_timer():
    start = time.time()
    print("你好！")
    time.sleep(1)
    elapsed = time.time() - start
    print(f"say_hello_with_timer 耗时: {elapsed:.3f}秒")

def calculate_sum_with_timer():
    start = time.time()
    total = sum(range(1000))
    print(f"1到999的和是: {total}")
    time.sleep(0.5)
    elapsed = time.time() - start
    print(f"calculate_sum_with_timer 耗时: {elapsed:.3f}秒")

# 问题：如果有100个函数怎么办？要改100次！太麻烦了！


# ==================== 第二部分：装饰器登场！====================

print("\n" + "=" * 60)
print("场景2：使用装饰器 - 一次编写，到处使用")
print("=" * 60)

def timer_decorator(func):
    """
    这是一个装饰器函数
    
    工作原理：
    1. 接收一个函数作为参数（func）
    2. 在里面定义一个新函数（wrapper）
    3. wrapper 会先记录开始时间，然后调用原函数，再记录结束时间
    4. 最后返回这个 wrapper 函数
    
    就像给函数穿了一件"计时外套"
    """
    def wrapper(*args, **kwargs):
        # 在调用原函数之前做的事
        start = time.time()
        
        # 调用原函数（把参数传进去）
        result = func(*args, **kwargs)
        
        # 在调用原函数之后做的事
        elapsed = time.time() - start
        print(f"⏱️  {func.__name__} 耗时: {elapsed:.3f}秒")
        
        # 返回原函数的结果
        return result
    
    return wrapper


# ✅ 使用装饰器：只需要在函数前面加 @timer_decorator
@timer_decorator
def say_hello_v2():
    """普通问候函数（加了装饰器）"""
    print("你好！")
    time.sleep(1)

@timer_decorator
def calculate_sum_v2():
    """计算求和函数（加了装饰器）"""
    total = sum(range(1000))
    print(f"1到999的和是: {total}")
    time.sleep(0.5)

@timer_decorator
def greet_person_v2(name):
    """带参数的问候函数（加了装饰器）"""
    print(f"你好，{name}！")
    time.sleep(0.8)


print("\n--- 测试装饰后的函数 ---")
say_hello_v2()
print()
calculate_sum_v2()
print()
greet_person_v2("张三")


# ==================== 第三部分：装饰器到底做了什么？====================

print("\n" + "=" * 60)
print("场景3：揭秘装饰器的等价写法")
print("=" * 60)

# 下面两种写法是完全等价的：

# 写法1：使用 @ 符号（推荐）
@timer_decorator
def my_function():
    print("Hello")

# 写法2：手动包装（不常用，但能帮助理解）
def my_function_original():
    print("Hello")

my_function_original = timer_decorator(my_function_original)

# 这两种写法效果一模一样！
# @timer_decorator 只是一个语法糖，让代码更简洁


# ==================== 第四部分：更多实用装饰器示例====================

print("\n" + "=" * 60)
print("场景4：其他常见的装饰器应用")
print("=" * 60)

# 示例1：日志记录装饰器
def log_decorator(func):
    """记录函数调用的日志"""
    def wrapper(*args, **kwargs):
        print(f"📝 [LOG] 调用函数: {func.__name__}")
        print(f"   参数: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"   返回值: {result}")
        return result
    return wrapper

@log_decorator
def add(a, b):
    """加法函数"""
    return a + b

print("\n--- 测试日志装饰器 ---")
result = add(3, 5)


# 示例2：权限检查装饰器
def require_login(func):
    """检查用户是否登录"""
    def wrapper(*args, **kwargs):
        # 模拟检查登录状态
        is_logged_in = True  # 实际项目中从session获取
        
        if not is_logged_in:
            print("❌ 请先登录！")
            return None
        
        print("✅ 已登录，可以访问")
        return func(*args, **kwargs)
    return wrapper

@require_login
def view_profile():
    """查看个人资料"""
    print("显示用户资料...")
    return {"name": "张三", "age": 25}

print("\n--- 测试权限装饰器 ---")
view_profile()


# 示例3：重试装饰器（AI开发中很常用！）
def retry(max_attempts=3):
    """失败时自动重试"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    print(f"尝试第 {attempt} 次...")
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"失败: {e}")
                    if attempt == max_attempts:
                        raise  # 最后一次也失败，抛出异常
            return None
        return wrapper
    return decorator

@retry(max_attempts=3)
def call_llm_api(prompt):
    """调用LLM API（可能失败）"""
    import random
    if random.random() < 0.7:  # 70%概率失败
        raise ConnectionError("网络超时")
    return f"回答: {prompt}"

print("\n--- 测试重试装饰器 ---")
try:
    result = call_llm_api("什么是AI？")
    print(f"成功: {result}")
except Exception as e:
    print(f"最终失败: {e}")


# ==================== 第五部分：叠加多个装饰器====================

print("\n" + "=" * 60)
print("场景5：一个函数可以用多个装饰器")
print("=" * 60)

@log_decorator      # 最外层：记录日志
@timer_decorator    # 中间层：计时间
@require_login      # 最内层：检查登录
def get_user_data(user_id):
    """获取用户数据"""
    time.sleep(0.5)
    return {"id": user_id, "name": "张三"}

print("\n--- 测试多重装饰器 ---")
get_user_data(123)


# ==================== 总结 ====================

print("\n" + "=" * 60)
print("🎯 装饰器核心要点总结")
print("=" * 60)
print("""
1. 装饰器是什么？
   → 一个"包装函数"，给原函数添加额外功能

2. 为什么要用装饰器？
   → 避免重复代码，保持函数干净

3. 怎么用？
   → 在函数前加 @装饰器名

4. 常见应用场景：
   • 计时间（性能分析）
   • 记日志（调试追踪）
   • 权限检查（安全控制）
   • 自动重试（容错处理）
   • 缓存结果（提升速度）

5. 记住这个比喻：
   装饰器就像给函数穿衣服
   - 函数本身不变
   - 但多了额外的功能（衣服）
   - 可以随时换不同的衣服（装饰器）
""")
