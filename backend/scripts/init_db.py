import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base import Base
from app.db.database import engine
from app import models as _models  # noqa: F401


def main() -> None:
    reset = "--reset" in sys.argv
    if reset:
        Base.metadata.drop_all(bind=engine)
        print("已删除旧表")
    Base.metadata.create_all(bind=engine)
    print("建表完成：", ", ".join(sorted(Base.metadata.tables.keys())))


if __name__ == "__main__":
    main()