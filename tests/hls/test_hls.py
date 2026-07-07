import pytest

from ..utils import check_generic
from ..utils import health

def test_health(appargs):
    assert health(appargs, 'profile.json').status_code == 200

def test_master(appargs):
    path    = f"00_master.txt"
    profile = "profile"
    assert check_generic(appargs, profile, path, 'master-playlist').status_code == 200
    
def test_chunk(appargs):
    path    = f"00_chunk.txt"
    profile = "profile"
    assert check_generic(appargs, profile, path, 'chunk').status_code == 200

def test_stream_playlist(appargs):
    path    = f"00_streamPlaylist.txt"
    profile = "profile"
    assert check_generic(appargs, profile, path).status_code == 200
