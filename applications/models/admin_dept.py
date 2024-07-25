import datetime
from applications.extensions import db
from applications.models.admin_user import User


class Dept(db.Model):
    __tablename__ = 'admin_dept'
    id = db.Column(db.Integer, primary_key=True, comment="部门ID")
    parent_id = db.Column(db.Integer, comment="父级编号")
    dept_name = db.Column(db.String(50), comment="部门名称")
    sort = db.Column(db.Integer, comment="排序")
    leader = db.Column(db.String(50), comment="负责人")
    phone = db.Column(db.String(20), comment="联系方式")
    email = db.Column(db.String(50), comment="邮箱")
    status = db.Column(db.Integer, comment='状态(1开启,0关闭)')
    remark = db.Column(db.Text, comment="备注")
    address = db.Column(db.String(255), comment="详细地址")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='创建时间')

    def get_teachers(self):
        teachers = [user for user in User.query.filter_by(dept_id=self.id).all() if user.is_teacher()]
        return teachers

    def get_students(self):
        # 查询该部门所有用户
        users_in_dept = User.query.filter_by(dept_id=self.id).all()
        # 筛选出具有“学生”角色的用户
        students = [user for user in users_in_dept if user.is_student()]
        return students
