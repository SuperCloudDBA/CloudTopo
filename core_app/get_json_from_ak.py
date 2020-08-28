# -*- coding: utf-8 -*-
"""
Booboowei
2020.07.22
在阿里云获取实例小工具基础上改造
除了输出excel表格外
还输出topo图需要的json类型

难点：坐标系建立图形全坐标
"""

# Build-in Modules
import os
import time
import shutil
import uuid
import json

# 3rd-part Modules
from jinja2 import Template
import argparse
import xlsxwriter
import progressbar
from aliyun_sdk import client

now_date = time.strftime('%Y%m%d', time.localtime())

log_strings = []


class OSHelper:
    def __init__(self):
        pass

    def mkdir(self, path):
        """
        在当前目录下创建子目录
        """
        try:
            os.makedirs(path)
        except Exception as e:
            # log_strings.append(str(e))
            return path
        else:
            return path

    def rmdir(self, path):
        """
        递归删除目录
        """
        try:
            shutil.rmtree(path)
        except Exception as e:
            log_strings.append(str(e))
            return path
        else:
            return path

    def rmfile(self, path):
        """
        删除文件
        """
        try:
            os.remove(path)
        except Exception as e:
            log_strings.append(str(e))
            return path
        else:
            return path


class ToExcel:
    def __init__(self, **kwargs):
        # 创建目录
        os_api = OSHelper()
        dir_name = os_api.mkdir(kwargs['dir_name'])
        self.file_name = os.path.join(dir_name, '{}-{}.xlsx'.format(kwargs['file_name'], now_date))
        self.workbook = xlsxwriter.Workbook(self.file_name)

    def write_file_column(self, work, worksheet, list_name):
        top = self.workbook.add_format(
            {'border': 1, 'align': 'center', 'bg_color': '#83CAF4', 'font_size': 10, 'bold': True})  # 设置单元格格式
        j = 0
        for i in list_name:
            worksheet.write(0, j, i, top)
            j += 1

    def add_sheet(self, **kwargs):
        type, shee_name, list_name, list_keys, lines = kwargs.values()
        column = self.workbook.add_format({'border': 1, 'align': 'center', 'font_size': 10})
        worksheet = self.workbook.add_worksheet(shee_name)

        for _c in range(len(list_keys)):
            worksheet.set_column('{0}:{0}'.format(chr(_c + ord('A'))), 20)
        self.write_file_column(self, worksheet, list_name)
        row = 1
        for i in lines:
            # print(json.dumps(i, indent=2))
            for col in range(len(list_name)):
                worksheet.write(row, col, i.get(list_keys[col], 'no_result'), column)
            row = row + 1

    def write_close(self):
        self.workbook.close()


class ToTopo:
    def __init__(self, data_topo):
        # log_strings.append(json.dumps(data_topo, indent=2, ensure_ascii=False))
        self.topo_data = data_topo

    def auto_position(self, product, x=50, y=50):
        i = 200
        j = 60

        # 一行打印10个
        # 打印几行？

        if len(product) % 10 == 0:
            row = round(len(product) / 10)
        else:
            row = round(len(product) / 10) + 1

        for _row in range(row):
            y = 50
            for _col in range(1, 11):
                try:
                    product[_col - 1 + _row * 10]["x"] = x
                    product[_col - 1 + _row * 10]["y"] = y
                    product[_col - 1 + _row * 10]['elementType'] = "node"
                    product[_col - 1 + _row * 10]['id'] = str(uuid.uuid4())
                    product[_col - 1 + _row * 10]['Image'] = "{0}.png".format(
                    product[_col - 1 + _row * 10]["instance_product"])
                    product[_col - 1 + _row * 10]["text"] = product[_col - 1 + _row * 10]["instance_id"]  # 实例ID
                    product[_col - 1 + _row * 10]["textPosition"] = "Bottom_Center"
                    product[_col - 1 + _row * 10]["larm"] = "Middle_Center"
                    if product[0]["instance_product"] in ("rds_dbs", "polardb_dbs"):
                        product[_col - 1 + _row * 10]["level"] = 2
                    else:
                        product[_col - 1 + _row * 10]["level"] = 1
                    # log_strings.append("row {0}  col{1}".format(_row, _col))
                    # log_strings.append("{}".format(_col + _row * 10))
                    # log_strings.append("x {0} y {0}".format(x, y))
                    y = y + j
                except:
                    break
            x = x + i
            # y = y + j
        log_strings.append("{0} Topo 数据渲染完成".format(product[0]["instance_product"].upper()))
        return product, x, y

    def to_json(self):
        # 获取待渲染节点的个数
        instance_num = len(self.topo_data)
        slb = list(filter(lambda x: x.get("instance_product") == 'slb', self.topo_data))
        ecs = list(filter(lambda x: x.get("instance_product") == 'ecs', self.topo_data))
        rds = list(filter(lambda x: x.get("instance_product") == 'rds', self.topo_data))
        polardb = list(filter(lambda x: x.get("instance_product") == 'polardb', self.topo_data))
        redis = list(filter(lambda x: x.get("instance_product") == 'redis', self.topo_data))
        mongodb = list(filter(lambda x: x.get("instance_product") == 'mongodb', self.topo_data))
        dts = list(filter(lambda x: x.get("instance_product") == 'dts', self.topo_data))
        rds_dbs = list(filter(lambda x: x.get("instance_product") == 'rds_dbs', self.topo_data))
        polardb_dbs = list(filter(lambda x: x.get("instance_product") == 'polardb_dbs', self.topo_data))
        # 容器 如果产品列表不为空则创建容器
        # 每个图片为45*45 因此给到的间隙为90
        # 同一类产品渲染在同一行
        node_result = []
        container_result = []
        x, y = 50, 50
        for product in [slb, ecs, rds, redis, mongodb, dts, polardb, rds_dbs, polardb_dbs]:
            if product:
                container_result.append({
                    "elementType": "container",
                    "text": product[0]["instance_product"]
                })
                # log_strings.append(product)
                y = 50
                out_product, x, y = self.auto_position(product, x, y)
                node_result.extend(out_product)

        return node_result + container_result


class GetInfo:
    def __init__(self):
        self.params = {
            'aliyun': [
                {
                    'type': 'slb',
                    'sheet_name': 'SLB',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '地域', '状态', '应用', '环境'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'region_id', 'status', 'APP', 'ENV']

                },
                {
                    'type': 'ecs',
                    'sheet_name': 'ECS',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '地域', '状态',  '应用', '环境'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'region_id', 'status', 'APP', 'ENV']

                }, {
                    'type': 'rds',
                    'sheet_name': 'RDS',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '端口', '地域', '存储引擎', '数据库版本', '实例类型'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'port', 'region_id',
                                  'engine',
                                  'engine_version',
                                  'instance_type']

                }, {
                    'type': 'rds_dbs',
                    'sheet_name': 'RDS Databases',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '端口', '地域', '存储引擎', '数据库版本', '实例类型',
                                  '数据库名', '数据库描述', '数据库引擎', '数据库字符集'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'port', 'region_id',
                                  'engine',
                                  'engine_version',
                                  'instance_type',
                                  "db_name", "db_description", "db_engine", "db_character_set_name"]

                }, {
                    'type': 'polardb',
                    'sheet_name': 'PolarDB',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '端口', '地域', '数据库类型', '数据库版本'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'port', 'region_id',
                                  'engine',
                                  'engine_version'
                                  ]

                },
                {
                    'type': 'polardb_dbs',
                    'sheet_name': 'PolarDB Databases',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '端口', '地域', '数据库类型', '数据库版本',
                                  '数据库名', '数据库描述', '数据库引擎', '数据库字符集'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'port', 'region_id',
                                  'engine',
                                  'engine_version',
                                  "db_name", "db_description", "db_engine", "db_character_set_name"
                                  ]

                },
                {
                    'type': 'redis',
                    'sheet_name': 'Redis',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '端口', '地域', '版本', ],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'port', 'region_id',
                                  'architecture_type']

                },
                {
                    'type': 'mongodb',
                    'sheet_name': 'MongoDB',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '端口', '地域', '角色'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'port',
                                  'region_id', 'instance_role']

                },
                {
                    'type': 'drds',
                    'sheet_name': 'DRDS',
                    'list_name': ['产品', '实例ID', '实例描述', '内网地址', '端口', '地域', ],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'connection_address',
                                  'port', 'region_id']

                },
                {
                    'type': 'dts_sync',
                    'sheet_name': 'DTS同步',
                    'list_name': ['产品', '实例ID', '实例描述', '任务状态',
                                  '源实例ID', '源实例描述', '源实例地域', '源数据库类型',
                                  '源数据库连接地址', '源数据库监听端口', '源数据库访问账号', '源Oracle SID', '源数据库名称',
                                  '目标实例ID', '目标实例描述', '目标实例地域',
                                  '目标实例数据库类型', '目标数据库连接地址', '目标数据库监听端口', '目标数据库访问账号', '目标Oracle SID', '目标数据库名称'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'Status',
                                  'SourceEndpoint_InstanceId', 'SourceEndpoint_InstanceType', 'SourceEndpoint_Region',
                                  'SourceEndpoint_EngineName', 'SourceEndpoint_IP', 'SourceEndpoint_Port',
                                  'SourceEndpoint_UserName',
                                  'SourceEndpoint_OracleSID', 'SourceEndpoint_DatabaseName',
                                  'DestinationEndpoint_InstanceId', 'DestinationEndpoint_InstanceType',
                                  'DestinationEndpoint_Region',
                                  'DestinationEndpoint_EngineName', 'DestinationEndpoint_IP',
                                  'DestinationEndpoint_Port', 'SDestinationEndpoint_UserName',
                                  'DestinationEndpoint_OracleSID', 'DestinationEndpoint_DatabaseName'
                                  ]

                },
                {
                    'type': 'dts_migrate',
                    'sheet_name': 'DTS迁移',
                    'list_name': ['产品', '实例ID', '实例描述', '任务状态',
                                  '源实例ID', '源实例描述', '源实例地域', '源数据库类型',
                                  '源数据库连接地址', '源数据库监听端口', '源数据库访问账号', '源Oracle SID', '源数据库名称',
                                  '目标实例ID', '目标实例描述', '目标实例地域',
                                  '目标实例数据库类型', '目标数据库连接地址', '目标数据库监听端口', '目标数据库访问账号', '目标Oracle SID', '目标数据库名称'],
                    'list_keys': ['instance_product', 'instance_id', 'instance_description', 'Status',
                                  'SourceEndpoint_InstanceId', 'SourceEndpoint_InstanceType', 'SourceEndpoint_Region',
                                  'SourceEndpoint_EngineName', 'SourceEndpoint_IP', 'SourceEndpoint_Port',
                                  'SourceEndpoint_UserName',
                                  'SourceEndpoint_OracleSID', 'SourceEndpoint_DatabaseName',
                                  'DestinationEndpoint_InstanceId', 'DestinationEndpoint_InstanceType',
                                  'DestinationEndpoint_Region',
                                  'DestinationEndpoint_EngineName', 'DestinationEndpoint_IP',
                                  'DestinationEndpoint_Port', 'SDestinationEndpoint_UserName',
                                  'DestinationEndpoint_OracleSID', 'DestinationEndpoint_DatabaseName'
                                  ]

                },
            ],
            # 'aws': [{}],
            # 'tencent': [{}],
            # 'azure': [{}],
        }

    def get_info(self, engine, filter_infos):
        """
        过滤
        """
        return list(filter(lambda x: x['type'] in filter_infos, self.params[engine]))


class Custom:
    def __init__(self):
        pass

    def get_config(self, **kwargs):
        self.out = kwargs
        self.aliyun = client.AliyunClient(config=kwargs)

    def get_slb_describe_regions(self):
        try:
            status_code, api_res = self.aliyun.common("slb", Action="DescribeRegions")
            region_ids = list(set(map(lambda x: x['RegionId'], api_res['Regions']['Region']
                                      )))
        except Exception as e:
            print(str(e))
            region_ids = []
        # print(region_ids)
        return region_ids

    def get_rds_describe_regions(self):
        try:
            status_code, api_res = self.aliyun.common("rds", Action="DescribeRegions")
            region_ids = list(set(map(lambda x: x['RegionId'], api_res['Regions']['RDSRegion']
                                      )))
        except Exception as e:
            print(str(e))
            region_ids = []
        # print(region_ids)
        return region_ids

    def get_redis_describe_regions(self):
        try:
            status_code, api_res = self.aliyun.common("redis", Action="DescribeRegions")
            region_ids = list(set(map(lambda x: x['RegionId'], api_res['RegionIds']['KVStoreRegion']
                                      )))
        except Exception as e:
            print(str(e))
            region_ids = []
        # print(region_ids)
        return region_ids

    def get_mongodb_describe_regions(self):
        try:
            status_code, api_res = self.aliyun.common("mongodb", Action="DescribeRegions")
            region_ids = list(set(map(lambda x: x['RegionId'], api_res['Regions']['DdsRegion']
                                      )))
        except Exception as e:
            print(str(e))
            region_ids = []
        # print(region_ids)
        return region_ids

    def get_polardb_describe_regions(self):
        try:
            status_code, api_res = self.aliyun.common("polardb", Action="DescribeRegions")
            region_ids = list(set(map(lambda x: x['RegionId'], api_res['Regions']['Region']
                                      )))
        except Exception as e:
            print(str(e))
            region_ids = []
        # print(region_ids)
        return region_ids

    def get_drds_describe_regions(self):
        try:
            status_code, api_res = self.aliyun.common("drds", Action="DescribeRegions")
            region_ids = list(set(map(lambda x: x['RegionId'], api_res['DrdsRegions']['DrdsRegion']
                                      )))
        except Exception as e:
            print(str(e))
            region_ids = []
        # print(region_ids)
        return region_ids

    def get_ecs_describe_regions(self):
        try:
            status_code, api_res = self.aliyun.common("ecs", Action="DescribeRegions")
            region_ids = list(set(map(lambda x: x['RegionId'], api_res['Regions']['Region']
                                      )))
        except Exception as e:
            print(str(e))
            region_ids = []
        # print(region_ids)
        return region_ids

    # get slb
    def get_slb_instance(self, all_regions):
        instance_list = []

        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("slb", Action="DescribeLoadBalancers", RegionId=region_id,
                                                              PageSize=100,
                                                              PageNumber=page_num)
                    # log_strings.append(json.dumps(api_res, indent=2))
                except Exception as e:
                    log_strings.append(str(e))

                if not api_res.get("LoadBalancers", {}).get("LoadBalancer", []):
                    break

                instance_list = instance_list + list(map(
                    lambda x: {"instance_id": x.get("LoadBalancerId"),
                               "instance_description": x.get("LoadBalancerName"),
                               "instance_product": "slb",
                               "connection_address": x.get("Address"),
                               "region_id": x.get("RegionId"),
                               "status": x.get("LoadBalancerStatus"),
                               },
                    api_res.get("LoadBalancers", {}).get("LoadBalancer", [])))
                page_num = page_num + 1
                # print(json.dumps(instance_list, indent=2))

        instance_list_tags = []
        for instance in instance_list:
            instance_id = {
                "LoadBalancerId": instance["instance_id"],
                "RegionId": instance["region_id"]
            }
            try:
                status_code, api_res_tags = self.aliyun.common("slb", Action="DescribeTags", **instance_id)
            except Exception as e:
                log_strings.append(str(e))
            else:
                for tag in api_res_tags.get("TagSets", {}).get("TagSet", []):
                    _d = {
                        "instance_id": instance["instance_id"],
                        "instance_description": instance["instance_description"],
                        "instance_product": "slb",
                        "connection_address": instance["connection_address"],
                        "region_id": instance["region_id"],
                        "status": instance["status"],
                    }
                    if tag["TagKey"] == "APP":
                        _d[tag["TagKey"]]: tag["TagValue"]
                    elif tag["TagKey"] == "ENV":
                        _d[tag["TagKey"]]: tag["TagValue"]
                    else:
                        _d["APP"] = ''
                        _d["ENV"] = ''
                    instance_list_tags.append(_d)
        return instance_list_tags

    # get ecs
    def get_ecs_instance(self, all_regions):
        instance_list = []

        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("ecs", Action="DescribeInstances",
                                                              RegionId=region_id, Total="TotalCount", PageSize=100,
                                                              PageNumber=page_num)
                except Exception as e:
                    log_strings.append(str(e))
                    break

                if not api_res.get("Instances", {}).get("Instance", []):
                    break
                # print(json.dumps(api_res, indent=2))

                instance_list = instance_list + list(map(
                    lambda x: {
                        "InstanceId": x.get("InstanceId"),
                        "tags": x.get("Tags", {}).get("Tag", [])
                    },
                    api_res.get("Instances", {}).get("Instance", [])))
                page_num = page_num + 1

        # print(json.dumps(instance_list, indent=2))
        datas = []

        for instance_id in instance_list:
            # print(instance_id["tags"])
            new_instance_id = {"InstanceId": instance_id["InstanceId"]}
            try:
                status_code, api_res = self.aliyun.common("ecs", Action="DescribeInstanceAttribute", **new_instance_id)
                # print(json.dumps(api_res, indent=2))
                # log_strings.append(json.dumps(api_res['InnerIpAddress']['IpAddress']))
            except Exception as e:
                log_strings.append(str(e))
            else:
                try:
                    vip = []
                    [vip.append(x) for x in api_res['VpcAttributes']['PrivateIpAddress']['IpAddress']]
                except Exception as e:
                    log_strings.append(str(e))
                else:
                    [vip.append(x) for x in api_res['InnerIpAddress']['IpAddress']]

                # print(json.dumps(instance_id, indent=2))
                APP = ''
                ENV = ''
                for tag in instance_id["tags"]:
                    if tag["TagKey"] == "APP":
                        APP = tag["TagValue"]
                    elif tag["TagKey"] == "ENV":
                        ENV = tag["TagValue"]
                    else:
                        APP = ''
                        ENV = ''

                # print("APP: {}".format(APP))
                # print("ENV: {}".format(ENV))
                instanceinfo_list = {
                                        "instance_id": api_res["InstanceId"],
                                        "instance_description": api_res["InstanceName"],
                                        "instance_product": "ecs",
                                        "connection_address": "".join(vip),
                                        "region_id": api_res["RegionId"],
                                        "status": api_res["Status"],
                                        "APP": APP,
                                        "ENV": ENV,
                                    },
                datas.extend(instanceinfo_list)
        return datas

    # get rds
    def get_rds_instance(self, all_regions):
        instance_list = []

        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("rds", Action="DescribeDBInstances", RegionId=region_id,
                                                              PageSize=100,
                                                              PageNumber=page_num)
                except Exception as e:
                    log_strings.append(str(e))
                    break

                if not api_res.get("Items", {}).get("DBInstance", []):
                    break

                instance_list = instance_list + list(map(
                    lambda x: {"DBInstanceId": x.get("DBInstanceId")},
                    api_res.get("Items", {}).get("DBInstance", [])))
                page_num = page_num + 1

        instanceinfo_list = []
        for instance_id in instance_list:
            try:
                status_code, api_res = self.aliyun.common("rds", Action="DescribeDBInstanceAttribute", **instance_id)
                # log_strings.append(json.dumps(api_res, indent=2))
            except Exception as e:
                log_strings.append(str(e))
            else:
                instanceinfo_list = instanceinfo_list + list(map(
                    lambda x: {"instance_id": x.get("DBInstanceId"),
                               "instance_description": x.get("DBInstanceDescription"),
                               "instance_product": 'rds',
                               "connection_address": x.get("ConnectionString"),
                               "port": x.get("Port"),
                               "region_id": x.get("RegionId"),
                               "engine": x.get("Engine"),
                               "engine_version": x.get("EngineVersion"),
                               "instance_type": x.get("DBInstanceType"),
                               },
                    api_res.get("Items", {}).get("DBInstanceAttribute", [])))

        return instanceinfo_list

    # get rds dbs
    def get_rds_database(self, all_regions):
        instance_list = []

        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("rds", Action="DescribeDBInstances", RegionId=region_id,
                                                              PageSize=100,
                                                              PageNumber=page_num)
                except Exception as e:
                    log_strings.append(str(e))
                    break

                if not api_res.get("Items", {}).get("DBInstance", []):
                    break

                instance_list = instance_list + list(map(
                    lambda x: {"DBInstanceId": x.get("DBInstanceId")},
                    api_res.get("Items", {}).get("DBInstance", [])))
                page_num = page_num + 1

        instanceinfo_list = []
        for instance_id in instance_list:
            try:
                status_code, api_res = self.aliyun.common("rds", Action="DescribeDBInstanceAttribute", **instance_id)
                # log_strings.append(json.dumps(api_res, indent=2))
            except Exception as e:
                log_strings.append(str(e))
            else:
                instanceinfo_list = instanceinfo_list + list(map(
                    lambda x: {"instance_id": x.get("DBInstanceId"),
                               "instance_description": x.get("DBInstanceDescription"),
                               "instance_product": 'rds',
                               "connection_address": x.get("ConnectionString"),
                               "port": x.get("Port"),
                               "region_id": x.get("RegionId"),
                               "engine": x.get("Engine"),
                               "engine_version": x.get("EngineVersion"),
                               "instance_type": x.get("DBInstanceType"),
                               },
                    api_res.get("Items", {}).get("DBInstanceAttribute", [])))

        instanceinfo_databases_list = []
        for instance_id in instanceinfo_list:
            params = {
                "DBInstanceId": instance_id["instance_id"]
            }
            try:
                status_code, api_res = self.aliyun.common("rds", Action="DescribeDatabases", **params)
                # print(api_res)
            except Exception as e:
                log_strings.append(e)
            else:
                for database in api_res.get("Databases", {}).get("Database", []):
                    instanceinfo_databases_list.append({
                        "instance_id": instance_id["instance_id"],
                        "instance_description": instance_id["instance_description"],
                        "instance_product": 'rds_dbs',
                        "connection_address": instance_id["connection_address"],
                        "port": instance_id["port"],
                        "region_id": instance_id["region_id"],
                        "engine": instance_id["engine"],
                        "engine_version": instance_id["engine_version"],
                        "instance_type": instance_id["instance_type"],
                        "db_name": database.get("DBName"),
                        "db_description": database.get("DBDescription"),
                        "db_engine": database.get("Engine"),
                        "db_character_set_name": database.get("CharacterSetName"),
                    })

        # print(instanceinfo_databases_list)
        return instanceinfo_databases_list

    # get polardb
    def get_polardb_instance(self, all_regions):
        instance_list = []
        instanceinfo_list = []
        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("polardb", Action="DescribeDBClusters",
                                                              RegionId=region_id,
                                                              PageSize=100,
                                                              PageNumber=page_num)
                    # log_strings.append(json.dumps(api_res, indent=2))
                except Exception as e:
                    log_strings.append(str(e))
                    break

                if not api_res.get("Items", {}).get("DBCluster", []):
                    break

                # 过滤出指定数据库Engines
                instance_list = instance_list + list(map(
                    lambda x: {"DBClusterId": x.get("DBClusterId"),
                               "RegionId": x["RegionId"]},
                    api_res.get("Items", {}).get("DBCluster", [])))

                page_num = page_num + 1
        for instance_id in instance_list:
            try:
                status_code, api_res = self.aliyun.common("polardb", Action="DescribeDBClusterAttribute", **instance_id)
                # log_strings.append(json.dumps(api_res, indent=2))
            except Exception as e:
                log_strings.append(str(e))
            else:
                instanceinfo_list.append({
                    "instance_id": api_res.get("DBClusterId"),
                    "instance_description": api_res.get("DBClusterDescription"),
                    "instance_product": "polardb",
                    "connection_address": '',
                    "port": '',
                    "region_id": api_res.get("RegionId"),
                    "engine": api_res.get("DBType"),
                    "engine_version": api_res.get("DBVersion"),
                })

        return instanceinfo_list

    # get polardb dbs
    def get_polardb_database(self, all_regions):
        instance_list = []
        instanceinfo_list = []
        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("polardb", Action="DescribeDBClusters",
                                                              RegionId=region_id,
                                                              PageSize=100,
                                                              PageNumber=page_num)
                    # log_strings.append(json.dumps(api_res, indent=2))
                except Exception as e:
                    log_strings.append(str(e))
                    break

                if not api_res.get("Items", {}).get("DBCluster", []):
                    break

                # 过滤出指定数据库Engines
                instance_list = instance_list + list(map(
                    lambda x: {"DBClusterId": x.get("DBClusterId"),
                               "RegionId": x["RegionId"]},
                    api_res.get("Items", {}).get("DBCluster", [])))

                page_num = page_num + 1

        # print(json.dumps(instance_list, indent=2))
        for instance_id in instance_list:
            try:
                status_code, api_res = self.aliyun.common("polardb", Action="DescribeDBClusterAttribute",
                                                          **instance_id)
                # print(json.dumps(api_res, indent=2))
            except Exception as e:
                log_strings.append(str(e))
            else:
                instanceinfo_list.append({
                    "instance_id": api_res.get("DBClusterId"),
                    "instance_description": api_res.get("DBClusterDescription"),
                    "instance_product": "polardb",
                    "connection_address": '',
                    "port": '',
                    "region_id": api_res.get("RegionId"),
                    "engine": api_res.get("DBType"),
                    "engine_version": api_res.get("DBVersion"),
                })
        instanceinfo_databases_list = []

        for instance_id in instanceinfo_list:
            params = {
                "DBClusterId": instance_id["instance_id"]
            }
            try:
                status_code, api_res = self.aliyun.common("polardb", Action="DescribeDatabases", **params)
                # print(json.dumps(api_res, indent=2))
            except Exception as e:
                log_strings.append(e)
            else:
                for database in api_res.get("Databases", {}).get("Database", []):
                    instanceinfo_databases_list.append({
                        "instance_id": instance_id["instance_id"],
                        "instance_description": instance_id["instance_description"],
                        "instance_product": 'polardb_dbs',
                        "connection_address": instance_id["connection_address"],
                        "port": instance_id["port"],
                        "region_id": instance_id["region_id"],
                        "engine": instance_id["engine"],
                        "engine_version": instance_id["engine_version"],
                        "db_name": database.get("DBName"),
                        "db_description": database.get("DBDescription"),
                        "db_engine": database.get("Engine"),
                        "db_character_set_name": database.get("CharacterSetName"),
                    })

        return instanceinfo_databases_list

    # get redis
    def get_redis_instance(self, all_regions):
        instance_list = []

        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("redis", Action="DescribeInstances", RegionId=region_id,
                                                              PageSize=100,
                                                              PageNumber=page_num)
                    # log_strings.append(json.dumps(api_res, indent=2))
                except Exception as e:
                    log_strings.append(str(e))
                    break

                if not api_res.get("Instances", {}).get("KVStoreInstance", []):
                    break

                instance_list = instance_list + list(map(
                    lambda x: {"InstanceId": x.get("InstanceId")},
                    api_res.get("Instances", {}).get("KVStoreInstance", [])))
                page_num = page_num + 1

        # log_strings.append(json.dumps(instance_list, indent=2))
        instanceinfo_list = []

        for instance_id in instance_list:
            try:
                status_code, api_res = self.aliyun.common("redis", Action="DescribeInstanceAttribute", **instance_id)
                # log_strings.append(json.dumps(api_res, indent=2))
            except Exception as e:
                log_strings.append(str(e))

            for x in api_res.get("Instances", {}).get("DBInstanceAttribute", []):
                # log_strings.append(json.dumps(x))
                instanceinfo_list.append(
                    {"instance_id": x.get("InstanceId"),
                     "instance_description": x.get("InstanceName"),
                     "instance_product": "redis",
                     "connection_address": x.get("ConnectionDomain"),
                     "port": x.get("Port"),
                     "region_id": x.get("RegionId"),
                     "architecture_type": x.get("ArchitectureType")  # cluster（集群版）standard（标准版）SplitRW（读写分离版）
                     })
                # 只取返回列表中的第一个元素，原因:https://gitlab.jiagouyun.com/DataProduct/zy_aliyun_metric/issues/16
                break

        return instanceinfo_list

    # get mongodb
    def get_mongodb_instance(self, all_regions):
        instance_list = []

        for region_id in all_regions:
            page_num = 1
            while True:
                # 循环获取实例
                try:
                    status_code, api_res = self.aliyun.common("mongodb", Action="DescribeDBInstances",
                                                              RegionId=region_id, PageSize=100,
                                                              PageNumber=page_num)
                except Exception as e:
                    log_strings.append(str(e))
                    break

                if not api_res.get("DBInstances", {}).get("DBInstance", []):
                    break
                instance_list = instance_list + list(map(
                    lambda x: {"DBInstanceId": x.get("DBInstanceId")},
                    list(api_res.get("DBInstances", {}).get("DBInstance", []))))
                page_num = page_num + 1

        instanceinfo_list = []

        for instance_id in instance_list:
            try:
                status_code, api_res = self.aliyun.common("mongodb", Action="DescribeDBInstanceAttribute",
                                                          **instance_id)
                # log_strings.append(json.dumps(api_res, indent=2))
            except Exception as e:
                log_strings.append(str(e))
            else:
                for x in api_res.get("DBInstances", {}).get("DBInstance", []):
                    for i in x.get("ReplicaSets", {}).get("ReplicaSet", [{}]):
                        instanceinfo_list.extend([{
                            "instance_id": x.get("DBInstanceId"),
                            "instance_description": x.get("DBInstanceDescription"),
                            "instance_product": "mongodb",
                            "connection_address": i.get("ConnectionDomain"),
                            "port": i.get("ConnectionPort"),
                            "region_id": x.get("RegionId"),
                            "instance_role": i.get("ReplicaSetRole"),
                        }])
        return instanceinfo_list

    # get drds
    def get_drds_instance(self, all_regions):
        instance_list = []
        # drds 没有翻页
        for region_id in all_regions:
            try:
                status_code, api_res = self.aliyun.common("drds", Action="DescribeDrdsInstances", RegionId=region_id)
            except Exception as e:
                log_strings.append(str(e))
            else:
                instance_list = instance_list + list(map(
                    lambda x: {"DrdsInstanceId": x.get("DrdsInstanceId")},
                    list(api_res.get("Data", {}).get("Instance", []))))

        instanceinfo_list = []

        for instance_id in instance_list:
            try:
                status_code, api_res = self.aliyun.common("drds", Action="DescribeDrdsInstance", **instance_id)
            except Exception as e:
                log_strings.append(str(e))
            else:
                instanceinfo_list = instanceinfo_list + list(map(
                    lambda x: {"instance_id": x.get("DrdsInstanceId"),
                               "instance_description": x.get("Description"),
                               "instance_product": "dts",
                               "connection_address": x.get("Vips", {}).get("Vip", [{}])[0].get("IP"),
                               "port": x.get("Vips", {}).get("Vip", [{}])[0].get("Port"),
                               "region_id": x.get("RegionId")
                               },
                    [api_res.get("Data", {})]))
        return instanceinfo_list

    # get dts sync
    def get_dts_sync_instance(self, all_regions):
        instance_info_list = []
        for region_id in all_regions:
            # api不支持翻页，将pagesize设置足够大即可。
            try:
                status_code, api_res = self.aliyun.common("dts", Action='DescribeSynchronizationJobs', RegionId=region_id,
                                                          PageSize=100, )
                # log_strings.append(json.dumps(api_res, indent=2, ensure_ascii=False))
            except Exception as e:
                log_strings.append(str(e))
            else:

                instance_info_list = instance_info_list + list(map(
                    lambda x: {
                        "instance_id": x.get("SynchronizationJobId"),
                        "instance_description": x.get("SynchronizationJobName"),
                        "instance_product": "dts",
                        "Status": x.get("Status"),
                        "SourceEndpoint_InstanceId": x.get("SourceEndpoint").get("InstanceId"),
                        "SourceEndpoint_InstanceType": x.get("SourceEndpoint").get("InstanceType"),
                        "SourceEndpoint_Region": x.get("SourceEndpoint").get("Region"),
                        "SourceEndpoint_EngineName": x.get("SourceEndpoint").get("EngineName"),
                        "SourceEndpoint_IP": x.get("SourceEndpoint").get("IP"),
                        "SourceEndpoint_Port": x.get("SourceEndpoint").get("Port"),
                        "SourceEndpoint_UserName": x.get("SourceEndpoint").get("UserName"),
                        "SourceEndpoint_OracleSID": x.get("SourceEndpoint").get("OracleSID"),
                        "SourceEndpoint_DatabaseName": x.get("SourceEndpoint").get("DatabaseName"),
                        "DestinationEndpoint_InstanceId": x.get("DestinationEndpoint").get("InstanceId"),
                        "DestinationEndpoint_InstanceType": x.get("DestinationEndpoint").get("InstanceType"),
                        "DestinationEndpoint_Region": x.get("DestinationEndpoint").get("Region"),
                        "DestinationEndpoint_EngineName": x.get("DestinationEndpoint").get("EngineName"),
                        "DestinationEndpoint_IP": x.get("DestinationEndpoint").get("IP"),
                        "DestinationEndpoint_Port": x.get("DestinationEndpoint").get("Port"),
                        "DestinationEndpoint_UserName": x.get("DestinationEndpoint").get("UserName"),
                        "DestinationEndpoint_OracleSID": x.get("DestinationEndpoint").get("OracleSID"),
                        "DestinationEndpoint_DatabaseName": x.get("DestinationEndpoint").get("DatabaseName"),
                    },
                    api_res.get("SynchronizationInstances", [])))
            break
        # log_strings.append(json.dumps(instance_info_list, indent=2, ensure_ascii=False))
        return instance_info_list

    def get_dts_migrate_instance(self, all_regions):
        instance_info_list = []
        for region_id in all_regions:
            # api不支持翻页，将pagesize设置足够大即可。
            try:
                status_code, api_res = self.aliyun.common("dts", Action="DescribeMigrationJobs", RegionId=region_id,
                                                          PageSize=100, )
                # log_strings.append(json.dumps(api_res, indent=2, ensure_ascii=False))
            except Exception as e:
                log_strings.append(str(e))

            instance_info_list = instance_info_list + list(map(
                lambda x: {
                    "instance_id": x.get("MigrationJobID"),
                    "instance_description": x.get("MigrationJobName"),
                    "instance_product": "dts",
                    "Status": x.get("MigrationJobStatus"),
                    "SourceEndpoint_InstanceId": x.get("SourceEndpoint").get("InstanceId"),
                    "SourceEndpoint_InstanceType": x.get("SourceEndpoint").get("InstanceType"),
                    "SourceEndpoint_Region": x.get("SourceEndpoint").get("Region"),
                    "SourceEndpoint_EngineName": x.get("SourceEndpoint").get("EngineName"),
                    "SourceEndpoint_IP": x.get("SourceEndpoint").get("IP"),
                    "SourceEndpoint_Port": x.get("SourceEndpoint").get("Port"),
                    "SourceEndpoint_UserName": x.get("SourceEndpoint").get("UserName"),
                    "SourceEndpoint_OracleSID": x.get("SourceEndpoint").get("OracleSID"),
                    "SourceEndpoint_DatabaseName": x.get("SourceEndpoint").get("DatabaseName"),
                    "DestinationEndpoint_InstanceId": x.get("DestinationEndpoint").get("InstanceId"),
                    "DestinationEndpoint_InstanceType": x.get("DestinationEndpoint").get("InstanceType"),
                    "DestinationEndpoint_Region": x.get("DestinationEndpoint").get("Region"),
                    "DestinationEndpoint_EngineName": x.get("DestinationEndpoint").get("EngineName"),
                    "DestinationEndpoint_IP": x.get("DestinationEndpoint").get("IP"),
                    "DestinationEndpoint_Port": x.get("DestinationEndpoint").get("Port"),
                    "DestinationEndpoint_UserName": x.get("DestinationEndpoint").get("UserName"),
                    "DestinationEndpoint_OracleSID": x.get("DestinationEndpoint").get("OracleSID"),
                    "DestinationEndpoint_DatabaseName": x.get("DestinationEndpoint").get("DatabaseName"),
                },
                api_res.get("MigrationJobs", {}).get("MigrationJob", [])
            ))
        # log_strings.append(json.dumps(instance_info_list, indent=2, ensure_ascii=False))
            break
        return instance_info_list


def startup(**kwargs):
    params = {
        'AccessKeyId': kwargs['AccessKeyId'],
        'AccessKeySecret': kwargs['AccessKeySecret'],
        'RoleName': kwargs['RoleName'],
    }
    # log_strings.append("开始连接阿里云")
    api = Custom()
    api.get_config(**params)
    # if kwargs['Region'] == 'all':
    #     all_region = api.get_describe_regions()
    # elif len(kwargs['Region'].split(',')):
    #     all_region = kwargs['Region'].split(',')
    # else:
    #     all_region = []
    #     exit()
    #     log_strings.append("请检查 Region 参数。")

    if kwargs["Product"] == 'all':
        products = (
            'slb', 'ecs', 'rds', 'polardb', 'redis', 'mongodb', 'drds', 'dts_sync', 'dts_migrate', 'rds_dbs',
            'polardb_dbs')
    elif len(kwargs["Product"].split(',')):
        products = kwargs['Product'].split(',')
    else:
        products = []
        exit()
        log_strings.append("请检查 Product 参数。")

    number_of_entry = len(products) + 1
    p_num = 1
    with progressbar.ProgressBar(max_value=number_of_entry) as bar:
        info = GetInfo()
        filter_info = info.get_info("aliyun", products)
        bar.update(p_num)
        # log_strings.append(json.dumps(filter_info, indent=2, ensure_ascii=False))
        # excel json 数据
        data = []
        data_topo = []
        for _info in filter_info:
            if _info["type"] == "slb":
                all_region = api.get_slb_describe_regions()
                _info["lines"] = api.get_slb_instance(all_region)
            elif _info["type"] == "ecs":
                all_region = api.get_ecs_describe_regions()
                _info["lines"] = api.get_ecs_instance(all_region)
            elif _info["type"] == "rds":
                all_region = api.get_rds_describe_regions()
                _info["lines"] = api.get_rds_instance(all_region)
            elif _info["type"] == "polardb":
                all_region = api.get_polardb_describe_regions()
                _info["lines"] = api.get_polardb_instance(all_region)
            # 增加数据库逻辑库
            elif _info["type"] == "rds_dbs":
                all_region = api.get_rds_describe_regions()
                _info["lines"] = api.get_rds_database(all_region)
            elif _info["type"] == "polardb_dbs":
                all_region = api.get_polardb_describe_regions()
                _info["lines"] = api.get_polardb_database(all_region)
            # 增加数据库逻辑库
            elif _info["type"] == "redis":
                all_region = api.get_redis_describe_regions()
                _info["lines"] = api.get_redis_instance(all_region)
            elif _info["type"] == "mongodb":
                all_region = api.get_mongodb_describe_regions()
                _info["lines"] = api.get_mongodb_instance(all_region)
            elif _info["type"] == "drds":
                all_region = api.get_drds_describe_regions()
                _info["lines"] = api.get_drds_instance(all_region)
            elif _info["type"] == "dts_sync":
                all_region = api.get_rds_describe_regions()
                _info["lines"] = api.get_dts_sync_instance(all_region)
            elif _info["type"] == "dts_migrate":
                all_region = api.get_rds_describe_regions()
                _info["lines"] = api.get_dts_migrate_instance(all_region)
            else:
                log_strings.append("暂不支持 {0} 类型资产".format(_info["type"]))
                _info["lines"] = []
            data.append(_info)
            data_topo.extend(_info["lines"])
            bar.update(p_num + 1)
        # log_strings.append(json.dumps(data, indent=2, ensure_ascii=False))

    # 渲染数据到json
    params_excel = {
        'file_name': "products",
        'dir_name': "history",
    }
    excel_api = ToExcel(**params_excel)
    for _data in data:
        excel_api.add_sheet(**_data)
    excel_path = excel_api.file_name
    excel_api.write_close()
    # print("******")
    # print(excel_path)

    # topo json 数据
    os_api = OSHelper()
    directory = os.getcwd()
    json_dir_name = "history"
    json_dir = os.path.join(directory, json_dir_name)
    os_api.mkdir(json_dir)
    json_file_name = '{0}-{1}.json'.format(now_date, str(uuid.uuid4()))
    path = os.path.join(json_dir, json_file_name)

    topo_api = ToTopo(data_topo)
    topo_json = topo_api.to_json()
    with open(path, mode='w', encoding='utf-8') as f:
        f.write(json.dumps(topo_json, indent=2, ensure_ascii=False))

    # 将json文件添加到js指定的文件中
    with open("static/js/json/{json_file_name}".format(json_file_name=json_file_name), mode='w',
              encoding='utf-8') as f:
        f.write(json.dumps(topo_json, indent=2, ensure_ascii=False))
    # 修改instances.js文件中的json文件名
    template_data = open("static/js/dynamic/instances_template.js", mode='r', encoding='utf-8').read()
    template = Template(template_data)
    j_params = {"json_file_name": json_file_name}
    with open("static/js/dynamic/instances.js".format(json_file_name=json_file_name), mode='w',
              encoding='utf-8') as f:
        f.write(template.render(**j_params))

    # 清理7天前的文件
    # 待补充

    # print(topo_json)
    # print(json.dumps(log_strings, indent=2, ensure_ascii=False))
    log_strings.append("后台运行结束")
    return excel_path, log_strings


if __name__ == "__main__":
    params = {
        'AccessKeyId': "xx",
        'AccessKeySecret': "xx",
        'RoleName': None,
        'Region': '',
        "Product": "ecs",
    }

    path, log_strings = startup(**params)
    print(path)
    print(log_strings)
