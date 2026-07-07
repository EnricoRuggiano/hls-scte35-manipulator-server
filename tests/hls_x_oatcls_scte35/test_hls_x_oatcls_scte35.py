import pytest

from ..utils import hls_get_scte35
from ..utils import check
from ..utils import get_cue_in
from ..utils import get_cue_out
from threefive import Cue 

HLS_TAG="x_oatcls_scte35"

def test_x_oatcls_scte35_streamPlaylist_splice_filter(appargs):
    path    = f"06_{HLS_TAG}_streamPlaylist_splice_filter.txt"
    profile = "profile-splice-filter.json"
    text:str = check(appargs, profile, path) 

    ### validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    cue_in         = get_cue_in(text)
    cue_out        = get_cue_out(text)

    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    splice       = list(filter(lambda x: x.command.command_type == 5, cues))    
    assert len(time_signals) == len(cues)
    assert len(splice) == 0
    assert cue_in == 1
    assert cue_out == 1

def test_x_oatcls_scte35_streamPlaylist_timesignal_filter(appargs):
    path    = f"07_{HLS_TAG}_streamPlaylist_timesignal_filter.txt"
    profile = "profile-timesignal-filter.json"
    text:str = check(appargs, profile, path) 

    ### validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    cue_in         = get_cue_in(text)
    cue_out        = get_cue_out(text)

    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    splice       = list(filter(lambda x: x.command.command_type == 5, cues))    
    assert len(time_signals) == 0
    assert len(splice) == len(cues)
    assert cue_in == 1
    assert cue_out == 1

def test_x_oatcls_scte35_streamPlaylist_convert_ads_to_break(appargs):
    path    = f"08_{HLS_TAG}_streamPlaylist_convert_ads_to_break.txt"
    profile = "profile-convert-ads-to-break.json"
    text:str = check(appargs, profile, path) 

    ### validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    cue_in         = get_cue_in(text)
    cue_out        = get_cue_out(text)

    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    breaks       = list(filter(lambda x: any([desc.segmentation_type_id == 34 or desc.segmentation_type_id == 35 for desc in x.descriptors]), time_signals))
    ads          = list(filter(lambda x: any([desc.segmentation_type_id == 48 or desc.segmentation_type_id == 49 for desc in x.descriptors]), time_signals))
    assert len(time_signals) == len(cues)
    assert len(breaks) == len(cues)
    assert len(ads) == 0
    assert cue_in == 1
    assert cue_out == 1


def test_x_oatcls_scte35_streamPlaylist_convert_break_to_ads(appargs):
    path    = f"09_{HLS_TAG}_streamPlaylist_convert_break_to_ads.txt"
    profile = "profile-convert-break-to-ads.json"
    text:str = check(appargs, profile, path) 

    ### validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    cue_in         = get_cue_in(text)
    cue_out        = get_cue_out(text)
    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    breaks       = list(filter(lambda x: any([desc.segmentation_type_id == 34 or desc.segmentation_type_id == 35 for desc in x.descriptors]), time_signals))
    ads          = list(filter(lambda x: any([desc.segmentation_type_id == 48 or desc.segmentation_type_id == 49 for desc in x.descriptors]), time_signals))    
    assert len(time_signals) == len(cues)
    assert len(breaks) == 0
    assert len(ads) == len(cues)
    assert cue_in == 1
    assert cue_out == 1

def test_x_oatcls_scte35_streamPlaylist_ads_and_break_descriptor(appargs):
    path    = f"10_{HLS_TAG}_streamPlaylist_descriptor_ads_filter.txt"
    profile = "profile-descriptor-ads-filter.json"
    text:str = check(appargs, profile, path) 

    ## validate text manifest
    ### validate text manifest
    cues:list[Cue] = hls_get_scte35(text)
    cue_in         = get_cue_in(text)
    cue_out        = get_cue_out(text)
    time_signals = list(filter(lambda x: x.command.command_type == 6, cues))
    breaks       = list(filter(lambda x: any([desc.segmentation_type_id == 34 or desc.segmentation_type_id == 35 for desc in x.descriptors]), time_signals))
    ads          = list(filter(lambda x: any([desc.segmentation_type_id == 48 or desc.segmentation_type_id == 49 for desc in x.descriptors]), time_signals))    
    assert len(time_signals) == len(cues)
    assert len(breaks) == len(cues)
    assert len(ads) == 0
    assert cue_in == 1
    assert cue_out == 1

    for _cue in cues:
        assert len(_cue.descriptors) == 1
