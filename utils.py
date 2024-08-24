import os
import time
import pygame

SCALE = 20
ORIG_SURF = pygame.Surface((32, 24))
PIX_ARRAY = pygame.PixelArray(ORIG_SURF)

def get_colour(value):
    R_colour, G_colour, B_colour = 0, 0, 0
    if 0 <= value < 30:
        R_colour = 0
        G_colour = 0
        B_colour = 20 + (120.0/30.0) * value
    elif 30 <= value < 60:
        R_colour = (120.0 / 30) * (value - 30.0)
        G_colour = 0
        B_colour = 140 - (60.0/30.0) * (value - 30.0)
    elif 60 <= value < 90:
        R_colour = 120 + (135.0/30.0) * (value - 60.0)
        G_colour = 0
        B_colour = 80 - (70.0/30.0) * (value - 60.0)
    elif 90 <= value < 120:
        R_colour = 255
        G_colour = 0 + (60.0/30.0) * (value - 90.0)
        B_colour = 10 - (10.0/30.0) * (value - 90.0)
    elif 120 <= value < 150:
        R_colour = 255
        G_colour = 60 + (175.0/30.0) * (value - 120.0)
        B_colour = 0
    elif 150 <= value <= 180:
        R_colour = 255
        G_colour = 235 + (20.0/30.0) * (value - 150.0)
        B_colour = 0 + 255.0/30.0 * (value - 150.0)
    return R_colour, G_colour, B_colour



def bio_linear_interpolation(dst_x:int, dst_y:int, src_data:list):
    """双线性插值"""  
    def getValue(y, x, _src_data):
        return _src_data[x + (23 - y) * 32]

    src_x = (dst_x*10000 + 5000) // SCALE - 5000
    src_y = (dst_y*10000 + 5000) // SCALE - 5000

    # 找到四个最近邻点的位置
    src_x0 = src_x // 10000
    src_y0 = src_y // 10000
    src_x1 = src_x0+1
    src_y1 = src_y0+1

    # 确保不超出源图像边界
    src_x0 = max(src_x0, 0)
    src_y0 = max(src_y0, 0)
    src_x1 = min(src_x1, 31)
    src_y1 = min(src_y1, 23)

    # 计算分数部分
    frac_x = src_x - src_x0 * 10000
    frac_y = src_y - src_y0 * 10000

    # 获取四个最近邻点的值
    value00 = getValue(src_y0, src_x0, src_data)
    value01 = getValue(src_y0, src_x1, src_data)
    value10 = getValue(src_y1, src_x0, src_data)
    value11 = getValue(src_y1, src_x1, src_data)
    # 沿x轴的线性插值
    v0 = value00 * (10000 - frac_x) + value01 * frac_x
    v1 = value10 * (10000 - frac_x) + value11 * frac_x

    v0 = v0 // 10000
    v1 = v1 // 10000
    # 沿y轴的线性插值
    return (v0 * (10000 - frac_y) + v1 * frac_y) / 10000


def draw_heatmap(matrix, draw_func):
    max_t, min_t, avg_t = matrix[:3]
    max_t += 0.1
    for k, temp in enumerate(matrix[3::]):
        value = 180.0 * (temp - min_t) / (max_t - min_t)
        r, g, b = get_colour(value)
        draw_func(k, (r, g, b))


def draw_heatmap_upsample(matrix):
    max_t, min_t, avg_t = matrix[:3]
    max_t += 0.1
    for k, temp in enumerate(matrix[3::]):
        value = 180.0 * (temp - min_t) / (max_t - min_t)
        r, g, b = get_colour(value)
        x = k % 32
        y = k // 32
        PIX_ARRAY[x, 23-y] = (r, g, b)
    return pygame.transform.smoothscale(PIX_ARRAY.make_surface(), (32*SCALE, 24*SCALE))


def save_frame(matrix:list, surf:pygame.Surface):
    lines = []
    line = []
    for k, data in enumerate(matrix[3::]):
    # for k, data in enumerate([i for i in range(768)]):
        if k  %  32 != 0:
            line.append(data)
        elif len(line) > 0:
            lines.insert(0, line)
            line = []
            line.append(data)
        else:
            line.append(data)
    lines.insert(0, line)
    with open(f'{time.strftime("%m-%d-%H-%M-%S")}.csv', 'w', encoding="utf-8") as f:
        f.write(' ,')
        [f.write(f"{k},") for k, _ in enumerate(lines[0])]
        f.write('\n')
        for k, line in enumerate(lines):
            f.write(f"{k},")
            for data in line:
                f.write(f"{data},")
            f.write('\n')
    
    cap_rect = pygame.Rect(0, 50, 20*32, 20*24)
    screen_cap = surf.subsurface(cap_rect)
    pygame.image.save(screen_cap, f'{time.strftime("%m-%d-%H-%M-%S")}.png')

def save_curv(times:list, points_bytime:list):
    with open(f'curv_{time.strftime("%m-%d-%H-%M-%S")}.csv', 'w', encoding="utf-8") as f:
        # by_point = [[] for _ in range(len(times))]
        # for _time in times:
        #     f.write(f"{_time},")
        # f.write('\n')
        # for time_stamps in points_bytime:
        #     for point in time_stamps:
        #         f.write(f"{point},")
        #     f.write('\n')
        f.write("time(s),max,")
        for i in range(len(points_bytime[0])-1):
            f.write(f"point_{i},")
        f.write('\n')
        for t, time_stamps in enumerate(points_bytime):
            f.write(f'{times[t]:.3f},')
            for temp in time_stamps:
                f.write(f"{temp},")
            f.write('\n')
