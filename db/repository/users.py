from db.repository.base import BaseRepository
from models.users import Users

class UsersRepository(BaseRepository[Users]):
    def __init__(self):
        super().__init__(Users)