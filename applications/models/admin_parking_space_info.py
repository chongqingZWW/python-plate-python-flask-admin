from datetime import datetime
from applications.extensions import db


class ParkingSpaceInfo(db.Model):
    """
    车位信息表: 存储车位总数和已占用数量
    """
    __tablename__ = 'admin_parking_space_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_spaces = db.Column(db.Integer, comment='总车位数')
    occupied_spaces = db.Column(db.Integer, comment='已占用车位数')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
