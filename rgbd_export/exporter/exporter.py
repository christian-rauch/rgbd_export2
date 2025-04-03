from typing import Optional, Union
import numpy.typing as npt
import abc


class Exporter(metaclass=abc.ABCMeta):
    def __init__(self, export_path: str):
        pass

    @abc.abstractmethod
    def write_rgbd(self,
                   colour: Union[npt.ArrayLike, bytes],
                   depth: Union[npt.ArrayLike, bytes],
                   width: int,
                   height: int,
                   K: npt.ArrayLike,
                   distortion_coefficients: list[float],
                   stamp: float,
                   T: Optional[npt.ArrayLike] = None,
                   ):
        pass
