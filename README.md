# RGBD exporter for ROS 2 bag files

## Usage

The script takes a bag file and topic names for colour, depth, camera info and optional a topic for the camera pose. It supports different export formats:
- ICL: https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html

```sh
ros2 run rgbd_export exporter
  ${BAG_FILE} \
  -c /camera/color/image_raw/compressed \
  -d /camera/depth/image_raw/compressed \
  -i /camera/color/camera_info \
  -p /camera_pose \
  -f ICL \
  -e ${EXPORT_FOLDER}
```
