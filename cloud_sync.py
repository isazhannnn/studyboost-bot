"""Cloud integrations are unavailable until a real OAuth flow is implemented.

Do not collect OAuth codes or access tokens through Telegram messages.
Legacy cloud_config.json is neither loaded nor written.
"""
from typing import Dict, Optional


class CloudSync:
    def connect_google_drive(self, user_id: int, auth_code: str) -> bool:
        return False

    def connect_dropbox(self, user_id: int, access_token: str) -> bool:
        return False

    def upload_to_google_drive(self, user_id: int, file_path: str,
                               folder_name: str = 'StudyBoost') -> Optional[str]:
        return None

    def upload_to_dropbox(self, user_id: int, file_path: str,
                         folder_path: str = '/StudyBoost') -> Optional[str]:
        return None

    def sync_notes(self, user_id: int, notes_data: Dict,
                   service: str = 'google_drive') -> bool:
        return False

    def is_connected(self, user_id: int, service: str = 'google_drive') -> bool:
        return False

    def disconnect(self, user_id: int, service: str = 'google_drive'):
        pass

    def get_connection_url(self, service: str = 'google_drive') -> str:
        return ''
