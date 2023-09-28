from unqlite import UnQLite

from nonebot_adapter_onebot_pretender.store import datastore

db = UnQLite(str(datastore.data_dir / "database.db"))
