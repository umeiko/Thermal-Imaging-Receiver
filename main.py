import pygame
import pygame_gui
import serial
import serial.tools.list_ports
import threading
import queue
import struct
from utils import *
import cmaprgb

pygame.init()
pygame.font.init()
pygame.mouse.set_visible(False)
FONT = pygame.font.Font(None, 25)  # 使用默认字体，大小为72
SERIAL = serial.Serial()
SERIAL.timeout = 2
IDENTIFY = queue.Queue(3)
DATA_BUFFER = None
REC = False
IDENTIFY_BUFFER = b""
ALIVE = True
SCALE = 20
REC_INTERVAL = 0.25
MAX_REC_TIME = 3600 * 5

ERROR = None
DISPLAY_MODE = "SCALED"
SURF_IMG = pygame.Surface((32*SCALE, 24*SCALE))
REC_LAST_TIME = time.time()
TIME_REC_LIST = []
POINTS_REC_LIST = []
REC_BEGIN_TIME = time.time()
LAST_FLAG_SEND = time.time()
LOCK = threading.Lock()
ORIG_SURF = pygame.Surface((32, 32))
PIX_ARRAY = pygame.PixelArray(ORIG_SURF)
CMAP_IDX = 0
CMAP_STR_DICT = {
    "经典":0,"明亮":1,"红热":2,"翠绿":3,"暗紫":4,"白热":5,"黑热":6
}


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
    global IDENTIFY_BUFFER, ALIVE, SERIAL, DATA_BUFFER, ERROR, LAST_FLAG_SEND
    while ALIVE:
        if SERIAL.is_open:
            current_time = time.time()
            if current_time - LAST_FLAG_SEND >= 0.5:
                SERIAL.write(b"stream\n")
                LAST_FLAG_SEND = current_time
                time.sleep(0.1)
            if SERIAL.is_open:
                LOCK.acquire()
                try:
                    IDENTIFY_BUFFER = SERIAL.read_until(b"END")
                except Exception as e:
                    IDENTIFY_BUFFER = b""
                    ERROR = e
                if b"BEGIN" in IDENTIFY_BUFFER and len(IDENTIFY_BUFFER) == 2060:
                    DATA_BUFFER = struct.unpack("<1026H", IDENTIFY_BUFFER[5: -3])
                else:
                    DATA_BUFFER = None
                LOCK.release()
            else:
                ...


def render():
    if DATA_BUFFER:
        draw_buffer = list(DATA_BUFFER)
        if DISPLAY_MODE == "ORIGINAL":
            surf = pygame.Surface((640, 640))
            t_max, t_min = draw_buffer[0], draw_buffer[1]
            idx = 2
            for i in range(32):
                for j in range(32):
                    value = int(180 * (draw_buffer[idx] - t_min) / (t_max - t_min))
                    if value > 179: 
                        value = 179
                    elif value < 0:
                        value = 0
                    pygame.draw.rect(surf, cmaprgb.CMAPS[CMAP_IDX][value], pygame.Rect(i*20, j*20, 20, 20))
                    idx += 1
            surf = pygame.transform.rotate(surf, 90.)
        else:
            surf = pygame.Surface((640, 640))
            t_max, t_min = draw_buffer[0], draw_buffer[1]
            idx = 2
            for i in range(32):
                for j in range(32):
                    value = int(180 * (draw_buffer[idx] - t_min) / (t_max - t_min))
                    if value > 179: 
                        value = 179
                    elif value < 0:
                        value = 0
                    PIX_ARRAY[i, j] = cmaprgb.CMAPS[CMAP_IDX][value]
                    idx += 1
            surf = pygame.transform.smoothscale(PIX_ARRAY.make_surface(), (640, 640))
            surf = pygame.transform.rotate(surf, 90.)
        return surf

def get_temp(pos):
    mx, my = pos
    x = mx//SCALE
    x = x if x < 31 else 31
    x = x if x > 0 else 0
    y = -(my-50) // SCALE+31
    y = y if y < 31 else 31
    y = y if y > 0 else 0
    k = y*32+x
    tmp = DATA_BUFFER[k+2] if DATA_BUFFER else None
    if tmp is not None:
        tmp = tmp / 10 - 273.15
    return x, y, k, tmp

def draw_temp_cross(surf:pygame.Surface, pos, temp):
    x, y = pos
    x_diff = 5 if x < 570 else -45
    y_diff = 5 if y < 500 else -15

    pygame.draw.line(surf, (255, 255, 255), (x-10, y), (x+10, y), 2)
    pygame.draw.line(surf, (255, 255, 255), (x, y-10), (x, y+10), 2)
    pygame.draw.line(surf, (0, 0, 0), (x-3, y), (x+3, y), 2)
    pygame.draw.line(surf, (0, 0, 0), (x, y-3), (x, y+3), 2)
    if 690 > y > 50 and x < 640:
        if isinstance(temp, float):
            text_surf = FONT.render(f"{temp:.2f}", True, (255, 255, 255), (0,0,0))
            surf.blit(text_surf, (x+x_diff, y+y_diff))

def change_mode():
    global DISPLAY_MODE
    DISPLAY_MODE = "SCALED" if DISPLAY_MODE == "ORIGINAL" else "ORIGINAL"


def rec_trigger():
    global REC, TIME_REC_LIST, POINTS_REC_LIST, REC_BEGIN_TIME
    if not SERIAL.is_open:
        return None
    if not REC:
        REC = True
        REC_BEGIN_TIME = time.time()
    else:
        REC = False
        save_curv(TIME_REC_LIST, POINTS_REC_LIST)
        TIME_REC_LIST = []
        POINTS_REC_LIST = []

def rec_loop(temps:list):
    global REC, TIME_REC_LIST, POINTS_REC_LIST, REC_LAST_TIME
    if REC:
        now = time.time()
        if now - REC_LAST_TIME > REC_INTERVAL:
            TIME_REC_LIST.append(now - REC_BEGIN_TIME)
            REC_LAST_TIME = now
        # for temp in temps:
            POINTS_REC_LIST.append(temps.copy())
            

def main():
    global ALIVE, ERROR, CMAP_IDX
    mouse_pos = (0,0)
    test_points = []
    test_temps = []
    msg = "热成像监视器"
    window_surface = pygame.display.set_mode((640, 690), pygame.RESIZABLE)
    max_temp, min_temp = 0, 0
    background = pygame.Surface((640, 690))
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager((640, 690))
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
    
    button_layout_rect4 = pygame.Rect((0, 0), (100, 50))
    button_layout_rect4.topleft = (300, 0)

    cmap_list = pygame_gui.elements.UIDropDownMenu(["经典","明亮","红热","翠绿","暗紫","白热","黑热"], "经典", 
                                 button_layout_rect4,
                                 manager, 
                                 anchors={  'left': 'left',
                                            'top': 'top',}) 
    
    button_layout_rect2 = pygame.Rect((0, 0), (150, 50))
    button_layout_rect2.topright = (0, 0)
    button_scale = pygame_gui.elements.UIButton(relative_rect=button_layout_rect2, 
                                            text='双线性插值：开', 
                                            manager=manager,
                                            anchors={    'right': 'right',
                                                        'top': 'top',})
    button_layout_rect3 = pygame.Rect((0, 0), (80, 50))
    button_layout_rect3.topright = (-150, 0)
    button_rec = pygame_gui.elements.UIButton(relative_rect=button_layout_rect3, 
                                            text='录制曲线', 
                                            manager=manager,
                                            anchors={   'right': 'right',
                                                        'top': 'top',})
    clock = pygame.time.Clock()
    is_running = True
    threading.Thread(target=thread_serial, daemon=True).start()

    while is_running:
        test_temps.clear()
        time_delta = clock.tick(60)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
                ALIVE = False
                rec_trigger()
            elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == port_list:
                    test_points.clear()
                    try:
                        if SERIAL.is_open:
                            SERIAL.close()
                        SERIAL.port = port_list.dic_ports[event.text]
                        SERIAL.baudrate = 921600
                        SERIAL.open()
                        SERIAL.write(b"stream\n")
                        msg = ""
                    except Exception as e:
                        SERIAL.close()
                        port_list.set_disconnected()
                        msg = str(e)
                elif event.ui_element == cmap_list:
                    print(event.text)
                    CMAP_IDX = CMAP_STR_DICT[event.text]

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == button_save:
                    if DATA_BUFFER is not None:
                        save_frame(DATA_BUFFER, window_surface)
                    else:
                        ERROR = '未连接串口'
                elif event.ui_element == button_scale:
                    change_mode()
                    if DISPLAY_MODE == "SCALED":
                        button_scale.set_text('双线性插值：开')
                    else:
                        button_scale.set_text('双线性插值：关')
                elif event.ui_element == button_rec:
                    if len(test_points) == 0:
                        msg = '请先选择测温点'
                    else:
                        rec_trigger()
                        if REC:
                            button_rec.set_text('结束录制')
                            msg = '曲线录制中'
                        else:
                            button_rec.set_text('录制曲线')
                            msg = '录制完成'
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if SERIAL.is_open and not REC:
                    if event.button == 1:
                        x, y = event.pos
                        if 530 > y > 50 and x < 640:
                            test_points.append(event.pos)
                    elif  event.button == 3:
                        if len(test_points) > 0:
                            test_points.pop()
                elif not SERIAL.is_open:
                    msg = '未连接串口'
                elif REC:
                    msg = '曲线录制中,结束后可添加测温点'
            manager.process_events(event)

        manager.update(time_delta)
        if SERIAL.is_open:
            pygame.draw.rect(window_surface, (0, 0, 0), (0, 0, 640, 50))
        else:
            window_surface.blit(background, (0, 0))
        
        if DATA_BUFFER is not None:
            window_surface.blit(render(), (0, 50))
 
        draw_temp_cross(window_surface, mouse_pos, get_temp(mouse_pos)[-1])
        if ERROR is not None:
            SERIAL.close()
            port_list.set_disconnected()
            msg = str(ERROR)
            ERROR = None
            if REC:  # 关闭未结束的曲线录制
                rec_trigger()
        
        if DATA_BUFFER:
            max_temp, min_temp = DATA_BUFFER[0] / 10 - 273.15, DATA_BUFFER[1] / 10 - 273.15
            pygame.display.set_caption(f'MAX: {max_temp:.2f}, MIN: {min_temp:.2f}, k: {get_temp(mouse_pos)[-2]} {msg}')
        else:
            pygame.display.set_caption(msg)
        
        test_temps.append(max_temp)
        for i in test_points:
            temp = get_temp(i)[-1]
            draw_temp_cross(window_surface, i, temp)
            test_temps.append(temp)

        rec_loop(test_temps)
        manager.draw_ui(window_surface)
        draw_temp_cross(window_surface, mouse_pos, get_temp(mouse_pos)[-1])
        draw_temp_cross(window_surface, mouse_pos, get_temp(mouse_pos)[-1])

        pygame.display.update()

if __name__ == '__main__':
    main()
