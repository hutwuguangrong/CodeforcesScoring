from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine("mysql+pymysql://root:1332931844@localhost:3306/CodeforcesScroing", pool_size=10)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_name = Column(String(30))  # 姓名
    class_pro = Column(String(100))  # 专业班级
    cf_name = Column(String(100))  # cf 姓名
    cf_rating = Column(Integer)  # cf 分数
    cf_profile_url = Column(String(100))  # cf 资料地址

    def to_json(self):
        return {
            "id": self.id,
            "user_name": self.user_name,
            "class_pro": self.class_pro,
            "cf_name": self.cf_name,
            "cf_rating": self.cf_rating,
            "cf_profile_url": self.cf_profile_url,
        }


Base.metadata.create_all(engine)  # 创建数据库表from
