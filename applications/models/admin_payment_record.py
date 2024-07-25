from datetime import datetime
from applications.extensions import db


class PaymentRecord(db.Model):
    """
    收费记录表: 记录车辆的停车时长和收费信息
    """
    __tablename__ = 'admin_payment_record'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    license_plate = db.Column(db.String(20), comment='车牌号')
    entry_time = db.Column(db.DateTime, comment='进入时间')
    exit_time = db.Column(db.DateTime, comment='离开时间')
    parking_duration = db.Column(db.Integer, comment='停车时长')
    fee = db.Column(db.DECIMAL(10, 2), comment='收费金额')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
