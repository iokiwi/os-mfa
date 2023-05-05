import unittest

from os_mfa.clouds_configs import create_long_term_config


class TestCreateLongTermConfig(unittest.TestCase):
    def setUp(self):
        self.config = {
            "auth": {
                "auth_url": "https://api.nz-hlz-1.catalystcloud.io:5000",
                "project_id": "1238a098c1273d409812409812",
                "project_name": "john-doe",
                "user_domain_name": "Default",
                "username": "john.doe@example.com",
                "password": "notaverygoodpassword123",
                "token": "thisisnotatallwhatatokenlookslike",
            },
            "auth_type": "password",
            "identity_api_version": 3,
            "interface": "public",
            "region_name": "nz-hlz-1",
        }

    def test_create_long_term_config(self):
        long_term_config = create_long_term_config(self.config)
        self.assertFalse("password" in long_term_config["auth"])
        self.assertFalse("token" in long_term_config["auth"])
        self.assertFalse("auth_type" in long_term_config)


if __name__ == "__main__":
    unittest.main()
