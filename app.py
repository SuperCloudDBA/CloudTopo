# -*- coding:utf8 -*-
import json
import os
import uuid
import datetime
from flask import Flask
from flask import request, redirect, url_for
from flask import make_response
from flask import render_template
from flask import send_file, send_from_directory
from core_app import get_json_from_ak
from core_app import get_json_from_excel
# 上传文件功能
import platform
from werkzeug.utils import secure_filename

if platform.system() == "Windows":
    slash = '\\'
else:
    platform.system() == "Linux"
    slash = '/'
UPLOAD_FOLDER = 'upload'
ALLOW_EXTENSIONS = set(['png', 'xlsx'])
# 判断文件夹是否存在，如果不存在则创建
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
else:
    pass


# 判断文件后缀是否在列表中
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOW_EXTENSIONS


app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = datetime.timedelta(seconds=1)  # 将缓存时间设置为1秒
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=('POST', 'GET'))
def index():
    if request.method == 'GET':
        show = 'collapse'
        log_strings = ''
        check = ''
        disabled = ''
        download_active = 'disabled'
        return render_template('index.html', show=show, log_strings=log_strings, check=check, disabled=disabled,
                               download_active=download_active)
    elif request.method == 'POST':
        filename = None
        log_strings = None
        disabled = 'disabled'
        download_active = ''
        check = request.form.get("download")
        slb = request.form.get("inlineCheckbox_slb")
        ecs = request.form.get("inlineCheckbox_ecs")
        rds = request.form.get("inlineCheckbox_rds")
        polardb = request.form.get("inlineCheckbox_polardb")
        rds_dbs = request.form.get("inlineCheckbox_rds_dbs")
        polardb_dbs = request.form.get("inlineCheckbox_polardb_dbs")
        redis = request.form.get("inlineCheckbox_redis")
        mongodb = request.form.get("inlineCheckbox_mongodb")
        dts_sync = request.form.get("inlineCheckbox_dts_sync")
        dts_migrate = request.form.get("inlineCheckbox_dts_migrate")
        products = [slb, ecs, rds, polardb, redis, mongodb, dts_sync, dts_migrate, rds_dbs, polardb_dbs]
        product = list(filter(lambda x: isinstance(x, str) and x is not None, products))

        web_params = {
            'RoleName': None,
            'Region': 'all',
            'Product': ','.join(product),
            'AccessKeyId': request.form.get('inputAccessKeyId'),
            'AccessKeySecret': request.form.get("inputAccessKeySecret")
        }

        if check:
            print(check)
            response = make_response(
                send_file(check, as_attachment=True, attachment_filename=check.split('/')[-1]))
            response.headers["Content-Disposition"] = "attachment; filename={}".format(
                check.encode().decode('latin-1'))
            return response
        else:
            if not web_params["AccessKeyId"] or not web_params["AccessKeySecret"] or not product:
                show = 'collapse'
                log_strings = ''
                check = ''
                disabled = ''
                download_active = 'disabled'
                return render_template('index.html', show=show, log_strings=log_strings, check=check, disabled=disabled,
                                       download_active=download_active)
            else:
                print(json.dumps(web_params, indent=2))
                print("下载属性")
                print(check)
                if not check:
                    filename, log_strings = get_json_from_ak.startup(**web_params)
                    print(log_strings)
                    show = 'collapse show'
                    disabled = ''
                    check = filename
                    return render_template('index.html', show=show, log_strings=log_strings, check=check,
                                           disabled=disabled, download_active=download_active)


@app.route('/index_excel/', methods=('POST', 'GET'))
def index_excel():
    if request.method == 'GET':
        return render_template('index_excel.html')
    elif request.method == 'POST':
        excel_demo = request.form.get("download")
        excel_upload = request.form.get("upload")
        print(excel_upload)
        if excel_demo == "excel-demo":
            file_name = "./static/excel/excel-demo.xlsx"
            response = make_response(
                send_file(file_name, as_attachment=True, attachment_filename=file_name.split('/')[-1]))
            response.headers["Content-Disposition"] = "attachment; filename={}".format(
                file_name.encode().decode('latin-1'))
            return response
        elif excel_upload == 'excel-upload':
            # 获取post过来的文件名称，从name=file参数中获取
            file = request.files['file']
            if file and allowed_file(file.filename):
                # secure_filename方法会去掉文件名中的中文
                filename = secure_filename(file.filename)
                # 因为上次的文件可能有重名，因此使用uuid保存文件
                file_name = str(uuid.uuid4()) + '.' + filename.rsplit('.', 1)[1]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
                base_path = os.getcwd()
                print(base_path)
                file_path = base_path + slash + app.config['UPLOAD_FOLDER'] + slash + file_name
                print(file_path)
                alert = 'alert'
                disabled = 'disabled'
                # 开始调用自动拓扑的方法，生成自动拓扑架构
                get_json_from_excel.startup(file_path)
                return render_template('index_excel.html', alert=alert, disabled=disabled)
        else:
            return "error"

@app.route('/index_online/')
def index_online():
    return render_template('index_online.html')


@app.route('/instances/')
def instances():
    return render_template('instances.html')


@app.route('/excel/')
def excel():
    return render_template('excel.html')


app.run(debug=True, host='0.0.0.0', port=5000)
