import os
import time
import pygame


def save_frame(matrix:list, surf:pygame.Surface):
    lines = []
    line = []
    for k, data in enumerate(matrix[2::]):
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
    
    cap_rect = pygame.Rect(0, 50, 20*32, 20*32)
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


if __name__ == "__main__":
    pass