# HLS SCTE35 Manipulator Server

HLS manifest proxy that manipulates SCTE-35 tags depending on specific json profile

## Installation

```
make build install
hls-scte35-manipulator-server --help
```

Also Docker Image is available [lalalaciccio/hls-scte35-manipulator-server](https://hub.docker.com/r/lalalaciccio/hls-scte35-manipulator-server)

## How it works

- Start an http server that will listen to PUT request at port 4999
- Forward the received PUT request at port 4999 to the origin server with IP 127.0.0.1 to the port 80
- Manipulates any detected SCTE35 Payload in hls tags of the `streamPlaylist.m3u8` received at port 4999 according the manipulation rules specified in the `profile.json`   

```
hls-scte35-manipulator-server --origin-base-url 127.0.0.1:80 --profile profiles/profile.json --host 0.0.0.0 --port 4999 --log-level INFO
```


## Supported HLS tags
- #EXT-OATCLS-SCTE35
- #EXT-X-SPLICEPOINT-SCTE35
- #EXT-X-SCTE35
- #EXT-X-CUE-OUT-CONT


## HLS SCTE35 Manipulation Profiles

`profile.json` supports two rules:
- `filters`: filters out scte35 payload if a condition is met
- `overwrites`: list of rules to apply a overwrite value if a condition is met


### Examples

1] Remove `splice_insert` SCTE35 commands
```
{
  "filters": [
    {
      "match": {
        "path": "command.command_type",
        "op": "eq",
        "value": 5
      }
    }
  ],
  "overwrites": []
}  
```

2] Change `segmentation_type_id` in the incoming `time_signals` from `Provider Advertisement Start`, `Provider Advertisement End` to `Break Start`, `Break End`
```
{
  "filters": [],
  "overwrites": [
    {
      "op": "update",
      "path": "descriptors[].segmentation_type_id",
      "where": {
        "path": "segmentation_type_id",
        "op": "eq",
        "value": 48
      },
      "value": 34
    },
    {
      "op": "update",
      "path": "descriptors[].segmentation_type_id",
      "where": {
        "path": "segmentation_type_id",
        "op": "eq",
        "value": 49
      },
      "value": 35
    }
  ]
}
```

For further examples check `/hls_scte35_manipulator_server/profiles` json files.  


## Examples of StreamPlaylists supported

Validation of SCTE35 payload manipulation has been done using the following __examples__ of StreamPlaylist.

For further examples check `/tests/streamPlaylist/` or run
```
make build install-dev tests
```


__EXT-X-SPLICEPOINT-SCTE35__
```
#EXTM3U
#EXT-X-TARGETDURATION:12
#EXT-X-MEDIA-SEQUENCE:178280911
#EXT-X-VERSION:3
#EXT-X-PROGRAM-DATE-TIME:2026-06-30T08:31:40.866Z
#EXTINF:3,
20260629T102246/ts/89140/sequence_178280918.ts
#EXT-X-SPLICEPOINT-SCTE35:/DA4AAAAAAAAAP/wBQb/rBnY4wAiAiBDVUVJcfQUJ3/fAACCdnAODDEzM180NDUxNzI5NTABAV2omD0=
#EXTINF:9,
20260629T102246/ts/89140/sequence_178280919.ts
#EXT-X-SPLICEPOINT-SCTE35:/DA4AAAAAAAAAP/wBQb/rJxPUwAiAiBDVUVJcfQUJ3/fAAAAAAAADDEzM180NDUxNzI5NTEBAeVV2XI=
#EXTINF:2,
20260629T102246/ts/89140/sequence_178280929.ts
#EXTINF:8,
20260629T102246/ts/89140/sequence_178280930.ts
#EXT-X-SPLICEPOINT-SCTE35:/DA2AAAAAAAAAP/wBQb/rKoK8wAgAh5DVUVJO5rKAX/fAAAAAAAACjEwMDAwMDAwMDExAQF+ZAsM
#EXTINF:4,
20260629T102246/ts/89140/sequence_178280931.ts
```

__#EXT-OATCLS-SCTE35__
```
#EXTM3U
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:297024192
#EXT-X-VERSION:3
#EXT-X-KEY:METHOD=NONE
#EXT-X-PROGRAM-DATE-TIME:2026-06-22T13:24:36.523Z
#EXTINF:5,
20260608T132502/ts/148512/sequence_297024197.ts
#EXT-OATCLS-SCTE35:/DA4AAAAAAAAAP/wBQb/rBnY4wAiAiBDVUVJcfQUJ3/fAACCdnAODDEzM180NDUxNzI5NTABAV2omD0=
#EXT-X-CUE-OUT:117.040
#EXT-X-PROGRAM-DATE-TIME:2026-06-22T13:25:12.323Z
#EXTINF:7,
20260608T132502/ts/148512/sequence_297024198.ts
#EXT-X-CUE-OUT-CONT:ElapsedTime=7.000,Duration=117.040,SCTE35=/DA4AAAAAAAAAP/wBQb/rBnY4wAiAiBDVUVJcfQUJ3/fAACCdnAODDEzM180NDUxNzI5NTABAV2omD0=
#EXT-X-PROGRAM-DATE-TIME:2026-06-22T13:25:18.523Z
#EXTINF:6,
20260608T132502/ts/148512/sequence_297024199.ts
#EXT-X-CUE-OUT-CONT:ElapsedTime=13.000,Duration=117.040,SCTE35=/DA4AAAAAAAAAP/wBQb/rBnY4wAiAiBDVUVJcfQUJ3/fAACCdnAODDEzM180NDUxNzI5NTABAV2omD0=
#EXT-X-PROGRAM-DATE-TIME:2026-06-22T13:25:24.523Z
#EXTINF:6,
20260608T132502/ts/148512/sequence_297024200.ts
#EXT-X-CUE-OUT-CONT:ElapsedTime=19.000,Duration=117.040,SCTE35=/DA4AAAAAAAAAP/wBQb/rBnY4wAiAiBDVUVJcfQUJ3/fAACCdnAODDEzM180NDUxNzI5NTABAV2omD0=
#EXT-X-PROGRAM-DATE-TIME:2026-06-22T13:25:30.523Z
#EXT-X-CUE-IN
```

