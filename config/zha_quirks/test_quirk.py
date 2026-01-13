'''
Author: Jiyon viysyu@gmail.com
Date: 2026-01-13 21:03:09
LastEditors: Jiyon viysyu@gmail.com
LastEditTime: 2026-01-13 21:07:20
FilePath: \homeassistant\config\zha_quirks\test_quirk.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.warning("🔥 ZHA QUIRK FILE IMPORTED: config/zha_quirks/test_quirk.py was loaded")

from zigpy.quirks import CustomDevice
from zigpy.zcl.clusters.general import Basic, Identify

_LOGGER = logging.getLogger(__name__)


class TestQuirkDevice(CustomDevice):
    """Simple test quirk device for verifying custom_quirks_path."""

    # ⚠️ signature 用来“匹配设备”
    signature = {
        "models_info": [
            # 这里写一个几乎“随便什么设备都能匹配到”的占位符
            ("TEST_MANUFACTURER", "TEST_MODEL"),
        ],
        "endpoints": {
            1: {
                "profile_id": 0x0104,  # ZHA Profile
                "device_type": 0x0000,
                "input_clusters": [
                    Basic.cluster_id,
                    Identify.cluster_id,
                ],
                "output_clusters": [],
            }
        },
    }

    # ⚠️ replacement 描述“我打算怎么替换”
    replacement = {
        "endpoints": {
            1: {
                "profile_id": 0x0104,
                "device_type": 0x0000,
                "input_clusters": [
                    Basic.cluster_id,
                    Identify.cluster_id,
                ],
                "output_clusters": [],
            }
        }
    }

    def __init__(self, *args, **kwargs):
        _LOGGER.warning(
            "🔥 ZHA TEST QUIRK LOADED: TestQuirkDevice has been initialized!"
        )
        super().__init__(*args, **kwargs)
