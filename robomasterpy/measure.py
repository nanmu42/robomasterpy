# -*- coding: utf-8 -*-


# ██████╗  ██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ ██████╗ ██╗   ██╗
# ██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝
# ██████╔╝██║   ██║██████╔╝██║   ██║██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝██████╔╝ ╚████╔╝
# ██╔══██╗██║   ██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗██╔═══╝   ╚██╔╝
# ██║  ██║╚██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║██║        ██║
# ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝        ╚═╝


import math
from typing import Tuple

FOCAL_LENGTH_HD: float = 710
HORIZONTAL_DEGREES: float = 96
HORIZONTAL_PIXELS: float = 1280
VERTICAL_DEGREES: float = 54
VERTICAL_PIXELS: float = 720

INFANTRY_LENGTH: float = 0.32
INFANTRY_WIDTH: float = 0.24
INFANTRY_HEIGHT: float = 0.27

ENGINEERING_LENGTH: float = 0.41
ENGINEERING_WIDTH: float = 0.24
ENGINEERING_HEIGHT: float = 0.33


def pinhole_distance(actual_size: float, pixel_size: float, focal_length: float = FOCAL_LENGTH_HD) -> float:
    """
    使用针孔相机模型估测物体到相机的距离。

    Estimate distance between camera and object using pinhole camera model.

    :param actual_size: 实际大小，单位米。 Actual object size in meters.
    :param pixel_size: 像素大小，单位像素。 Object size in pixels.
    :param focal_length: （可选）当前分辨率下的等效焦距，和分辨率相关。默认使用1280*720分辨率下的数值。Perceived focal length at specified image resolution, default to value under 1280*720.
    :return: 物体到相机的距离，单位米。 Distance between camera and object, in meters.
    """
    return focal_length * actual_size / pixel_size


def distance_decomposition(pixel_x: float, distance: float, horizontal_pixels: float = HORIZONTAL_PIXELS, horizontal_degrees: float = HORIZONTAL_DEGREES) -> Tuple[float, float, float]:
    """
    将距离分解为前进分量（前为正）和侧向分量（右为正）。本函数要求线段的两端在相同海拔高度。

    Decomposition distance into forward vector(forward as positive) and lateral vector(right as positive).
    This function requires that both ends of the line segment are at the same altitude.

    :param pixel_x: 物体在图像上的x坐标，单位像素。 the x coordinate of the object on the image, in pixels.
    :param distance: 距离，单位米。 Distance in meter.
    :param horizontal_pixels: 图像横向的像素数目，默认1280. The number of pixels in the horizontal direction of the image, the default is 1280.
    :param horizontal_degrees: 图像横向的视角大小，默认96. The horizontal viewing angle of the image, the default is 96.
    :return: 前进分量和侧向分量，单位米；水平偏转角度，单位度。 forward vector and lateral vector in meters; horizontal angle in degrees.
    """
    horizontal_degree = horizontal_degrees * (pixel_x / horizontal_pixels - 0.5)
    rad = horizontal_degree / 180 * math.pi
    lateral = distance * math.sin(rad)
    forward = distance * math.cos(rad)
    return forward, lateral, horizontal_degree
