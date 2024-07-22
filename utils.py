import os
import time
import pygame

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


def draw_heatmap(matrix, daw_func):
    max_t, min_t, avg_t = matrix[:3]
    max_t += 0.1
    for k, temp in enumerate(matrix[3::]):
        value = 180.0 * (temp - min_t) / (max_t - min_t)
        
        # if (temp < -41 and temp > 301):
        #     value = 180.0 * (temp - min_t) / (max_t - min_t)
        # elif(temp>0):
        #     value = 180.0 * (matrix[k-1] - min_t) / (max_t - min_t)
        # else:
        #     value = 180.0 * (matrix[k+1] - min_t) / (max_t - min_t)
        r, g, b = get_colour(value)
        daw_func(k, (r, g, b))

def draw_heatmap(matrix, daw_func):
    max_t, min_t, avg_t = matrix[:3]
    max_t += 0.1
    for k, temp in enumerate(matrix[3::]):
        value = 180.0 * (temp - min_t) / (max_t - min_t)
        
        # if (temp < -41 and temp > 301):
        #     value = 180.0 * (temp - min_t) / (max_t - min_t)
        # elif(temp>0):
        #     value = 180.0 * (matrix[k-1] - min_t) / (max_t - min_t)
        # else:
        #     value = 180.0 * (matrix[k+1] - min_t) / (max_t - min_t)
        r, g, b = get_colour(value)
        daw_func(k, (r, g, b))

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
