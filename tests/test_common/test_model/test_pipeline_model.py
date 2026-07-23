"""
Tests for pipeline_model PipelineProcessResult.
"""

from maize.common.model.pipeline_model import PipelineProcessResult


class TestPipelineProcessResult:
    """Test PipelineProcessResult."""

    def test_default_values(self):
        result = PipelineProcessResult()
        assert result.success_count == 0
        assert result.fail_count == 0

    def test_add_merges_counts(self):
        a = PipelineProcessResult(success_count=5, fail_count=2)
        b = PipelineProcessResult(success_count=3, fail_count=1)
        a.add(b)
        assert a.success_count == 8
        assert a.fail_count == 3

    def test_add_zero_result(self):
        a = PipelineProcessResult(success_count=10, fail_count=4)
        b = PipelineProcessResult()
        a.add(b)
        assert a.success_count == 10
        assert a.fail_count == 4

    def test_add_to_zero(self):
        a = PipelineProcessResult()
        b = PipelineProcessResult(success_count=7, fail_count=3)
        a.add(b)
        assert a.success_count == 7
        assert a.fail_count == 3

    def test_add_does_not_modify_other(self):
        """add() should not mutate the argument."""
        a = PipelineProcessResult(success_count=1, fail_count=1)
        b = PipelineProcessResult(success_count=2, fail_count=2)
        a.add(b)
        assert b.success_count == 2
        assert b.fail_count == 2

    def test_multiple_add(self):
        a = PipelineProcessResult(success_count=1, fail_count=0)
        b = PipelineProcessResult(success_count=2, fail_count=1)
        c = PipelineProcessResult(success_count=3, fail_count=2)
        a.add(b)
        a.add(c)
        assert a.success_count == 6
        assert a.fail_count == 3
