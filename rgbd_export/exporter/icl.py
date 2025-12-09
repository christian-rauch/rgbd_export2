from typing import Optional, Union
import numpy.typing as npt

import os
import numpy as np
import imageio.v3 as iio
from datetime import datetime
import yaml
import filetype

from .exporter import Exporter, Intrinsics


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
        # create relative symlinks from "images" and "input" to "rgb" for compatibility
        # with COLMAP for Gaussian Splatting and LangSplat data readers
        os.symlink(self.folder_colour, os.path.join(self.path, "images"))
        os.symlink(self.folder_colour, os.path.join(self.path, "input"))

        self.f_poses = open(os.path.join(self.path, "poses.gt.sim"), 'w', encoding="utf-8")

    @staticmethod
    def params_from_intrinsics(intrinsics: Intrinsics):
        camera_params = dict()
        camera_params['image_height'] = intrinsics.height
        camera_params['image_width'] = intrinsics.width
        camera_params['fx'] = float(intrinsics.K[0, 0])
        camera_params['fy'] = float(intrinsics.K[1, 1])
        camera_params['cx'] = float(intrinsics.K[0, 2])
        camera_params['cy'] = float(intrinsics.K[1, 2])
        camera_params['png_depth_scale'] = 1000

        # OpenCV convention
        k1 = intrinsics.distortion_coefficients[0]
        k2 = intrinsics.distortion_coefficients[1]
        k3 = intrinsics.distortion_coefficients[4]
        p1 = intrinsics.distortion_coefficients[2]
        p2 = intrinsics.distortion_coefficients[3]
        camera_params['distortion'] = [k1, k2, p1, p2, k3]

        return camera_params

    def write_rgbd(self,
                   colour: Union[npt.ArrayLike, bytes],
                   depth: Union[npt.ArrayLike, bytes],
                   intrinsics: Intrinsics,
                   stamp: float,
                   intrinsics_depth: Optional[Intrinsics] = None,
                   T: Optional[npt.ArrayLike] = None,
                   ):
        stamp_str = datetime.fromtimestamp(stamp).strftime("%Y%m%d_%H%M%S_%f") + f"_{self.i}"
        fpath_colour = os.path.join(self.path_colour, f"frame_{stamp_str}.{{ext}}")
        fpath_depth = os.path.join(self.path_depth, f"{stamp_str}.{{ext}}")

        if type(colour) is bytes:
            fmt_colour = filetype.guess_extension(colour)
            if fmt_colour is None:
                raise RuntimeError("Cannot determine image format for colour data!")
            with open(fpath_colour.format(ext=fmt_colour), 'wb') as f:
                f.write(colour)
        elif type(colour) is np.ndarray:
            iio.imwrite(fpath_colour.format(ext="jpg"), colour)

        if type(depth) is bytes:
            fmt_depth = filetype.guess_extension(depth)
            if fmt_depth is None:
                raise RuntimeError("Cannot determine image format for depth data!")
            with open(fpath_depth.format(ext=fmt_depth), 'wb') as f:
                f.write(depth)
        elif type(depth) is np.ndarray:
            iio.imwrite(fpath_depth.format(ext="png"), depth)

        if self.i == 0:
            metadata = {
                'dataset_name': "icl",
                'camera_params': ICLExporter.params_from_intrinsics(intrinsics),
            }
            if intrinsics_depth is not None:
                metadata['camera_params_depth'] = ICLExporter.params_from_intrinsics(intrinsics_depth)

            with open(os.path.join(self.path, "icl.yaml"), 'w', encoding="utf-8") as f:
                yaml.dump(metadata, f)

        if T is not None:
            self.f_poses.write(f"{T[0][0]:f} {T[0][1]:f} {T[0][2]:f} {T[0][3]:f}\n")
            self.f_poses.write(f"{T[1][0]:f} {T[1][1]:f} {T[1][2]:f} {T[1][3]:f}\n")
            self.f_poses.write(f"{T[2][0]:f} {T[2][1]:f} {T[2][2]:f} {T[2][3]:f}\n")
            self.f_poses.write("\n")

        self.i += 1
