"""
Unit test for stateless cookie-based credential application submissions.
Verifies that Agent 08 uses the passed in-memory credentials without contacting Agent 07 or database stores.
"""
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")

from agents import agent_08_application_submission

class TestStatelessApply(unittest.TestCase):
    @patch('agents.agent_07_credential_manager.get_credential')
    @patch('agents.agent_08_application_submission._is_working_hours', return_value=True)
    def test_stateless_batch_apply_no_db_access(self, mock_working_hours, mock_get_cred):
        # Mock get_credential to raise an exception if it is called
        mock_get_cred.side_effect = Exception("Should not call get_credential! Database/Session store should remain untouched.")

        # Mock jobs list
        jobs = [
            {
                "job_id": "job_wellfound_123",
                "title": "Python Developer",
                "company": "Test Wellfound Co",
                "apply_url": "https://wellfound.com/jobs/123",
                "apply_method": "wellfound",
                "recommendation": "strong_apply",
            },
            {
                "job_id": "job_linkedin_456",
                "title": "Backend Engineer",
                "company": "Test LinkedIn Co",
                "apply_url": "https://linkedin.com/jobs/view/456",
                "apply_method": "linkedin",
                "recommendation": "strong_apply",
            }
        ]

        # Credentials to pass in-memory
        credentials_payload = {
            "linkedin": {
                "username": "linkedin_user@example.com",
                "password": "linkedin_password"
            },
            "wellfound": {
                "username": "wellfound_user@example.com",
                "password": "wellfound_password",
                "oauth_token": "wellfound_oauth_token"
            }
        }

        # Mock application functions to prevent actual execution while asserting correct args are passed
        with patch('agents.agent_08_application_submission.apply_wellfound', return_value={"status": "SUCCESS"}) as mock_wellfound, \
             patch('agents.agent_08_application_submission.apply_linkedin_selenium', return_value={"status": "SUCCESS"}) as mock_linkedin:
            
            result = agent_08_application_submission.submit_batch(
                jobs=jobs,
                user_id="test_user_id",
                credentials=credentials_payload,
                daily_limit=2,
            )

            # Assertions
            self.assertEqual(result["status"], "success")
            
            # Verify credentials manager was NOT accessed
            mock_get_cred.assert_not_called()

            # Verify wellfound received the correct credentials
            mock_wellfound.assert_called_once()
            args, kwargs = mock_wellfound.call_args
            passed_cred = args[4] if len(args) > 4 else kwargs.get("cred")
            self.assertEqual(passed_cred, credentials_payload["wellfound"])

            # Verify linkedin received the correct credentials
            mock_linkedin.assert_called_once()
            args_li, kwargs_li = mock_linkedin.call_args
            passed_cred_li = args_li[4] if len(args_li) > 4 else kwargs_li.get("cred")
            self.assertEqual(passed_cred_li, credentials_payload["linkedin"])

            print("\n[SUCCESS] Stateless credentials application tests passed successfully!")

if __name__ == "__main__":
    unittest.main()
