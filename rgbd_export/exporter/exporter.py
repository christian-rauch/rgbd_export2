from typing import Optional, Union
import numpy.typing as npt
import abc
from dataclasses import dataclass


@dataclass
class Intrinsics:
    width: int
    height: int
    K: npt.ArrayLike
    distortion_coefficients: list[float]


class Exporter(metaclass=abc.ABCMeta):
    def __init__(self, export_path: str):
        pass

    @abc.abstractmethod
    def write_rgbd(self,
                   colour: Union[npt.ArrayLike, bytes],
                   depth: Union[npt.ArrayLike, bytes],
                   intrinsics: Intrinsics,
                   stamp: float,
                   intrinsics_depth: Optional[Intrinsics] = None,
                   T: Optional[npt.ArrayLike] = None,
                   Tcd: Optional[npt.ArrayLike] = None,
                   ):
        pass
