import unittest

from os_mfa.clouds_configs import create_token_config


class TestCreateLongTermConfig(unittest.TestCase):
    def setUp(self):
        self.config = {
            "auth": {
                "auth_url": "https://api.nz-hlz-1.catalystcloud.io:5000",
                "project_id": "1238a098c1273d409812409812",
                "project_name": "john-doe",
                "user_domain_name": "Default",
                "username": "john.doe@example.com",
                "token": "thisisnotatallwhatatokenlookslike",
            },
            "auth_type": "password",
            "identity_api_version": 3,
            "interface": "public",
            "region_name": "nz-hlz-1",
        }

    def test_password_not_in_long_term_config(self):
        token = "not a real_token"
        token_config = create_token_config(self.config, token)
        self.assertFalse("password" in token_config["auth"])
        self.assertFalse("user_domain_name" in token_config["auth"])
        self.assertFalse("username" in token_config["auth"])
        self.assertEqual(token_config["auth_type"], "token")
        self.assertEqual(token_config["auth"]["token"], token)


if __name__ == "__main__":
    unittest.main()
