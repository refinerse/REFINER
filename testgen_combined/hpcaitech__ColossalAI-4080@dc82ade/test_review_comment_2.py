import re

import pytest


def test_ppo_trainer_uses_dataloader_next_not_next_iter():
    """
    The review fix replaced the incorrect pattern:
        next(iter(self.prompt_dataloader))
    with:
        self.prompt_dataloader.next()

    This test asserts the fixed pattern is present and the old pattern is absent.
    """
    source = open("/workspace/applications/Chat/coati/trainer/ppo.py", "r", encoding="utf-8").read()

    # Old (buggy) pattern: recreates a new iterator each call, always returns first batch
    old_prompt = "next(iter(self.prompt_dataloader))"
    old_pretrain = "next(iter(self.pretrain_dataloader))"

    # New (fixed) pattern: relies on dataloader wrapper providing .next() that advances
    new_prompt = "self.prompt_dataloader.next()"
    new_pretrain = "self.pretrain_dataloader.next()"

    assert new_prompt in source, (
        "Expected PPOTrainer to sample prompts using 'self.prompt_dataloader.next()' "
        "to advance through the dataloader, but it was not found."
    )
    assert new_pretrain in source, (
        "Expected PPOTrainer to sample pretrain batches using 'self.pretrain_dataloader.next()' "
        "to advance through the dataloader, but it was not found."
    )

    assert old_prompt not in source, (
        "Found the old buggy pattern 'next(iter(self.prompt_dataloader))' which re-initializes "
        "the iterator each time and can repeatedly return the first batch."
    )
    assert old_pretrain not in source, (
        "Found the old buggy pattern 'next(iter(self.pretrain_dataloader))' which re-initializes "
        "the iterator each time and can repeatedly return the first batch."
    )