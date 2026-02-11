from typing import Optional, Dict
import json
import os


class CloudSync:
    def __init__(self):
        self.config_file = 'cloud_config.json'
        self.credentials = self.load_credentials()
    
    def load_credentials(self) -> Dict:
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_credentials(self, service: str, credentials: Dict):
        self.credentials[service] = credentials
        with open(self.config_file, 'w') as f:
            json.dump(self.credentials, f)
    
    def connect_google_drive(self, user_id: int, auth_code: str) -> bool:
        try:
            self.credentials[f'gdrive_{user_id}'] = {
                'service': 'google_drive',
                'connected': True,
                'user_id': user_id,
                'auth_code': auth_code
            }
            self.save_credentials(f'gdrive_{user_id}', 
                                 self.credentials[f'gdrive_{user_id}'])
            return True
        except Exception as e:
            print(f"Ошибка подключения Google Drive: {e}")
            return False
    
    def connect_dropbox(self, user_id: int, access_token: str) -> bool:
        try:
            self.credentials[f'dropbox_{user_id}'] = {
                'service': 'dropbox',
                'connected': True,
                'user_id': user_id,
                'access_token': access_token
            }
            self.save_credentials(f'dropbox_{user_id}', 
                                 self.credentials[f'dropbox_{user_id}'])
            return True
        except Exception as e:
            print(f"Ошибка подключения Dropbox: {e}")
            return False
    
    def upload_to_google_drive(self, user_id: int, file_path: str, 
                               folder_name: str = 'StudyBoost') -> Optional[str]:
        creds = self.credentials.get(f'gdrive_{user_id}')
        if not creds or not creds.get('connected'):
            return None
        
        print(f"Загрузка {file_path} в Google Drive...")
        return f"https://drive.google.com/file/example_{user_id}"
    
    def upload_to_dropbox(self, user_id: int, file_path: str, 
                         folder_path: str = '/StudyBoost') -> Optional[str]:
        creds = self.credentials.get(f'dropbox_{user_id}')
        if not creds or not creds.get('connected'):
            return None
        
        print(f"Загрузка {file_path} в Dropbox...")
        return f"https://www.dropbox.com/s/example_{user_id}"
    
    def sync_notes(self, user_id: int, notes_data: Dict, 
                  service: str = 'google_drive') -> bool:
        try:
            temp_file = f'temp_sync_{user_id}.json'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, ensure_ascii=False, indent=2)
            
            if service == 'google_drive':
                url = self.upload_to_google_drive(user_id, temp_file)
            elif service == 'dropbox':
                url = self.upload_to_dropbox(user_id, temp_file)
            else:
                return False
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return url is not None
        
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")
            return False
    
    def is_connected(self, user_id: int, service: str = 'google_drive') -> bool:
        key = f'{service}_{user_id}'
        return key in self.credentials and self.credentials[key].get('connected', False)
    
    def disconnect(self, user_id: int, service: str = 'google_drive'):
        key = f'{service}_{user_id}'
        if key in self.credentials:
            del self.credentials[key]
            self.save_credentials(key, {})
    
    def get_connection_url(self, service: str = 'google_drive') -> str:
        if service == 'google_drive':
            return "https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID"
        elif service == 'dropbox':
            return "https://www.dropbox.com/oauth2/authorize?client_id=YOUR_APP_KEY"
        return ""
