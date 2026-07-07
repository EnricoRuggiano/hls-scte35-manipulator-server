import pytest

from ..utils import hls_get_scte35
from ..utils import check
from threefive import Cue 

HLS_TAG="x_splicepoint"

def test_x_splicepoint_streamPlaylist_splice_filter(appargs):
    path    = f"01_{HLS_TAG}_streamPlaylist_splice_filter.txt"
    profile = "profile-splice-filter.json"
    text:str = check(appargs, profile, path) 

    ## validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    splice       = list(filter(lambda x: x.command.command_type == 5, cues))
    assert len(time_signals) == 3
    assert len(splice) == 0

def test_x_splicepoint_streamPlaylist_timesignal_filter(appargs):
    path    = f"02_{HLS_TAG}_streamPlaylist_timesignal_filter.txt"
    profile = "profile-timesignal-filter.json"
    text:str = check(appargs, profile, path) 

    ## validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    splice       = list(filter(lambda x: x.command.command_type == 5, cues))
    assert len(time_signals) == 0
    assert len(splice) == 2


def test_x_splicepoint_streamPlaylist_convert_ads_to_break(appargs):
    path    = f"03_{HLS_TAG}_streamPlaylist_convert_ads_to_break.txt"
    profile = "profile-convert-ads-to-break.json"
    text:str = check(appargs, profile, path) 

    ## validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    breaks       = list(filter(lambda x: any([desc.segmentation_type_id == 34 or desc.segmentation_type_id == 35 for desc in x.descriptors]), time_signals))
    ads          = list(filter(lambda x: any([desc.segmentation_type_id == 48 or desc.segmentation_type_id == 49 for desc in x.descriptors]), time_signals))
    
    assert len(breaks) == 3
    assert len(ads) == 0

def test_x_splicepoint_streamPlaylist_convert_break_to_ads(appargs):
    path    = f"04_{HLS_TAG}_streamPlaylist_convert_break_to_ads.txt"
    profile = "profile-convert-break-to-ads.json"
    text:str = check(appargs, profile, path) 

    ## validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    breaks       = list(filter(lambda x: any([desc.segmentation_type_id == 34 or desc.segmentation_type_id == 35 for desc in x.descriptors]), time_signals))
    ads          = list(filter(lambda x: any([desc.segmentation_type_id == 48 or desc.segmentation_type_id == 49 for desc in x.descriptors]), time_signals))
    
    assert len(breaks) == 0
    assert len(ads) == 3

def test_x_splicepoint_streamPlaylist_ads_and_break_descriptor(appargs):
    path    = f"05_{HLS_TAG}_streamPlaylist_descriptor_ads_filter.txt"
    profile = "profile-descriptor-ads-filter.json"
    text:str = check(appargs, profile, path) 

    ## validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    breaks       = list(filter(lambda x: any([desc.segmentation_type_id == 34 or desc.segmentation_type_id == 35 for desc in x.descriptors]), time_signals))
    ads          = list(filter(lambda x: any([desc.segmentation_type_id == 48 or desc.segmentation_type_id == 49 for desc in x.descriptors]), time_signals))
    
    assert len(ads) == 0
    assert len(breaks) == len(cues)
    for _cue in cues:
        assert len(_cue.descriptors) == 1
