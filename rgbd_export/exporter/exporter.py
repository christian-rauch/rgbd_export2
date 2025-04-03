from typing import Optional
import numpy.typing as npt
import abc


class Exporter(metaclass=abc.ABCMeta):
    def __init__(self, export_path: str):
        pass

    @abc.abstractmethod
    def write_rgbd(self,
                   colour: npt.ArrayLike,
                   depth: npt.ArrayLike,
                   K: npt.ArrayLike,
                   distortion_coefficients: list[float],
                   stamp: float,
                   T: Optional[npt.ArrayLike] = None,
                   ):
        pass
