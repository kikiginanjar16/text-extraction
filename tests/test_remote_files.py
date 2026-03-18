import socket
import unittest
from unittest.mock import patch

from app.core.errors import InvalidRequestError
from app.services.storage.temp_files import validate_remote_url


class RemoteUrlValidationTest(unittest.TestCase):
    @patch("app.services.storage.temp_files.socket.getaddrinfo")
    def test_rejects_private_ip_targets(self, getaddrinfo) -> None:
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]
        with self.assertRaises(InvalidRequestError):
            validate_remote_url("http://localhost/file.txt")

    @patch("app.services.storage.temp_files.socket.getaddrinfo")
    def test_accepts_public_http_url(self, getaddrinfo) -> None:
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        ]
        parsed = validate_remote_url("https://example.com/report.pdf")
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "example.com")


if __name__ == "__main__":
    unittest.main()
