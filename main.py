import pygame
import pygame_gui
import serial
import serial.tools.list_ports
import threading
import queue
import struct
from utils import *

pygame.init()
pygame.font.init()
pygame.mouse.set_visible(False)
FONT = pygame.font.Font(None, 25)  # 使用默认字体，大小为72
SERIAL = serial.Serial()
SERIAL.timeout = 2
IDENTIFY = queue.Queue(3)
IMG_BUFFER = None
IDENTIFY_BUFFER = b""
ALIVE = True
SCALE = 20
ERROR = None



class Serial_Manager():
    def __init__(self):
        self.ports = []
        self.names = []
    
    def scan_ports(self):
        options = serial.tools.list_ports.comports()
        ports = [i.device for i in options]
        names = [i.description for i in options]
        self.ports = ports
        self.names = names
        return ports, names

def get_serial_msg(port):
        if SERIAL.in_waiting:
            print(SERIAL.read())

class myUIDropDownMenu(pygame_gui.elements.UIDropDownMenu):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.listed = False 
        self.serial_manager = Serial_Manager()
        self.dic_ports = {}
    
    def process_event(self, event: pygame.event.Event):
        consumed_event = False
        if event.type == 32868:
            if event.ui_object_id in ["drop_down_menu.#expand_button", "drop_down_menu.#selected_option"]:
                if self.current_state != self.menu_states['expanded']:
                    self.update_ports()
                    print(self.dic_ports)

        if self.is_enabled:
            consumed_event = self.current_state.process_event(event)
        return consumed_event
    
    def set_disconnected(self):
        self.selected_option = self.options_list[0]

    def update_ports(self):
        self.dic_ports = {}
        ports, names = self.serial_manager.scan_ports()
        if self.selected_option[0] not in names:
            self.selected_option = self.options_list[0]
        
        for i in self.options_list:
            if i[0] not in ["断开连接"]:
                self.remove_options([i[0]])
        
        for port, name in zip(ports, names):
            self.dic_ports[name] = port
            self.add_options([name])

def thread_serial():
    global IDENTIFY_BUFFER, ALIVE, SERIAL, IMG_BUFFER, ERROR
    nums = []
    while ALIVE:
        if SERIAL.is_open:
            try:
                IDENTIFY_BUFFER = SERIAL.read_until(b"END")
                # IDENTIFY_BUFFER = SERIAL.read_all()
            except Exception as e:
                IDENTIFY_BUFFER = b""
                ERROR = e
            if b"BEGIN" in IDENTIFY_BUFFER and len(IDENTIFY_BUFFER) == 3092:
            # if b"BEGIN" in IDENTIFY_BUFFER:
                # print(IDENTIFY_BUFFER.index(b"BEGIN"), len(IDENTIFY_BUFFER))
                IMG_BUFFER = struct.unpack("<771f", IDENTIFY_BUFFER[5:-3])
                # IMG_BUFFER = struct.unpack("<3f", IDENTIFY_BUFFER[5:-3])
                # print(IMG_BUFFER)
            else:
                IMG_BUFFER = None

def draw_func(surf, k, color):
    y = k  // 32
    x = k  %  32
    pygame.draw.rect(surf, color, (x*SCALE, (23-y)*SCALE+50, SCALE, SCALE))

def render(surf, ):
    if IMG_BUFFER:
        draw_heatmap(IMG_BUFFER, lambda k, c: draw_func(surf, k, c))

def get_temp(pos):
    mx, my = pos
    x = mx//SCALE
    x = x if x < 31 else 31
    x = x if x > 0 else 0
    y = -(my-50)//SCALE+24
    y = y if y < 23 else 23
    y = y if y > 0 else 0
    k = y*32+x
    tmp = IMG_BUFFER[k+3] if IMG_BUFFER else None
    return x, y, k, tmp

def draw_temp_cross(surf:pygame.Surface, pos, temp):
    x, y = pos
    x_diff = 5 if x < 570 else -45
    y_diff = 5 if y < 500 else -15

    pygame.draw.line(surf, (255, 255, 255), (x-10, y), (x+10, y), 2)
    pygame.draw.line(surf, (255, 255, 255), (x, y-10), (x, y+10), 2)
    pygame.draw.line(surf, (0, 0, 0), (x-3, y), (x+3, y), 2)
    pygame.draw.line(surf, (0, 0, 0), (x, y-3), (x, y+3), 2)
    if 530 > y > 50 and x < 640:
        if isinstance(temp, float):
            text_surf = FONT.render(f"{temp:.2f}", True, (255, 255, 255), (0,0,0))
            surf.blit(text_surf, (x+x_diff, y+y_diff))
        # text_surf = FONT.render(f"{temp:.2f}℃", True, (255, 255, 255), (0,0,0))
        # surf.blit(text_surf, (x+50, y+50))


def main():
    global ALIVE, ERROR
    mouse_pos = (0,0)
    test_points = []
    pygame.display.set_caption('热成像监视器')
    window_surface = pygame.display.set_mode((640, 530), pygame.RESIZABLE)

    background = pygame.Surface((640, 530))
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager((640, 530))
    manager.set_locale('zh')
    # hello_list = pygame_gui.elements.UIDropDownMenu(["1","2","3"], "1", pygame.Rect((350, 275), (100, 50)),manager)
    port_list = myUIDropDownMenu(["断开连接"], "断开连接", 
                                 pygame.Rect((0, 0), (200, 50)),
                                 manager, 
                                 anchors={  'left': 'left',
                                            'top': 'top',}) 
    
    button_layout_rect = pygame.Rect((0, 0), (100, 50))
    button_layout_rect.topleft = (200, 0)
    button_save = pygame_gui.elements.UIButton(relative_rect=button_layout_rect, 
                                               text='保存温度帧', 
                                               manager=manager,
                                               anchors={    'left': 'left',
                                                            'top': 'top',})
    clock = pygame.time.Clock()
    is_running = True
    threading.Thread(target=thread_serial, daemon=True).start()

    while is_running:    
        time_delta = clock.tick(60)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
                ALIVE = False
            elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                test_points.clear()
                try:
                    if SERIAL.is_open:
                        SERIAL.close()
                    SERIAL.port = port_list.dic_ports[event.text]
                    SERIAL.baudrate = 921600
                    SERIAL.open()
                except Exception as e:
                    SERIAL.close()
                    port_list.set_disconnected()
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == button_save:
                    if IMG_BUFFER is not None:
                        save_frame(IMG_BUFFER, window_surface)

                    else:
                        ERROR = '未连接串口'
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if SERIAL.is_open:
                    if event.button == 1:
                        x, y = event.pos
                        if 530 > y > 50 and x < 640:
                            test_points.append(event.pos)
                    elif  event.button == 3:
                        if len(test_points) > 0:
                            test_points.pop()

            manager.process_events(event)

        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        
        render(window_surface)
        
        if ERROR is not None:
            SERIAL.close()
            port_list.set_disconnected()
            ERROR = None
       
        for i in test_points:
            draw_temp_cross(window_surface, i, get_temp(i)[-1])
        
        manager.draw_ui(window_surface)
        draw_temp_cross(window_surface, mouse_pos, get_temp(mouse_pos)[-1])
        if IMG_BUFFER:
            max_temp, min_temp, avg_temp = IMG_BUFFER[:3]
            pygame.display.set_caption(f'MAX: {max_temp:.2f}, MIN: {min_temp:.2f}, AVG: {avg_temp:.2f}')
        else:
            pygame.display.set_caption('热成像监视器')
        pygame.display.update()

if __name__ == '__main__':
    main()