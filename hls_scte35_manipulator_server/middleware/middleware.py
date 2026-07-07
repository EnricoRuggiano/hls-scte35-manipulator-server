from threefive import Cue

from ..logger import logger
from ..patterns import find_hls_scte35_tag
from ..patterns import get_line_and_newline
from ..profiles import Profile

CUE_IN_TAG = "#EXT-X-CUE-IN"
CUE_OUT_TAG = "#EXT-X-CUE-OUT:"
CUE_OUT_CONT_TAG = "#EXT-X-CUE-OUT-CONT:"


def rewrite_manifest_if_needed(target_url: str, body: bytes, profile: Profile) -> bytes:
    text = body.decode("utf-8", errors="replace")
    if "#EXTM3U" not in text:
        return body

    out_lines = []
    has_been_manipulated = False
    is_filtered_oatcls_break = False
    is_overwrite_oatcls_break = False

    for raw_line in text.splitlines(keepends=True):
        line, newline = get_line_and_newline(raw_line)

        if is_filtered_oatcls_break:
            if line.startswith(CUE_OUT_TAG):
                logger.info("Removing cue-out while filtered break is active")
                has_been_manipulated = True
                continue
            if line.startswith(CUE_OUT_CONT_TAG):
                logger.info("Removing cue-out-cont while filtered break is active")
                has_been_manipulated = True
                continue
            if line.startswith(CUE_IN_TAG):
                logger.info("Removing cue-in that closes a filtered break")
                has_been_manipulated = True
                is_filtered_oatcls_break = False
                is_overwrite_oatcls_break = False
                continue

        if is_overwrite_oatcls_break:
            if line.startswith(CUE_IN_TAG):
                is_overwrite_oatcls_break = False
            elif line.startswith(CUE_OUT_CONT_TAG):
                parsed = find_hls_scte35_tag(line)
                if parsed:
                    payload, _tag_name, rebuild = parsed
                    try:
                        cue = Cue(payload)
                        cue.decode()
                        changed = profile.apply_overwrites(cue)
                        if changed:
                            original_line = line
                            line = rebuild(cue.encode())
                            logger.info(f"Overwriting input line {original_line} with {line}")
                            has_been_manipulated = True
                    except Exception:
                        logger.error(f"Failed to decode scte35 payload: {payload}")
                out_lines.append(f"{line}{newline}")
                continue

        parsed = find_hls_scte35_tag(line)
        if not parsed:
            out_lines.append(raw_line)
            logger.debug(f"Skipping line {raw_line}")
            continue

        payload, tag_name, rebuild = parsed
        try:
            cue = Cue(payload)
            cue.decode()
            logger.info(f"Detected SCTE35 payload in {target_url}: {cue.bites.hex()}")
        except Exception:
            out_lines.append(raw_line)
            logger.error(f"Failed to decode scte35 payload: {payload}")
            continue

        if profile.matches_filter(cue):
            logger.info(f"Removing {raw_line} because it matched filters from {profile.path}")
            has_been_manipulated = True
            if tag_name == "ext_oatcls_scte35":
                is_filtered_oatcls_break = True
                is_overwrite_oatcls_break = False
            continue

        changed = profile.apply_overwrites(cue)
        if changed:
            original_line = line
            line = rebuild(cue.encode())
            logger.info(f"Overwriting input line {original_line} with {line}")
            has_been_manipulated = True
            if tag_name == "ext_oatcls_scte35":
                is_overwrite_oatcls_break = True
        out_lines.append(f"{line}{newline}")

    out_lines_str = "".join(out_lines)
    out_lines_bytes = out_lines_str.encode("utf-8")

    if has_been_manipulated:
        logger.info(f"Rewriting {target_url} with content: {out_lines_str}")
    else:
        logger.info(f"Passthrough {target_url} with content: {out_lines_str}")
    return out_lines_bytes
