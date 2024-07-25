from datetime import datetime
from applications.extensions import db


class VehicleEntryExit(db.Model):
    """
    车辆进出记录表: 记录车辆的进出时间和车牌信息
    """
    __tablename__ = 'admin_vehicle_entry_exit'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    license_plate = db.Column(db.String(20), comment='车牌号')
    entry_exit_flag = db.Column(db.String(10), comment='进出标志')
    timestamp = db.Column(db.DateTime, comment='进出时间')
    vehicle_image_path = db.Column(db.String(255), comment='车辆照片路径')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
