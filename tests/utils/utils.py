import os
from hls_scte35_manipulator_server import load_profile
from hls_scte35_manipulator_server import Profile
from hls_scte35_manipulator_server import create_app
import posixpath
from threefive import Cue
from fastapi import Response
from fastapi.testclient import TestClient

def health(appargs, profile:str) -> Response:
    appargs['profile_path'] = manipulator_profile(profile).path
    app = TestClient(create_app(**appargs))
    return app.get('/health')

def check_generic(appargs, profile:str, path:str, path_type='stream-playlist') -> Response:
    appargs['profile_path'] = manipulator_profile(profile).path
    app = TestClient(create_app(**appargs))
    content = streamPlaylist(path)
    url = streamPlaylistUrl()
    if path_type == 'master-playlist':
        url = masterPlaylistUrl()
    elif path_type == 'chunk':
        url = chunkUrl()        
    return app.put(url=url, content=content)

def check(appargs, profile:str, path:str) -> str:
    appargs['profile_path'] = manipulator_profile(profile).path
    app = TestClient(create_app(**appargs))
    content = streamPlaylist(path)
    response:Response = app.put(url=streamPlaylistUrl(), content=content)
    text:str = response.content.decode('utf-8')
    return text

def manipulator_profile(profile_name:str) -> Profile :
    profile_path = os.path.join('hls_scte35_manipulator_server', "profiles", profile_name)
    return load_profile(profile_path)

def streamPlaylist(streamPlaylist_name:str) -> str :
    stream_playlist_path = os.path.join('tests', 'streamPlaylists', streamPlaylist_name)
    content = ""
    with open(stream_playlist_path) as f:
        content = f.read()
    return content

def masterPlaylistUrl(masterPlaylist:str='master.m3u8') -> str:
    return posixpath.join('channel', masterPlaylist)

def streamPlaylistUrl(streamPlaylist_name:str='streamPlaylist.m3u8') -> str:
    return posixpath.join('channel', 'stream01', streamPlaylist_name)

def chunkUrl(chunkUrl:str='chunk.ts') -> str:
    return posixpath.join('channel', 'stream01', chunkUrl)

def hls_get_scte35(content:str) -> list[Cue]:
    cues = []
    hls_time = duration = cue_out = cue_in = 0
    lines = content.splitlines()
    last_line = lines[:-1]
    for l in lines:
        if not l:
            break
        # if l.startswith("#EXT-X-CUE-OUT:"):
        #     cue_out = hls_time
        #     duration = float(l.split(":")[1])
        #     cue_in = hls_time + duration
        #     print(f"hls time: {hls_time}")
        #     print(f"cue out: {cue_out}")
        #     print(f"duration: {duration}")
        #     print(f"cue in: {cue_in}")
       
        # ##EXTINF:4.000000,
        # if l.startswith("#EXTINF:"):
        #     t = l.split(":")[1].split(",")[0]
        #     t = float(t)
        #     hls_time += t
        #     next_line = manifest.readline()[:-1]
        #     if not (next_line.startswith("#")):
        #         print(f"Segment: {next_line} @ {hls_time}")

        # EXT-X-SCTE35:CUE=
        if l.startswith("#EXT-X-SCTE35"):
            mesg = l.split("CUE=")[1]
            cues.append(Cue(mesg))

        if l.startswith("#EXT-OATCLS-SCTE35:"):
            mesg = l.split("#EXT-OATCLS-SCTE35:")[1]
            cues.append(Cue(mesg))

        if l.startswith("#EXT-X-CUE-OUT-CONT:"):
            chunks = l.split(",")
            _last = chunks[-1]
            if _last.startswith("SCTE35="):
                mesg = _last.split("SCTE35=")[-1]
                cues.append(Cue(mesg))

        ##EXT-X-DATERANGE:ID="splice-6FFFFFF0",START-DATE="2014-03-05T11:15:00Z",PLANNED-DURATION=59.993,SCTE35-OUT=0xFC002F0000000000FF000014056FFFFFF000E011622DCAFF000052636200000000000A000829896F50000008700000000
        if l.startswith("#EXT-X-DATERANGE:"):
            for chunk in l.split(","):
                k, v = chunk.split("=")
                if k.startswith("SCTE35"):
                    cue = Cue(v)
                    cues.append(Cue(mesg))
        #EXT-X-SPLICEPOINT-SCTE35:/DA4AAAAAAAAAP/wBQb/rBnY4wAiAiBDVUVJcfQUJ3/fAACCdnAODDEzM180NDUxNzI5NTABAV2omD0=
        if l.startswith("#EXT-X-SPLICEPOINT-SCTE35:"):
            mesg = l.split("#EXT-X-SPLICEPOINT-SCTE35:")[1]
            cues.append(Cue(mesg))
    return cues

def get_cue_out(content:str) -> int:
    lines = content.splitlines()
    num_cue = 0
    for l in lines:
        if l.startswith("#EXT-X-CUE-OUT:"):
            num_cue += 1
    return num_cue

def get_cue_in(content:str) -> int:
    lines = content.splitlines()
    num_cue = 0
    for l in lines:
        if l.startswith("#EXT-X-CUE-IN"):
            num_cue += 1
    return num_cue
