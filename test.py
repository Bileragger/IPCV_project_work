import cv2
import numpy as np
from matplotlib import pyplot as plt
import time
import statistics

file = '2022.png'
checkbin = []
in_river = []
out_river = []
old_checkbin = []
threshold_r = 30
threshold_g = 30
threshold_b = 30
ref_r = 0
ref_g = 0
ref_b = 0
ref_x = 500
ref_y = 0
radius = 10
threshold = 30
plot_scan = True
update_ref = False
distance_type = 'mahalanobis'

four_connected = [(-1, 0), (0, 1), (1, 0), (0, -1)]
eight_connected = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def calc_distance(center, radius):
    global distance_type
    if distance_type == 'spheric':
        calc_spheric_distance(center)
    if distance_type == 'mahalanobis':
        calc_mahalanobis_dist(center, radius)


def calc_spheric_distance(center):
    global ref_r, ref_g, ref_b
    global threshold_r, threshold_g, threshold_b

    ref_r = image_original[center[0], center[1], 0]
    ref_g = image_original[center[0], center[1], 1]
    ref_b = image_original[center[0], center[1], 2]

    threshold_r = threshold
    threshold_g = threshold
    threshold_b = threshold
    return


def calc_mahalanobis_dist(center, radius):
    global ref_r, ref_g, ref_b
    global threshold_r, threshold_g, threshold_b
    global threshold
    # get a neighbourhood of p of radius R
    neighbourhood = []
    x_width = list(range(center[0] - radius, center[0] + radius + 1))
    y_width = list(range(center[1] - radius, center[1] + radius + 1))
    for x in x_width:
        for y in y_width:
            p = (x, y)
            if 0 <= x < image_original.shape[0] and 0 <= y < image_original.shape[1]:
                neighbourhood.append(p)
    # separate the three channels
    R_vector = []
    G_vector = []
    B_vector = []
    for p in neighbourhood:
        R_vector.append(image_original[p[0], p[1], 0])
        G_vector.append(image_original[p[0], p[1], 1])
        B_vector.append(image_original[p[0], p[1], 2])
    # calculate the standard deviation for each vector
    r_mean = statistics.mean(R_vector)
    g_mean = statistics.mean(G_vector)
    b_mean = statistics.mean(B_vector)

    if radius > 0:
        r_stdev = statistics.stdev(R_vector)
        g_stdev = statistics.stdev(G_vector)
        b_stdev = statistics.stdev(B_vector)

        threshold_r = r_stdev * 3
        threshold_g = g_stdev * 3
        threshold_b = b_stdev * 3
    else:
        threshold_r = threshold
        threshold_g = threshold
        threshold_b = threshold

    # ref_r = r_mean
    # ref_g = g_mean
    # ref_b = b_mean

    ref_r = image_original[center[0], center[1], 0]
    ref_g = image_original[center[0], center[1], 1]
    ref_b = image_original[center[0], center[1], 2]

    return


def update_reference():
    global ref_x, ref_y
    global ref_r, ref_g, ref_b
    global radius

    sum_x = 0
    sum_y = 0
    for p in checkbin:
        sum_x = sum_x + p[0]
        sum_y = sum_y + p[1]
    baricentre = (sum_x / len(checkbin), sum_y / len(checkbin))
    reference = checkbin[0]
    reference_distance = abs(checkbin[0][0] - baricentre[0]) + abs(checkbin[0][1] - baricentre[1])
    for p in checkbin:
        distance = abs(p[0] - baricentre[0]) + abs(p[1] - baricentre[1])
        if distance < reference_distance:
            reference = p
            reference_distance = distance

    ref_x = reference[0]
    ref_y = reference[1]

    calc_distance((ref_x, ref_y), radius)

    return


def expand_checkbin():
    global checkbin
    global old_checkbin
    new_checkbin = []
    for position in checkbin:
        expansion = build_expansion(position, new_checkbin, four_connected)
        new_checkbin = new_checkbin + expansion

    old_checkbin = checkbin
    checkbin = new_checkbin


def build_expansion(position, new_checkbin, connection_type):
    x = position[0]
    y = position[1]
    expansion = []
    for p in connection_type:
        new_pos = verify_position((x + p[0], y + p[1]), new_checkbin)
        if new_pos is not None:
            expansion.append(new_pos)
    return expansion


def verify_position(position_to_check, new_checkbin):
    if position_to_check not in checkbin and position_to_check not in old_checkbin and position_to_check not in new_checkbin:
        if 0 <= position_to_check[0] < image_original.shape[0] and 0 <= position_to_check[1] < image_original.shape[1]:
            return position_to_check
    return None


def check():
    global old_checkbin
    global checkbin
    global in_river
    global out_river
    for p in checkbin:
        x = p[0]
        y = p[1]
        R = image_original[x, y, 0]
        G = image_original[x, y, 1]
        B = image_original[x, y, 2]
        dis_r = abs(int(R) - int(ref_r))
        dis_g = abs(int(G) - int(ref_g))
        dis_b = abs(int(B) - int(ref_b))
        if dis_r < threshold_r and dis_g < threshold_g and dis_b < threshold_b:
            min_dis = min([dis_r, dis_g, dis_b])
            m = statistics.mean([threshold_r, threshold_g, threshold_b])
            val = 255 * min_dis/m
            in_river.append(p)
            image_river[x, y] = (val, 0, val)
        else:
            out_river.append(p)

    checkbin = [x for x in checkbin if x not in out_river]
    return


image_original = cv2.imread(file, cv2.IMREAD_COLOR)
image_original = cv2.cvtColor(image_original, cv2.COLOR_BGR2RGB)
image_river = np.copy(image_original)

ref = (ref_x, ref_y)

checkbin.append(ref)

# calculate distance
calc_distance(ref, radius)
print("current reference colour: ({}, {}, {})".format(ref_r, ref_g, ref_b))

if plot_scan:
    plt.ion()
    fig = plt.figure()
    plt.imshow(image_original)

n = 0

while len(checkbin) > 0:
    n += 1
    expand_checkbin()
    check()
    print("iteration {}".format(n))
    if plot_scan is True and n % 200 == 0:
        for position in checkbin:
            plt.plot(position[1], position[0], marker='.', color="red", markersize=1)
        for position in out_river:
            plt.plot(position[1], position[0], marker='.', color="violet", markersize=1)
        plt.plot(ref_y, ref_x, marker='v', color="blue")
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(.1)
    if update_ref and n % 200 == 0:
        update_reference()
        # for p in checkbin:
        #     river_image[p[0],p[1]] = (0, 255, 0)
        # river_image[refX][refY] = (255, 0, 0)
        print("current reference colour: ({}, {}, {})".format(ref_r, ref_g, ref_b))

if plot_scan:
    plt.ioff()

print("plotting river image...")
plt.figure()
plt.imshow(image_river)
plt.show()