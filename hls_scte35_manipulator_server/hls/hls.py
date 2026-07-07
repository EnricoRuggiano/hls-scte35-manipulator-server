from fastapi import Request

# paths
def is_manifest_path(path:str) -> bool:
    return path.lower().endswith(".m3u8")

def is_segment_path(path:str) -> bool:
    return path.lower().endswith(".ts")

# requests
def is_segment_content(request:Request) -> bool:
    content_type = request.headers.get("content-type", "")    
    return "mp2t" in content_type.lower()

def is_manifest_content(request:Request) -> bool:
    content_type = request.headers.get("content-type", "")
    return "mpegurl" in content_type.lower() 

# content of the manifest
def is_manifest_text(text:str) -> bool:
    return "#EXTM3U" in text

def is_manifest_playlist(lines:list[str]) -> bool:
    return any(line.strip().startswith("#EXTINF:") for line in lines)

# line inside manifest
def is_segment_line(text:str) -> bool:
    stripped = text.strip()
    return bool(stripped and not stripped.startswith("#"))
