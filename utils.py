
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

