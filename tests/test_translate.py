"""Tests for the pure translation helpers in batch_translate_queue."""

from __future__ import annotations

from hanhua_v3 import batch_translate_queue as btq


def test_protect_restore_tokens_roundtrip() -> None:
    text = '获得 %d 个 [font size = "12"]Item[/font]，%s'
    protected, tokens = btq.protect_tokens(text)
    assert "%d" not in protected or any("%d" in token for token in tokens)
    restored = btq.restore_tokens(protected, tokens)
    assert restored == text


def test_protect_tokens_empty() -> None:
    protected, tokens = btq.protect_tokens("纯中文文本")
    assert protected == "纯中文文本"
    assert tokens == []


def test_is_acceptable_batch_result_accepts_chinese() -> None:
    assert btq.is_acceptable_batch_result("账号创建成功")
    assert btq.is_acceptable_batch_result("剩余恢复量：%s")


def test_is_acceptable_batch_result_rejects_english_sentence() -> None:
    assert not btq.is_acceptable_batch_result("You cannot use this skill right now")


def test_translate_plain_exact_map() -> None:
    assert btq.translate_plain("Normal") == "普通"
    assert btq.translate_plain("Account Creation Successful") == "账号创建成功"


def test_translate_plain_preserves_outer_space() -> None:
    assert btq.translate_plain("Normal ") == "普通 "


def test_translate_plain_empty_passthrough() -> None:
    assert btq.translate_plain("") == ""
    assert btq.translate_plain("   ") == "   "


def test_internal_identifier_patterns() -> None:
    assert btq.INTERNAL_IDENTIFIER_RE.match("DST_STATUS_STAT_STR")
    assert btq.INTERNAL_IDENTIFIER_RE.match("Buff SK 12")
    assert btq.INTERNAL_IDENTIFIER_RE.match("MOB Makai3")
    assert not btq.INTERNAL_IDENTIFIER_RE.match("Normal Attack")
