import re
from typing import Any
from ..logger import logger

EXT_OATCLS = re.compile(r"^(#EXT-OATCLS-SCTE35:)([^\s]+)(\s*)$")
EXT_SPLICEPOINT = re.compile(r"^(#EXT-X-SPLICEPOINT-SCTE35:)([^\s]+)(\s*)$")
EXT_X_SCTE35 = re.compile(r'^(#EXT-X-SCTE35:.*?CUE=")([^"]+)(".*)$')
EXT_X_CUE_OUT_CONT = re.compile(r'^(#EXT-X-CUE-OUT-CONT:.*?SCTE35="?)([^",\s]+)("?.*)$')


def _canonical_tag(prefix: str) -> str:
    if prefix.startswith("#EXT-OATCLS-SCTE35"):
        return "ext_oatcls_scte35"
    if prefix.startswith("#EXT-X-SPLICEPOINT-SCTE35"):
        return "ext_x_splicepoint_scte35"
    if prefix.startswith("#EXT-X-SCTE35"):
        return "ext_x_scte35"
    if prefix.startswith("#EXT-X-CUE-OUT-CONT"):
        return "ext_x_cue_out_cont"
    return "unknown"


def find_hls_scte35_tag(line: str) -> tuple[str, str, Any] | None:
    for pattern in (EXT_OATCLS, EXT_SPLICEPOINT, EXT_X_SCTE35, EXT_X_CUE_OUT_CONT):
        match = pattern.match(line.rstrip("\r\n"))
        if not match:
            continue

        prefix = match.group(1)
        payload = match.group(2)
        suffix = match.group(3)
        logger.info(f"Detected SCTE35 HLS TAG in line: {line}")

        def _rebuild(new_payload: str, p: str = prefix, s: str = suffix) -> str:
            return f"{p}{new_payload}{s}"

        return payload, _canonical_tag(prefix), _rebuild
    return None
