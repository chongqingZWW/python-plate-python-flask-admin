from datetime import datetime

from applications.extensions import db


class VehicleInfo(db.Model):
    __tablename__ = 'admin_vehicle_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键，唯一标识
    license_plate = db.Column(db.String(255), comment='车牌号')
    name = db.Column(db.String(255), comment='业主姓名')
    address = db.Column(db.Text, comment='业主地址')
    phone = db.Column(db.String(20), comment='业主电话')
    type = db.Column(db.String(50), comment='车辆类型')
    color = db.Column(db.String(50), comment='车辆颜色')
    registration_start_date = db.Column(db.Date, comment='登记开始日期')
    registration_end_date = db.Column(db.Date, comment='登记截止日期')
    photo_path = db.Column(db.String(255), comment='车牌照图片')
    create_time = db.Column(db.DateTime, default=datetime.now)  # 创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间