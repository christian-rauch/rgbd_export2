import numpy.typing as npt
import numpy as np
from geometry_msgs.msg import Pose
from scipy.spatial.transform import Rotation

def pose_to_matrix(pose: Pose) -> npt.ArrayLike:
    T = np.eye(4)
    T[:3, 3] = np.array([pose.position.x, pose.position.y, pose.position.z])
    T[:3, :3] = Rotation.from_quat([
        pose.orientation.x,
        pose.orientation.y,
        pose.orientation.z,
        pose.orientation.w,
    ]).as_matrix()
    return T
