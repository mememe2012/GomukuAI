from typing import Literal
import pygame as pg
from rich.console import Console
import random
import math
import sys

CONSOLE = Console()

def SetClock(fps:int=60):
    return pg.time.Clock().tick(fps)

def CreateScreen(size:tuple=(640,480), title:str="Pygame Window", icon:str=None):
    screen = pg.display.set_mode(size)
    pg.display.set_caption(title)
    if icon:
        try:
            icon_surface = pg.image.load(icon)
            pg.display.set_icon(icon_surface)
        except Exception as e:
            CONSOLE.print(f"[ERROR] Failed to load icon '{icon}': {e}", style="red")
    return screen

import pygame
import random
import math

class MeteorShower:
    """
    一个用于在Pygame窗口中创建流星雨效果的类。
    """

    def __init__(self, screen_width, screen_height, meteor_count=50, max_speed=10, min_speed=5):
        """
        初始化流星雨。

        参数:
            screen_width (int): 显示窗口的宽度。
            screen_height (int): 显示窗口的高度。
            meteor_count (int): 流星的数量，默认为50。
            max_speed (int): 流星的最大速度，默认为10。
            min_speed (int): 流星的最小速度，默认为5。
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.meteor_count = meteor_count
        self.max_speed = max_speed
        self.min_speed = min_speed

        # 初始化流星列表
        self.meteors = []
        self._init_meteors()

    def _init_meteors(self):
        """在屏幕外随机位置初始化所有流星。"""
        self.meteors = []
        for _ in range(self.meteor_count):
            # 流星从屏幕右侧或上侧之外随机位置开始
            start_x = random.randint(self.screen_width, self.screen_width + 100)
            start_y = random.randint(0, self.screen_height // 2)  # 主要从上半部分出现

            # 随机速度（斜向下方向）
            speed = random.uniform(self.min_speed, self.max_speed)
            # 随机角度（大致指向左下方）
            angle = random.uniform(math.pi * 0.7, math.pi * 0.9)  # 约225度到270度之间
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed

            # 流星属性：位置、速度、长度、颜色、生命值（用于拖尾）
            meteor = {
                'x': start_x,
                'y': start_y,
                'vx': velocity_x,
                'vy': velocity_y,
                'length': random.randint(15, 30),  # 流星长度
                'color': self._random_meteor_color(),  # 流星颜色
                'trail': [],  # 拖尾轨迹点列表
                'max_trail': 8  # 最大拖尾点数
            }
            self.meteors.append(meteor)

    def _random_meteor_color(self):
        """生成随机的流星颜色（偏向白色、浅蓝、浅黄）。"""
        base_color = random.choice(['white', 'lightblue', 'lightyellow', 'cyan'])
        if base_color == 'white':
            return (255, 255, 255)
        elif base_color == 'lightblue':
            return (173, 216, 230)
        elif base_color == 'lightyellow':
            return (255, 255, 224)
        else:  # cyan
            return (0, 255, 255)

    def update(self):
        """更新所有流星的位置和状态。"""
        for meteor in self.meteors:
            # 更新位置
            meteor['x'] += meteor['vx']
            meteor['y'] += meteor['vy']

            # 添加当前位置到拖尾
            meteor['trail'].append((int(meteor['x']), int(meteor['y'])))
            # 保持拖尾长度不超过最大值
            if len(meteor['trail']) > meteor['max_trail']:
                meteor['trail'].pop(0)

            # 如果流星完全飞出屏幕左侧或底部，则重置它
            if (meteor['x'] < -meteor['length'] or
                meteor['y'] > self.screen_height + meteor['length']):
                self._reset_meteor(meteor)

    def _reset_meteor(self, meteor):
        """将飞出屏幕的流星重置到起始位置。"""
        meteor['x'] = random.randint(self.screen_width, self.screen_width + 100)
        meteor['y'] = random.randint(0, self.screen_height // 2)
        speed = random.uniform(self.min_speed, self.max_speed)
        angle = random.uniform(math.pi * 0.7, math.pi * 0.9)
        meteor['vx'] = math.cos(angle) * speed
        meteor['vy'] = math.sin(angle) * speed
        meteor['length'] = random.randint(15, 30)
        meteor['color'] = self._random_meteor_color()
        meteor['trail'] = []  # 清空拖尾

    def draw(self, screen):
        """
        在给定的Pygame屏幕上绘制所有流星及其拖尾。

        参数:
            screen (pygame.Surface): 要绘制流星的Pygame表面。
        """
        for meteor in self.meteors:
            # 计算流星的头部和尾部
            head_x = int(meteor['x'])
            head_y = int(meteor['y'])
            # 尾部根据速度方向反向计算
            tail_x = int(meteor['x'] - meteor['vx'] * meteor['length'] / meteor['max_speed'])
            tail_y = int(meteor['y'] - meteor['vy'] * meteor['length'] / meteor['max_speed'])

            # 1. 绘制拖尾（从旧到新，逐渐变亮/变实）
            if len(meteor['trail']) > 1:
                for i in range(len(meteor['trail']) - 1):
                    # 拖尾的透明度和粗细逐渐变化
                    alpha = int(255 * (i + 1) / len(meteor['trail']))
                    width = max(1, int(3 * (i + 1) / len(meteor['trail'])))
                    # 创建临时颜色（带透明度效果，通过混合实现）
                    # 注意：这里简化处理，实际Pygame绘制线没有直接alpha，可通过画多条细线或使用surface模拟
                    # 此处采用固定颜色渐变
                    color = meteor['color']
                    pygame.draw.line(screen, color,
                                     meteor['trail'][i],
                                     meteor['trail'][i + 1],
                                     width)

            # 2. 绘制流星主体（从尾部到头部的线段）
            pygame.draw.line(screen, meteor['color'], (tail_x, tail_y), (head_x, head_y), 3)

            # 3. 可选：在流星头部绘制一个更亮的点
            pygame.draw.circle(screen, (255, 255, 255), (head_x, head_y), 2)

    def set_meteor_count(self, count):
        """动态改变流星的数量。"""
        self.meteor_count = count
        # 如果数量增加，添加新的流星
        while len(self.meteors) < count:
            self._add_new_meteor()
        # 如果数量减少，移除多余的流星
        while len(self.meteors) > count:
            self.meteors.pop()

    def _add_new_meteor(self):
        """添加一个新的流星到列表。"""
        start_x = random.randint(self.screen_width, self.screen_width + 100)
        start_y = random.randint(0, self.screen_height // 2)
        speed = random.uniform(self.min_speed, self.max_speed)
        angle = random.uniform(math.pi * 0.7, math.pi * 0.9)
        velocity_x = math.cos(angle) * speed
        velocity_y = math.sin(angle) * speed

        meteor = {
            'x': start_x,
            'y': start_y,
            'vx': velocity_x,
            'vy': velocity_y,
            'length': random.randint(15, 30),
            'color': self._random_meteor_color(),
            'trail': [],
            'max_trail': 8
        }
        self.meteors.append(meteor)

def test():
    pg.init()
    screen = CreateScreen((800, 600), "Meteor Shower Test")
    meteor_shower = MeteorShower(screen.get_width(), screen.get_height(), meteor_count=100)

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        meteor_shower.update()

        screen.fill((0, 0, 0))  # 清空屏幕
        meteor_shower.draw(screen)  # 绘制流星雨
        pg.display.flip()  # 更新显示

        SetClock(60)  # 控制帧率

    pg.quit()

if __name__ == "__main__":
    test()
