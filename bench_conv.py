import itertools
import sys
import time

import mlx.core as mx


def timeit(fn, *args):
    for _ in range(5):
        mx.eval(fn(*args))

    tic = time.time()
    for _ in range(100):
        mx.eval(fn(*args))
    toc = time.time()
    ms = 10 * (toc - tic)
    return ms


N = [1, 4, 8, 16, 32, 64]
HW = [9, 18, 36, 72]
C = [16, 32, 64, 64, 128, 256]

if len(sys.argv) > 1:
    times = []
    for n, hw, c in itertools.product(N, HW, C):
        image = mx.random.uniform(shape=(n, hw, hw, c))
        weight = mx.random.uniform(shape=(c, 3, 3, c))

        def fun(image):
            for _ in range(5):
                image = mx.conv2d(image, weight, padding=1, stride=1)
            return image

        times.append(str(timeit(fun, image)))
    print(",".join(times))
    exit(0)

import os
import subprocess

import matplotlib.pyplot as plt
import numpy as np

env = os.environ
env["MLX_USE_WINOGRAD_CONV"] = "1"
winograd = subprocess.run(
    ["python", "bench_conv.py", "-b"], env=env, capture_output=True
)
winograd = [float(t) for t in winograd.stdout.decode().split(",")]
env["MLX_USE_WINOGRAD_CONV"] = "0"
no_winograd = subprocess.run(
    ["python", "bench_conv.py", "-b"], env=env, capture_output=True
)
no_winograd = [float(t) for t in no_winograd.stdout.decode().split(",")]

k = 0
for n in N:
    res_mat = np.zeros((len(HW), len(C)))
    for i in range(len(HW)):
        for j in range(len(C)):
            res_mat[i, j] = winograd[k] / no_winograd[k]
            k += 1
    ax = plt.gca()
    p = ax.imshow(res_mat, cmap="RdBu")
    ax.set_xticks(list(range(len(C))))
    ax.set_yticks(list(range(len(HW))))
    ax.set_xticklabels(C)
    ax.set_yticklabels(HW)
    plt.gcf().colorbar(p, ax=ax)

    plt.title("Conv 2D: (Time Winograd / Time No Winograd)")
    plt.xlabel("Channels In/Out")
    plt.ylabel("Height/Width")
    plt.savefig(f"winograd_vs_no_batch{n}.png")
