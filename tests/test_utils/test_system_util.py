"""
Tests for system_util.
"""

from unittest.mock import MagicMock, mock_open, patch

from maize.utils.system_util import get_container_id


class TestGetContainerId:
    """Test get_container_id."""

    def test_returns_none_when_mountinfo_absent(self):
        with patch("maize.utils.system_util.Path.exists", return_value=False):
            assert get_container_id() is None

    def test_returns_none_when_no_resolv_conf_line(self):
        lines = [
            "1 2 3 / /some/other/file\n",
            "4 5 6 / /another/file\n",
        ]
        with (
            patch("maize.utils.system_util.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="".join(lines))),
        ):
            assert get_container_id() is None

    def test_returns_container_id_from_resolv_conf_line(self):
        """A line containing /resolv.conf should yield the container id segment.

        Logic: text before "/resolv.conf" split by "/", last element is the id.
        """
        lines = [
            "100 99 98:0 /docker/containers/abc123def/resolv.conf /etc/resolv.conf rw - tmpfs tmpfs\n",
        ]
        with (
            patch("maize.utils.system_util.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="".join(lines))),
        ):
            result = get_container_id()
        assert result == "abc123def"

    def test_returns_first_matching_container_id(self):
        """When multiple lines match, the first container id is returned."""
        lines = [
            "100 99 98:0 /docker/containers/first_id/resolv.conf /etc/resolv.conf rw - tmpfs tmpfs\n",
            "101 98 98:0 /docker/containers/second_id/resolv.conf /etc/resolv.conf rw - tmpfs tmpfs\n",
        ]
        with (
            patch("maize.utils.system_util.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="".join(lines))),
        ):
            result = get_container_id()
        assert result == "first_id"

    def test_returns_none_when_resolv_conf_line_has_empty_container_id(self):
        """A matching line whose container id segment is empty returns None."""
        lines = [
            "100 99 98:0 /resolv.conf /etc/resolv.conf rw - tmpfs tmpfs\n",
        ]
        m = MagicMock()
        m.readlines.return_value = lines
        with (
            patch("maize.utils.system_util.Path.exists", return_value=True),
            patch("builtins.open", return_value=m),
        ):
            assert get_container_id() is None
