#!/usr/bin/python3
from typing import Union, Optional
import argparse
import rosbag2_py
from rosidl_runtime_py.utilities import get_message
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import Image, CompressedImage, CameraInfo
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import numpy as np

from .bag_time_synchronizer import BagTimeSynchronizer
from .conversion import pose_to_matrix
from .exporter.icl import ICLExporter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bagpath", type=str,
                        help="path to bag file")
    parser.add_argument('-c', '--topic_colour', type=str,
                        help="colour image topic")
    parser.add_argument('-d', '--topic_depth', type=str,
                        help="depth image topic")
    parser.add_argument('-i', '--topic_info', type=str,
                        help="camera info topic")
    parser.add_argument("-p", "--topic_pose", type=str,
                        help="camera pose topic")
    parser.add_argument("-f", "--format", type=str,
                        choices=["ICL"],
                        required=True,
                        help="export format")
    parser.add_argument("-e", "--export", type=str,
                        required=True,
                        help="path to exported data")
    parser.add_argument('-r', '--range', type=float, nargs=2,
                        help="time range in seconds since start of bag file")
    parser.add_argument('--sync_queue_size', type=int, default=100,
                        help="queue size for synchronizer")
    parser.add_argument('--sync_slop', type=float, default=0.016,
                        help="slop for synchronizer")
    args = parser.parse_args()

    global exporter
    if args.format == "ICL":
        exporter = ICLExporter(export_path = args.export)
    else:
        raise ValueError(f"unknown export format '{args.format}'")

    global bridge
    bridge = CvBridge()

    reader = rosbag2_py.SequentialReader()
    reader.open_uri(args.bagpath)

    # index all message types
    topic_types = {}
    for topic in reader.get_all_topics_and_types():
        try:
            message = get_message(topic.type)
        except ModuleNotFoundError:
            # ignoring unknown message types
            pass
        else:
            topic_types[topic.name] = message

    # check for valid topics
    topics = [
        args.topic_colour,
        args.topic_depth,
        args.topic_info,
    ]

    if args.topic_pose is not None:
        topics.append(args.topic_pose)

    for topic in topics:
        if topic not in topic_types:
            print("available topics:")
            for tname, ttype in topic_types.items():
                print(f"  {tname} ({ttype.__module__}.{ttype.__name__})")
            raise ValueError(f"topic '{topic}' not found in bag file")

    # filter topics of interest
    reader.set_filter(rosbag2_py.StorageFilter(topics=topics))

    sync = BagTimeSynchronizer(topics, args.sync_queue_size, args.sync_slop)
    sync.registerCallback(on_sync)

    stamp_start = None
    while reader.has_next():
        topic, data, stamp_ns = reader.read_next()

        # normalise time stamps
        stamp = stamp_ns / 1e9
        if stamp_start is None:
            stamp_start = stamp
        nstamp = stamp - stamp_start

        # seek to start
        if (args.range is not None) and (nstamp < args.range[0]):
            reader.seek(stamp_ns + int(args.range[0]*1e9))

        # early return
        if (args.range is not None) and (nstamp > args.range[1]):
            break

        # add message to synchronisation queue
        msg = deserialize_message(data, topic_types[topic])
        sync.add_msg(msg, topic)

    # call the destructor to flush data
    del exporter

def on_sync(
        msg_colour: Union[Image, CompressedImage],
        msg_depth: Union[Image, CompressedImage],
        msg_info: CameraInfo,
        msg_pose: Optional[PoseStamped] = None,
    ):
    assert msg_colour.header.frame_id == msg_depth.header.frame_id == msg_info.header.frame_id

    if type(msg_colour) == Image:
        img_colour = bridge.imgmsg_to_cv2(msg_colour, desired_encoding="rgb8")
    elif type(msg_colour) == CompressedImage:
        img_colour = bridge.compressed_imgmsg_to_cv2(msg_colour, desired_encoding="rgb8")
    else:
        raise TypeError(f"unknown colour image type {type(msg_colour)}")

    if type(msg_depth) == Image:
        img_depth = bridge.imgmsg_to_cv2(msg_depth)
    elif type(msg_depth) == CompressedImage:
        img_depth = bridge.compressed_imgmsg_to_cv2(msg_depth)
    else:
        raise TypeError(f"unknown depth image type {type(msg_colour)}")

    # intrinsic matrix
    K = msg_info.k.reshape(3, 3)

    # extrinsic matrix
    Twc = pose_to_matrix(msg_pose.pose) if msg_pose is not None else None

    assert img_colour.shape[:2] == img_depth.shape[:2]

    assert img_depth.dtype == np.uint16

    exporter.write_rgbd(
        img_colour,
        img_depth,
        K,
        msg_info.d,
        msg_colour.header.stamp.sec + msg_colour.header.stamp.nanosec * 1e-9,
        Twc,
    )

if __name__ == '__main__':
    main()
