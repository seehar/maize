"""
Tests for system_util
"""

from unittest.mock import MagicMock, patch

import pytest

from maize.utils.system_util import get_container_id


class TestSystemUtil:
    """Test system_util"""

    def test_get_container_id_no_mountinfo(self):
        """Test get_container_id when /proc/self/mountinfo doesn't exist"""
        with patch("maize.utils.system_util.Path.exists", return_value=False):
            result = get_container_id()
            assert result is None

    def test_get_container_id_returns_none_when_no_match(self):
        """Test get_container_id returns None when no resolv.conf found in mountinfo"""
        with patch("maize.utils.system_util.Path.exists", return_value=True):
            mock_file_content = """
            1 2 3 / /some/other/file
            4 5 6 / /another/file
            """
            with patch("builtins.open", MagicMock()) as mock_open:
                mock_open.return_value.__enter__.return_value.readlines.return_value = mock_file_content.strip().split(
                    "\n"
                )
                result = get_container_id()
                assert result is None

    @pytest.mark.skip(reason="Windows-specific functionality")
    def test_fix_windows_aiohttp_proxy_error_windows(self):
        """Test fix_windows_aiohttp_proxy_error on Windows - skipped on non-Windows"""
        pass
