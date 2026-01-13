import logging

from zigpy.quirks import CustomDevice
from zigpy.zcl.clusters.general import Basic, Identify

_LOGGER = logging.getLogger(__name__)


class SonoffTestQuirk(CustomDevice):
    """
    Minimal and safe ZHA quirk for testing.
    Does NOT modify any behavior.
    """

    signature = {
        "models_info": [
            # 你给的厂商是 sonoff，model 随便起一个测试用
            ("sonoff", "TEST_MODEL_ID"),
        ],
        "endpoints": {
            1: {
                "profile_id": 0x0104,  # Home Automation
                "device_type": 0x0000,
                "input_clusters": [
                    Basic.cluster_id,
                    Identify.cluster_id,
                ],
                "output_clusters": [],
            }
        },
    }

    # replacement 保持与 signature 一致，确保零副作用
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
            "✅ SonoffTestQuirk loaded for device: %s",
            self.signature["models_info"][0],
        )
        super().__init__(*args, **kwargs)
