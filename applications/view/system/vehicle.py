from datetime import datetime, timedelta

import cv2
import numpy as np
from flask import Blueprint, render_template, Response, jsonify, request
from flask_login import login_required
from sqlalchemy import desc
from sqlalchemy.orm import aliased

from applications.common.utils.http import fail_api, success_api, table_api
from applications.common.utils.license_plate_recognition import license_plate_recognition
from applications.common.utils.rights import authorize
from applications.extensions import db
from applications.models import VehicleInfo, VehicleEntryExit, ParkingSpaceInfo, PaymentRecord

bp = Blueprint('vehicle', __name__, url_prefix='/vehicle')
lpr = license_plate_recognition()


# 车辆信息注册
@bp.route('/info_register')
def info_register():
    return render_template('system/vehicle/info_register.html')


# 车辆信息表格
@bp.route('/info_table')
def vehicle_info_table():
    # 获取筛选和分页参数
    license_plate = request.args.get('license_plate', type=str)
    name = request.args.get('name', type=str)
    page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=10)

    # 构建查询条件
    filters = []
    if license_plate:
        filters.append(VehicleInfo.license_plate.like(f"%{license_plate}%"))
    if name:
        filters.append(VehicleInfo.name.like(f"%{name}%"))

    # 构建查询对象并执行分页查询
    query = VehicleInfo.query.filter(*filters).order_by(VehicleInfo.create_time.desc())
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    # 格式化数据
    vehicle_data = [{
        'id': vehicle.id,
        'license_plate': vehicle.license_plate,
        'name': vehicle.name,
        'address': vehicle.address,
        'phone': vehicle.phone,
        'type': vehicle.type,
        'color': vehicle.color,
        'registration_start_date': vehicle.registration_start_date.strftime("%Y-%m-%d"),
        'registration_end_date': vehicle.registration_end_date.strftime("%Y-%m-%d"),
        'photo_path': vehicle.photo_path,
        'create_time': vehicle.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        'update_time': vehicle.update_time.strftime("%Y-%m-%d %H:%M:%S")
    } for vehicle in pagination.items]

    return table_api(data=vehicle_data, count=pagination.total)


@bp.route('/info_update', methods=['PUT'])
def update_vehicle_info():
    req_json = request.get_json(force=True)
    vehicle_id = req_json.get("id")
    updated_data = req_json.get("updated_data")

    vehicle = VehicleInfo.query.get_or_404(vehicle_id)
    for key, value in updated_data.items():
        if hasattr(vehicle, key):
            setattr(vehicle, key, value)

    db.session.commit()
    return success_api(msg="车辆信息更新成功")


@bp.route('/info_remove/<int:id>', methods=['DELETE'])
@authorize("system:vehicle:info_remove", log=True)
def delete_vehicle(id):
    vehicle = VehicleInfo.query.get_or_404(id)
    db.session.delete(vehicle)
    db.session.commit()
    return success_api(msg="删除成功")


# 车辆信息主页面
@bp.route('/info_main')
def info_main():
    return render_template('system/vehicle/info_main.html')


# 车辆出入表格
@bp.route('/entry_exit_table')
def vehicle_entry_exit_table():
    # 获取筛选和分页参数
    license_plate = request.args.get('license_plate', type=str)
    entry_exit_flag = request.args.get('entry_exit_flag', type=str)
    page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=10)

    # 构建查询条件
    filters = [VehicleEntryExit.license_plate.like(f"%{license_plate}%")] if license_plate else []
    if entry_exit_flag:
        filters.append(VehicleEntryExit.entry_exit_flag == entry_exit_flag)

    # 为PaymentRecord表创建别名以避免连接冲突
    PaymentRecordAlias = aliased(PaymentRecord)

    # 构建查询对象，包括外连接到PaymentRecord
    query = db.session.query(
        VehicleEntryExit,
        PaymentRecordAlias.fee,
        PaymentRecordAlias.parking_duration
    ).outerjoin(
        PaymentRecordAlias, VehicleEntryExit.license_plate == PaymentRecordAlias.license_plate
    ).filter(*filters).order_by(desc(VehicleEntryExit.timestamp))

    # 执行分页查询
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    entry_exit_data = [{
        'id': item[0].id,
        'license_plate': item[0].license_plate,
        'entry_exit_flag': item[0].entry_exit_flag,
        'timestamp': item[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        'vehicle_image_path': item[0].vehicle_image_path,
        'create_time': item[0].create_time.strftime("%Y-%m-%d %H:%M:%S"),
        'update_time': item[0].update_time.strftime("%Y-%m-%d %H:%M:%S"),
        'parking_duration': item[2] if item[2] else None,  # parking_duration来自PaymentRecordAlias
        'fee': item[1] if item[1] else None  # fee来自PaymentRecordAlias
    } for item in pagination.items]


    return table_api(data=entry_exit_data, count=pagination.total)


# 车辆初入主页面
@bp.route('/entry_exit_main')
def entry_exit_main():
    return render_template('system/vehicle/entry_exit_main.html')


@bp.route('/entry_exit_update', methods=['PUT'])
def update_vehicle_entry_exit():
    req_json = request.get_json(force=True)
    record_id = req_json.get("id")
    updated_data = req_json.get("updated_data")

    record = VehicleEntryExit.query.get_or_404(record_id)
    for key, value in updated_data.items():
        if hasattr(record, key):
            setattr(record, key, value)

    db.session.commit()
    return success_api(msg="车辆出入记录更新成功")


@bp.route('/entry_exit_remove/<int:id>', methods=['DELETE'])
def delete_vehicle_entry_exit(id):
    record = VehicleEntryExit.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return success_api(msg="车辆出入记录删除成功")


# 车辆识别
@bp.route('/recognize')
def recognize():
    return render_template('system/vehicle/recognize.html')


# 识别车牌
@bp.route('/info/capture_plate')
def capture_plate():
    if lpr.is_camera_active:
        return Response(lpr.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return fail_api(msg="摄像头未激活")


# 开启摄像头
@bp.route('/info/start_camera', methods=['POST'])
def start_camera():
    if lpr.start_camera():
        return success_api(msg="摄像头启动成功")
    else:
        return fail_api(msg="摄像头已被其他用户使用，请关闭后再进行开启")


# 关闭摄像头
@bp.route('/info/stop_camera', methods=['POST'])
def stop_camera():
    if lpr.stop_camera():
        return success_api(msg="摄像头停止成功")
    else:
        return fail_api(msg="摄像头已经停止")


# 拍照
@bp.route('/info/capture_photo', methods=['POST'])
def capture_photo():
    if not lpr.is_camera_active:
        return fail_api(msg="摄像头未激活")

    plates, error = lpr.capture_and_recognize()
    if error:
        return fail_api(msg=error)

    if plates:
        return jsonify(success=True, data=plates)
    else:
        return fail_api(msg="未识别到车牌")


# 上传图片识别
@bp.route('/info/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify(success=False, msg="没有文件上传")

    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, msg="没有选择文件")

    # 读取文件内容为字节流
    file_content = file.read()
    nparr = np.frombuffer(file_content, np.uint8)

    # 使用 OpenCV 解码图像
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify(success=False, msg="无法解析图像")

    results = lpr.process_uploaded_image(img)

    if results:
        # 返回包含车牌信息和文件路径的响应
        return jsonify(success=True, data=results)
    else:
        return jsonify(success=True, msg="未识别到车牌")


@bp.route('/info/register', methods=['POST'])
@login_required
def register_vehicle():
    # 获取表单数据

    # 从JSON请求体获取数据
    req_json = request.get_json(force=True)
    license_plate = req_json.get('license_plate', '').strip()
    name = req_json.get('name', '').strip()
    address = req_json.get('address', '').strip()
    phone = req_json.get('phone', '').strip()
    vehicle_type = req_json.get('type', '').strip()
    registration_start_date = req_json.get('registration_start_date', '')
    registration_end_date = req_json.get('registration_end_date', '')
    photo_path = req_json.get('photo_path', '')
    color = req_json.get('color', '')
    custom_color = req_json.get('custom_color', '')
    custom_type = req_json.get('custom_type', '')

    if vehicle_type == '自定义':
        # 如果颜色是自定义颜色，则使用自定义的颜色
        if not custom_type:
            return fail_api(msg="自定义车辆类型必填")
        vehicle_type = custom_type

    if color == '自定义':
        # 如果颜色是自定义颜色，则使用自定义的颜色
        if not custom_color:
            return fail_api(msg="自定义颜色必填")
        color = custom_color

    # 校验必填字段
    if not license_plate:
        return fail_api(msg="车牌号不能为空")
    if not name:
        return fail_api(msg="车主姓名不能为空")
    if not address:
        return fail_api(msg="地址不能为空")
    if not phone:
        return fail_api(msg="电话号码不能为空")
    if not vehicle_type:
        return fail_api(msg="车辆类型不能为空")
    if not color:
        return fail_api(msg="车辆类型不能为空")
    if not registration_start_date or not registration_end_date:
        return fail_api(msg="注册开始和结束日期不能为空")
    if not photo_path:
        return fail_api(msg="车牌照片不能为空")

    # 转换日期格式
    try:
        registration_start_date = datetime.strptime(registration_start_date, '%Y-%m-%d')
        registration_end_date = datetime.strptime(registration_end_date, '%Y-%m-%d')
    except ValueError:
        return fail_api(msg="日期格式错误，请使用正确的日期格式")

    # 检查注册的开始时间是否早于结束时间
    if registration_start_date >= registration_end_date:
        return fail_api(msg="注册开始时间必须早于结束时间")

    # 创建新的车辆信息记录
    new_vehicle = VehicleInfo(
        license_plate=license_plate,
        name=name,
        address=address,
        phone=phone,
        type=vehicle_type,
        color=color,
        registration_start_date=registration_start_date,
        registration_end_date=registration_end_date,
        create_time=datetime.now(),
        photo_path=photo_path
    )
    db.session.add(new_vehicle)
    db.session.commit()

    return success_api(msg="登记成功")


MIN_INTERVAL = timedelta(seconds=5)  # 设置最小识别间隔为5秒


@bp.route('/recognize/get_plates')
def get_plates():
    mode = request.args.get('mode', 'entry')
    specific_plate = request.args.get('license_plate')  # 获取特定车牌号的参数
    plates_info = [specific_plate] if specific_plate else lpr.plates_info

    if not plates_info:
        return jsonify([])

    results = []
    try:
        for plate in plates_info:
            if not plate:  # 跳过空值
                continue

            vehicle_info = VehicleInfo.query.filter_by(license_plate=plate).first()
            parking_info = ParkingSpaceInfo.query.first()

            last_state = VehicleEntryExit.query.filter_by(license_plate=plate).order_by(
                VehicleEntryExit.timestamp.desc()).first()

            if last_state and (datetime.now() - last_state.timestamp) < MIN_INTERVAL:
                continue
            if last_state and ((mode == 'entry' and last_state.entry_exit_flag == 'entry') or
                               (mode == 'exit' and last_state.entry_exit_flag == 'exit')):
                continue

            if mode == 'entry':
                new_entry = VehicleEntryExit(license_plate=plate, entry_exit_flag='entry', timestamp=datetime.now())
                db.session.add(new_entry)
                if parking_info:
                    parking_info.occupied_spaces = min(parking_info.occupied_spaces + 1, parking_info.total_spaces)
                result = create_entry_result(plate, new_entry, parking_info, vehicle_info)
                results.append(result)
            elif mode == 'exit':
                if not last_state:
                    continue  # 如果没有入场记录，则不处理出场
                new_exit = VehicleEntryExit(license_plate=plate, entry_exit_flag='exit', timestamp=datetime.now())
                db.session.add(new_exit)
                if parking_info:
                    parking_info.occupied_spaces = max(parking_info.occupied_spaces - 1, 0)

                parking_duration = (new_exit.timestamp - last_state.timestamp).total_seconds()
                fee = calculate_fee(parking_duration / 60)  # 转换为分钟
                new_payment = PaymentRecord(
                    license_plate=plate,
                    entry_time=last_state.timestamp,
                    exit_time=new_exit.timestamp,
                    parking_duration=int(parking_duration),
                    fee=fee
                )
                db.session.add(new_payment)
                result = create_exit_result(plate, new_exit, last_state, vehicle_info)
                results.append(result)

        db.session.commit()

    except Exception as e:
        print("发生错误:", e)
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500

    return jsonify(results)


def create_entry_result(plate, new_entry, parking_info, vehicle_info):
    vehicle_type = "外来车辆" if vehicle_info is None else "已登记车辆"
    return {
        'license_plate': plate,
        'entry_time': new_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'total_spaces': parking_info.total_spaces if parking_info else None,
        'available_spaces': parking_info.total_spaces - parking_info.occupied_spaces if parking_info else None,
        'vehicle_type': vehicle_type
    }


def create_exit_result(plate, new_exit, last_entry, vehicle_info):
    vehicle_type = "外来车辆" if vehicle_info is None else "已登记车辆"
    parking_duration = max((new_exit.timestamp - last_entry.timestamp).total_seconds(), 1)
    fee = calculate_fee(parking_duration / 60)
    return {
        'license_plate': plate,
        'vehicle_type': vehicle_type,
        'parking_duration': format_duration(int(parking_duration)),
        'fee': '￥{:.2f}'.format(fee)
    }


def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return "{}小时{}分钟{}秒".format(hours, minutes, seconds)


def calculate_fee(duration_minutes):
    if duration_minutes < 0.5:
        return 0
    fee = min(20, (duration_minutes // 60 + (duration_minutes % 60 > 0)) * 5)
    return fee
