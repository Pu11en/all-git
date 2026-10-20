from allgit.youtube import chunk_vtt

VTT = """WEBVTT

00:00:00.000 --> 00:00:20.000
first repo is
great

00:00:20.000 --> 00:00:45.000
and fast

00:00:45.000 --> 00:01:00.000
second repo
"""


def test_chunk_vtt_groups_cues_by_time():
    chunks = chunk_vtt(VTT)
    assert [c["chunk_index"] for c in chunks] == [0, 1]
    assert chunks[0] == {
        "chunk_index": 0,
        "start_ms": 0,
        "end_ms": 45000,
        "text": "first repo is great and fast",
    }
    assert chunks[1]["text"] == "second repo"


def test_chunk_vtt_empty():
    assert chunk_vtt("WEBVTT\n") == []
