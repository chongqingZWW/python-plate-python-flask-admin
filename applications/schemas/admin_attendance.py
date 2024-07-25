from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from applications.models import Attendance, Leave, SignIn, AttendanceSummary


class AttendanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Attendance
        include_fk = True


class LeaveSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Leave
        include_fk = True


class SignInSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SignIn
        include_fk = True


class AttendanceSummarySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AttendanceSummary
        include_fk = True
