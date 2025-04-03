from typing import Optional
import numpy.typing as npt

import os
import imageio.v3 as iio
from datetime import datetime
import yaml

from .exporter import Exporter


class ICLExporter(Exporter):
    def __init__(self, export_path: str):
        self.path = export_path
        self.i = 0

        # create folder layout
        self.folder_colour = "rgb"
        self.folder_depth = "depth"
        self.path_colour = os.path.join(self.path, self.folder_colour)
        self.path_depth = os.path.join(self.path, self.folder_depth)

        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
        else:
            raise RuntimeError(f"Path '{self.path}' exists already!")

        os.makedirs(self.path_colour, exist_ok=True)
        os.makedirs(self.path_depth, exist_ok=True)

        self.f_poses = open(os.path.join(self.path, "poses.gt.sim"), 'w', encoding="utf-8")

    def write_rgbd(self,
                   colour: npt.ArrayLike,
                   depth: npt.ArrayLike,
                   K: npt.ArrayLike,
                   distortion_coefficients: list[float],
                   stamp: float,
                   T: Optional[npt.ArrayLike] = None,
                   ):
        stamp_str = datetime.fromtimestamp(stamp).strftime("%Y%m%d_%H%M%S_%f") + f"_{self.i}"
        iio.imwrite(os.path.join(self.path_colour, f"frame_{stamp_str}.jpg"), colour)
        iio.imwrite(os.path.join(self.path_depth, f"{stamp_str}.png"), depth)

        if self.i == 0:
            camera_params = dict()
            camera_params['image_height'] = colour.shape[0]
            camera_params['image_width'] = colour.shape[1]
            camera_params['fx'] = float(K[0, 0])
            camera_params['fy'] = float(K[1, 1])
            camera_params['cx'] = float(K[0, 2])
            camera_params['cy'] = float(K[1, 2])
            camera_params['png_depth_scale'] = 1000

            # OpenCV convention
            k1 = distortion_coefficients[0]
            k2 = distortion_coefficients[1]
            k3 = distortion_coefficients[4]
            p1 = distortion_coefficients[2]
            p2 = distortion_coefficients[3]
            camera_params['distortion'] = [k1, k2, p1, p2, k3]

            with open(os.path.join(self.path, "icl.yaml"), 'w', encoding="utf-8") as f:
                yaml.dump({'dataset_name': "icl", 'camera_params': camera_params}, f)

        if T is not None:
            self.f_poses.write(f"{T[0][0]:f} {T[0][1]:f} {T[0][2]:f} {T[0][3]:f}\n")
            self.f_poses.write(f"{T[1][0]:f} {T[1][1]:f} {T[1][2]:f} {T[1][3]:f}\n")
            self.f_poses.write(f"{T[2][0]:f} {T[2][1]:f} {T[2][2]:f} {T[2][3]:f}\n")
            self.f_poses.write("\n")

        self.i += 1
