import pygame
import sys
import random
import math

# ============ 初始化与常量 ============
# 初始化 Pygame
pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fish Simulation")
clock = pygame.time.Clock()

# 颜色定义
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# ============ Fish 类 ============
class Fish:
    """表示一条鱼，包含移动和绘制行为"""
    def __init__(self):
        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(100, HEIGHT - 100)
        self.angle = random.uniform(0, 2 * math.pi)

        self.base_speed = round(random.uniform(1.5,2.5),2)
        self.speed = self.base_speed
        
        self.max_turn_rate = math.radians(5)  # 最大转向速率
        self.length = 12  # 鱼体长度
        self.width = 8   # 鱼体宽度
        self.visualradius = 40    #视野半径
        self.alignment_weight = 0.5  # 对齐行为影响系数
        self.separation_weight = 1.0  # 避障行为影响系数
        self.cohesion_weight = 0.5  # 聚集行为影响系数
        self.chasefood_weight = 0.8 #追逐食物强度
        
        # self.is_lonely = False  # 当前是否孤独
        # self.start_lonely_time = None  # 孤独开始时间
        # self.random_lonely_interval = None  # 随机间隔时间（3~5 秒）
        self.target_angle = None  

        # 定义三种蓝色并随机选择一种作为鱼的颜色
        self.color = random.choice([
            (0, 100, 255),  # 蓝色较浅
            (0, 150, 255),  # 中等蓝色
            (0, 200, 255)   # 深蓝色
        ])

    def move(self, foods, fishes):
        """鱼的移动逻辑，包含避障、对齐、聚集、追逐食物和减速行为"""

        # neighbor_count = 0

        # # 一次循环处理多个行为
        # for other in fishes:
        #     if other is self:
        #         continue
        #     dx = other.x - self.x
        #     dy = other.y - self.y
        #     distance = math.hypot(dx, dy)

        #     if distance < 2 * self.visualradius:
        #         neighbor_count += 1
        # # 判断当前是否孤独
        # current_is_lonely = (neighbor_count == 0)

        # # 处理孤独状态变化
        # if current_is_lonely != self.is_lonely:
        #     if current_is_lonely:
        #         # 进入孤独状态：开始计时 + 生成随机间隔时间
        #         self.start_lonely_time = time.time()
        #         self.random_lonely_interval = random.uniform(3, 5)  # 3~5 秒
        #     else:
        #         # 退出孤独状态：停止计时
        #         self.start_lonely_time = None
        #         self.random_lonely_interval = None
        #     self.is_lonely = current_is_lonely

        # # 孤独减速机制
        # if self.is_lonely:
        #     self.speed = max(0.5, self.speed * 0.8)  # 减速到最低 0.5
        #     # 检查是否达到随机间隔时间
        #     if self.start_lonely_time is not None:
        #         elapsed_time = time.time() - self.start_lonely_time
        #         if elapsed_time >= self.random_lonely_interval:
        #             # 改变方向 + 重置计时器
        #             self.target_angle = random.uniform(0, 2 * math.pi)
        #             self.start_lonely_time = time.time()  # 重置时间
        #             self.random_lonely_interval = random.uniform(3, 5)  # 新的随机间隔
        # else:
        #     self.speed = self.base_speed  # 恢复正常速度

        # # 调用平滑转向逻辑
        # if self.is_lonely and self.target_angle is not None:
        #     self.adjust_angle(self.target_angle, weight=1.0)
        # 更新行为
        self.align(fishes)
        self.separate(fishes)
        self.cohesion(fishes) 
        self.seek_food(foods)

        # 计算新位置
        new_x = self.x + math.cos(self.angle) * self.speed
        new_y = self.y + math.sin(self.angle) * self.speed
        self.x, self.y = new_x, new_y

        # 边界穿越
        self.handle_boundary()

    def align(self, fishes):
        """对齐行为：与邻近鱼保持一致方向"""
        align_vector_x = 0.0
        align_vector_y = 0.0
        neighbor_count = 0

        for other in fishes:
            if other is self:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            distance = math.hypot(dx, dy)
            if distance < self.visualradius:  
                align_vector_x += math.cos(other.angle)
                align_vector_y += math.sin(other.angle)
                neighbor_count += 1

        if neighbor_count > 0:
            align_angle = math.atan2(align_vector_y, align_vector_x)
            self.adjust_angle(align_angle, self.alignment_weight)


    def separate(self, fishes):
        """避障行为：远离邻近鱼"""
        avoid_vector_x = 0.0
        avoid_vector_y = 0.0

        for other in fishes:
            if other is self:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            distance = math.hypot(dx, dy)
            if 0 < distance < 0.7 * self.visualradius:  
                weight = 1.0 / (distance * distance)
                avoid_dir_x = -dx / distance
                avoid_dir_y = -dy / distance
                avoid_vector_x += avoid_dir_x * weight * self.separation_weight
                avoid_vector_y += avoid_dir_y * weight * self.separation_weight

        if avoid_vector_x != 0 or avoid_vector_y != 0:
            avoid_angle = math.atan2(avoid_vector_y, avoid_vector_x)
            self.adjust_angle(avoid_angle, self.separation_weight)

    def cohesion(self, fishes):
        """聚集行为：向邻近鱼群的中心移动"""
        center_x = 0.0
        center_y = 0.0
        neighbor_count = 0

        for other in fishes:
            if other is self:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            distance = math.hypot(dx, dy)
            if distance < self.visualradius:  # 检测半径
                center_x += other.x
                center_y += other.y
                neighbor_count += 1

        if neighbor_count > 0:
            center_x /= neighbor_count
            center_y /= neighbor_count
            target_angle = math.atan2(center_y - self.y, center_x - self.x)
            self.adjust_angle(target_angle, self.cohesion_weight)

    def seek_food(self, foods):
        """鱼粮追逐行为：向最近的鱼粮移动"""
        if not foods:
            return

        closest_food = None
        min_distance = float('inf')
        food_sense_radius = 500  # 新增：鱼粮感知半径

        for food in foods:
            if not food.exists:
                continue

            dx = food.x - self.x
            dy = food.y - self.y
            distance = math.hypot(dx, dy)

            if distance > food_sense_radius:  # 只处理半径 500 以内的食物
                continue

            if distance < min_distance:
                min_distance = distance
                closest_food = food

        if closest_food:
            if math.hypot(closest_food.x - self.x, closest_food.y - self.y) < (self.length + closest_food.radius):
                closest_food.exists = False
            else:
                target_angle = math.atan2(closest_food.y - self.y, closest_food.x - self.x)
                self.adjust_angle(target_angle, self.chasefood_weight)


    def adjust_angle(self, target_angle, weight=1.0):
        """平滑调整角度"""
        angle_diff = target_angle - self.angle
        # 角度归一化
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        turn_amount = max(min(angle_diff, self.max_turn_rate * weight), -self.max_turn_rate * weight)
        self.angle += turn_amount

    def handle_boundary(self):
        """边界穿越逻辑"""
        if self.x < 0:
            self.x = WIDTH
        elif self.x > WIDTH:
            self.x = 0

        if self.y < 0:
            self.y = HEIGHT
        elif self.y > HEIGHT:
            self.y = 0

    def get_vertices(self):
        """计算鱼的三角形顶点"""
        dir_x = math.cos(self.angle)
        dir_y = math.sin(self.angle)
        left_x = -dir_y
        left_y = dir_x

        head_x = self.x + dir_x * self.length
        head_y = self.y + dir_y * self.length
        tail_left_x = self.x - dir_x * (self.length/2) + left_x * (self.width/2)
        tail_left_y = self.y - dir_y * (self.length/2) + left_y * (self.width/2)
        tail_right_x = self.x - dir_x * (self.length/2) - left_x * (self.width/2)
        tail_right_y = self.y - dir_y * (self.length/2) - left_y * (self.width/2)

        return [(head_x, head_y), (tail_left_x, tail_left_y), (tail_right_x, tail_right_y)]

    def draw(self, screen):
        """绘制鱼"""
        points = self.get_vertices()
        pygame.draw.polygon(screen, self.color, points)

# ============ Food 类 ============
class Food:
    """表示鱼粮"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.exists = True
        self.radius = 5

    def draw(self, screen):
        """绘制鱼粮"""
        if self.exists:
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)

# ============ 主函数 ============
def main():
    # 初始化实体
    fishes = [Fish() for _ in range(100)]  # 创建20条鱼
    foods = []

    running = True
    while running:
        # 事件处理
        handle_events(foods)

        # 更新逻辑
        update_fishes(fishes, foods)
        update_foods(foods)

        # 绘制逻辑
        screen.fill(BLACK)
        draw_fishes(fishes, screen)
        draw_foods(foods, screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

# ============ 辅助函数 ============
def handle_events(foods):
    """处理用户事件（如鼠标点击生成鱼粮）"""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键生成鱼粮
                for _ in range(5):  # 🔁 循环 3 次
                    x = random.randint(0, WIDTH) 
                    y = random.randint(0, HEIGHT)  
                    foods.append(Food(x, y))

def update_fishes(fishes, foods):
    """更新所有鱼的状态"""
    for fish in fishes:
        fish.move(foods, fishes)

def update_foods(foods):
    """更新鱼粮状态（无动作）"""
    # 当前无需额外更新逻辑
    pass

def draw_fishes(fishes, screen):
    """绘制所有鱼"""
    for fish in fishes:
        fish.draw(screen)

def draw_foods(foods, screen):
    """绘制所有鱼粮"""
    for food in foods:
        food.draw(screen)

# ============ 程序入口 ============
if __name__ == "__main__":
    main()