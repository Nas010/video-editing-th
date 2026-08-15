from video_editing_th.config import EditingProfile
from video_editing_th.models import Transcript, TranscriptSegment, TranscriptWord
from video_editing_th.retakes import find_retake_groups, text_similarity


def make_transcript(texts: list[str]) -> Transcript:
    words = []
    segments = []
    for index, text in enumerate(texts):
        start = index * 3.0
        end = start + 2.0
        words.append(TranscriptWord(text=text, start=start, end=end))
        segments.append(
            TranscriptSegment(
                id=f"s{index}",
                start=start,
                end=end,
                text=text,
                word_indices=[index],
            )
        )
    return Transcript(
        media_sha256="a" * 64,
        language="th",
        backend="test",
        model="test",
        words=words,
        segments=segments,
    )


def profile() -> EditingProfile:
    return EditingProfile.model_validate(
        {
            "name": "test",
            "version": 1,
            "language": "th",
            "retakes": {
                "maximum_gap_seconds": 12,
                "similarity_threshold": 0.62,
                "prefer_latest_complete": True,
                "preserve_uncertain": True,
            },
        }
    )


def test_thai_character_similarity_handles_small_rewording() -> None:
    score = text_similarity(
        "วันนี้เราจะพูดเรื่องการกินโปรตีน",
        "วันนี้เรามาพูดเรื่องการกินโปรตีนกันครับ",
    )

    assert score > 0.65


def test_find_retake_groups_recommends_latest_complete_candidate() -> None:
    transcript = make_transcript(
        [
            "วันนี้เราจะพูดเรื่องการกินโปรตีน เอ่อ",
            "วันนี้เราจะพูดเรื่องการกินโปรตีน",
            "วันนี้เรามาพูดเรื่องการกินโปรตีนกันครับ",
            "ต่อไปเป็นเรื่องการนอนหลับ",
        ]
    )

    groups = find_retake_groups(transcript, profile())

    assert len(groups) == 1
    assert [candidate.segment_ids for candidate in groups[0].candidates] == [
        ["s0"],
        ["s1"],
        ["s2"],
    ]
    assert groups[0].recommended_candidate_id == groups[0].candidates[-1].id
    assert groups[0].requires_review is True


def test_unrelated_segments_are_not_grouped() -> None:
    transcript = make_transcript(
        ["กินโปรตีนให้เพียงพอ", "การนอนหลับสำคัญ", "วันนี้อากาศดีมาก"]
    )

    assert find_retake_groups(transcript, profile()) == []
