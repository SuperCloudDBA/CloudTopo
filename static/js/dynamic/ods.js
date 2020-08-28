$(document).ready(function(){
        var canvas = document.getElementById('Jtopo');
        canvas.height = window.innerHeight * 0.8;
        canvas.width = window.innerWidth * 0.78;
        var stage = new JTopo.Stage(canvas);
        //显示工具栏
        showJTopoToobar(stage);

        var scene = new JTopo.Scene(stage);
//        scene.background = 'img/bg.png';

        scene.alpha = 1;

        function addNode(text, product){
            var node = new JTopo.Node();
            node.setImage('img/aliyun_img_128/' + product +'.png', true);
            node.text = text;
            node.fontColor = '0,0,0';
            scene.add(node);
            return node;
        }

        function addLink(nodeA, nodeZ, text, direction){
            var link = new JTopo.FlexionalLink(nodeA, nodeZ, text, direction);
            link.direction = direction || 'horizontal'; //'vertical'
            //灰色线条
//            link.strokeColor = '204,204,204';
            link.strokeColor = '0,0,0';
            link.arrowsRadius = 10;
//            link.strokeColor = JTopo.util.randomColor(); // 线条颜色随机
            link.lineWidth = 2; // 线宽
            link.bundleOffset = 60; // 折线拐角处的长度
            link.bundleGap = 20; // 线条之间的间隔
            link.textOffsetY = 3; // 文本偏移量（向下3个像素）
            link.textColor = '0,0,0';
            scene.add(link);
            return link;
        }

        function addContainer(text){
            // 流式布局（水平、垂直间隔均为10)
            var flowLayout = JTopo.layout.FlowLayout(500, 500);

            // 网格布局(4行3列) 蓝色'0,123,255' 0,25,51
            var gridLayout = JTopo.layout.GridLayout(4, 3);
            var container = new JTopo.Container(text);
            container.textPosition = 'Middle_Center';
            //字体颜色
            container.fontColor = '0,123,255';
            //边框
            container.borderColor = '0,25,51';
            //填充背景色
            container.fillColor = '225,224,223';
            container.font = '14pt 微软雅黑';
//            container.borderColor = '0,123,255';
            container.borderRadius = 30; // 圆角
            scene.add(container);
            return container;
        }

        // 源端IDC机房
        var idc_container = addContainer('IDC机房');
        var rootNode_sqlserver = addNode('SQLServer', 'sqlserver');
        var rootNode_db2 = addNode('DB2', 'db2');
        idc_container.add(rootNode_sqlserver);
        idc_container.add(rootNode_db2);

        // 同步工具informatica
        var informatica_node = addNode('异构数据同步', 'informatica');


        //阿里金融云MySQL双机高可用架构
        var mysql_container =  addContainer('MySQL双机高可用');
        var slb_node = addNode('SLB', 'slb');
        mysql_container.add(slb_node);
        for(var j=0; j<2; j++){
           var thirdNode = addNode('MySQL节点' + j, 'mysql');
           addLink(slb_node, thirdNode, 'slb');
           mysql_container.add(thirdNode);
         }

        //DTS
        var dts_node = addNode('DTS同步链路', 'dts');
        //polardb
        var rds_node = addNode('PolarDB For MySQL', 'polardb');

        addLink(idc_container, informatica_node, '异构数据同步');
        addLink(informatica_node, mysql_container, '异构数据同步');
        addLink(mysql_container, dts_node,'dts同步');
        addLink(dts_node, rds_node,'dts同步');




        // 树形布局
        scene.doLayout(JTopo.layout.TreeLayout('down', 200, 107));
    });
