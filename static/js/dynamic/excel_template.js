$(document).ready(function() {

            var canvas = document.getElementById('Jtopo');
            canvas.height = window.innerHeight * 0.895;
            canvas.width = window.innerWidth * 0.978;

            var scene = new JTopo.Scene();
            var stage = new JTopo.Stage(canvas);
            showJTopoToobar(stage);
            var currentNode = null;
            var endNode = null;
            var tmpx = null;
            var tmpy = null;
            var validation = null;

//            服务器载入绘制拓扑图
            $.ajax({
                typt:"GET",
                url:"/static/js/json/{{ json_file_name }}",
                dataType:"json",
                success:function(data){
                    //业务容器
                    data.forEach(function(c){
                      if(c.elementType == "container" && c.level == 1){
                        yewu_container = addContainer(c.text);
                            //业务节点
                            data.forEach(function(b){
                                if(b.elementType == "node" && b.env == "all"  && b.project == c.text){
                                    node = AddNode(b.x, b.y, b.text, b.Image, b.textPosition, b.level);
                                    yewu_container.add(node);
                                }
                            }); //业务节点
                        //环境容器
                        data.forEach(function(a){
                            if(a.elementType == "container" && a.level==2){
                               container = addContainer(a.text);
                                    //普通节点
                                   data.forEach(function(b){
                                        //节点属于某个环境则创建节点加入业务容器，并加入对应的环境容器
                                        if(b.elementType == "node" && b.env == a.text && b.project == c.text){
                                          node = AddNode(b.x, b.y, b.text, b.Image, b.textPosition, b.level, b.instance_id);
                                          container.add(node);
                                          yewu_container.add(node);
                                        }
                                    });//普通节点
                            }

                        });//环境容器

                        }
                     });//业务容器


                    //不属于业务容器的节点
                    data.forEach(function(d){
                        if(d.elementType == "node" && d.env=='固定'){
                            node = AddNode(d.x, d.y, d.text, d.Image, d.textPosition, d.level, d.instance_id);
                            }
                    }); //不属于业务容器的节点


                    //画线
                    data.forEach(function(a){
                        if(a.elementType == "link"){
                            var nodeA = scene.findElements(function(e){return e.id == a.nodeAid;});
                            var nodeZ = scene.findElements(function(e){return e.id == a.nodeZid;});
                            if(nodeA[0] && nodeZ[0]) {
                                Addlink(nodeA[0], nodeZ[0], a.text, a.fontColor);
                            }
                        }
                    });//画线
                }
                });

            //画出拓扑图(函数)
            function addContainer(text){
//                var container = new JTopo.Container(text);
                var container = new JTopo.Container('');
                container.textPosition = 'Middle_Center';
                //字体颜色
                container.fontColor = '0,123,255';
                //边框
                container.borderColor = '0,25,51';
                //填充背景色
                container.fillColor = '225,224,223';
                container.font = '8pt 微软雅黑';
    //            container.borderColor = '0,123,255';
                container.borderRadius = 30; // 圆角
                scene.add(container);
                return container;
            }




            function AddNode(x, y, text, img, textPosition, level, alarm)
            {
                var node = new JTopo.Node(text);
                node.serializedProperties.push('id');
                node.serializedProperties.push('level');
                node.setLocation(x ,y);
                node.Image = '';
                node.id = x*y;
                node.level = level;
                if(null != img) {
                    node.setImage('/static/img/aliyun_img_45/' + img, true);
                    node.Image = img;
                }

                node.alarm = alarm;
                node.textPosition = textPosition;
                node.fontColor = '0,0,0';
                node.addEventListener('mouseup',function(event){
                    handler(event,node);//将当前事件的node赋给currentNode并显示右键菜单
                });
                node.addEventListener('click', function(event){
                    endNode = node;
                    if(null != currentNode && currentNode != endNode && validation === true){
                        strr = "";
                        Addlink(currentNode, endNode, strr);
                        currentNode = null;
                        validation = false;//验证是否在当前节点上右键点击了添加节点
                    }
                });

                scene.add(node);
                return node;
            }


            function Addlink(node1, node2, str, color)//-----增加折线------
            {
                var link = new JTopo.Link(node1, node2, str);
                //node2.father = node1;
                link.lineWidth = 3;//线宽
                link.dashedPattern = 2; // 虚线
                link.bundleOffset = 60;
                link.bundleGap = 20;
                link.textOffsetY = 3;
                link.arrowsRadius = 5; //箭头大小
                link.fontColor = color || '0, 200, 255';
                link.strokeColor = color || '0, 200, 255';
                link.addEventListener('mouseup',function(event){
                    currentLink = this;
                    handlelink(event);
                });
                scene.add(link);
            }

            function AddTextNode(x, y, str, scene)//加入单独的文字节点
            {
                var node = new JTopo.Node(str);
                node.setLocation(x, y);
                node.serializedProperties.push('id');
                node.id = x+y;
                node.fillColor = '255,255,255';
                node.textPosition = 'Middle_Center';
                node.fontColor = '0,0,0';
                node.setSize(120,30);
                node.dragable = false;
                node.showSelected = false;
                node.selected = false;
                scene.add(node);
            }

            function handler(event, obj) {//绑定右键菜单
                $("#linkmenu").hide();
                if (event.button == 2) {
                    currentNode = obj;
                    tmpx = event.pageX + 30;
                    tmpy = event.pageY + 30;
                    $("#contextmenu").css({
                        top: event.pageY,
                        left: event.pageX
                    }).show();
                    $("#contextmenu a").click(function(){
                        var text = $(this).text();
                          if (text == '添加连线'){
                            validation = true;//验证是否在当前节点上右键点击了添加节点
                 }
                 });
                }
            }

            function handlelink(event){
                $("#contextmenu").hide();
                if(event.button == 2){
                    $("#linkmenu").css({
                        top:event.pageY,
                        left:event.pageX
                    }).show();
                }
            }

             stage.click(function (event) {
                if (event.button == 0) {// 右键
                    // 关闭弹出菜单（div）
                    $("#contextmenu").hide();
                    $("#linkmenu").hide();
                    $("#uploadmenu").hide();
                }
            });

            //右键菜单处理
            $("#contextmenu a").click(function(){
                var text = $(this).text();
                if("取消" == text){
                    $("#contextmenu").hide();
                }if(text == '删除该节点'){
                    scene.remove(currentNode);
                    currentNode = null;
                    $("#contextmenu").hide();
                }
                    currentNode.save();

                 if (text == '添加连线'){

                 } else if(text == '添加节点'){
                    AddNode(tmpx, tmpy, currentNode.text, currentNode.Image,'Bottom_Center', currentNode.level,'');
                }else if(text == '顺时针旋转'){
                    currentNode.rotate += 0.5;
                }else if(text == '逆时针旋转'){
                    currentNode.rotate -= 0.5;
                }else if(text == '放大节点'){
                    currentNode.scaleX += 0.2;
                    currentNode.scaleY += 0.2;
                }else if(text == '缩小节点'){
                    currentNode.scaleX -= 0.2;
                    currentNode.scaleY -= 0.2;
                }else if(text == '警告')
                {
                    if(currentNode.alarm == null) {
                        currentNode.alarm = 'Alarm';
                    }else
                    {

                        currentNode.alarm = null;
                    }

                }else if(text == '查看实例详情')
                {
                    currentNode.alarm = "拓展功能待完善，可以查看节点详细属性";
                }
                $("#contextmenu").hide();
            });
            $("#linkmenu a").click(function(){
                var text = $(this).text();
                if("取消" == text){
                    $("#linkmenu").hide();
                }
                if(text == '修改颜色(随机)'){
                    //currentLink.fillColor = JTopo.util.randomColor();
                    currentLink.strokeColor = JTopo.util.randomColor();
                }
                else if(text == '改为黑色')
                {
                    currentLink.strokeColor = '0,0,0';//线路
                    currentLink.fontColor = '0,0,0';
                }
                else if(text == '改为红色')
                {
                    currentLink.strokeColor = '255,0,0';//线路
                    currentLink.text = "告警";
                    currentLink.fontColor = '255,0,0';
                }else if(text == '改为普通颜色')
                {
                    currentLink.strokeColor =  '0,200,255';
                }else if(text == '删除连线')
                {
                    scene.remove(currentLink);
                }
                $("#linkmenu").hide();
            });

            //修改文字
            var textfield = $("#jtopo_textfield");
            scene.dbclick(function(event){
                if(event.target == null) return;
                var e = event.target;
                textfield.css({
                    top: event.pageY,
                    left:event.pageX - e.width/2
                }).val(e.text).show().focus().select();
                console.log(textfield.val());
                e.text = "";
                textfield[0].JTopoNode = e;
            });
            $("#jtopo_textfield").blur(function(){
                textfield[0].JTopoNode.text = textfield.hide().val();
            });
            stage.add(scene);

            // 页面工具栏
            function showJTopoToobar(stage){
                // 工具栏按钮处理
                // 查询
                $('#findButton').click(function(){
                    var text = $('#findText').val().trim();
                    //var nodes = stage.find('node[text="'+text+'"]');
                    var scene = stage.childs[0];
                    var nodes = scene.childs.filter(function(e){
                        return e instanceof JTopo.Node;
                    });
                    nodes = nodes.filter(function(e){
                        if(e.text == null) return false;
                        return e.text.indexOf(text) != -1;
                    });

                    if(nodes.length > 0){
                        var node = nodes[0];
                        node.selected = true;
                        var location = node.getCenterLocation();
                        // 查询到的节点居中显示
                        stage.setCenter(location.x, location.y);

                        function nodeFlash(node, n){
                            if(n == 0) {
                                node.selected = false;
                                return;
                            };
                            node.selected = !node.selected;
                            setTimeout(function(){
                                nodeFlash(node, n-1);
                            }, 300);
                        }

                        // 闪烁几下
                        nodeFlash(node, 6);
                    }
                });

                $("input[name='modeRadio']").click(function(){
                    stage.mode = $("input[name='modeRadio']:checked").val();
                });
                $('#centerButton').click(function(){
                    stage.centerAndZoom(); //缩放并居中显示
                });
                $('#zoomOutButton').click(function(){//放大
                    stage.zoomOut();
                });
                $('#zoomInButton').click(function(){//缩小
                    stage.zoomIn();
                });
                $('#exportButton').click(function(){//保存PNG
                    stage.saveImageInfo();
                });
                $('#zoomCheckbox').click(function(){
                    if($('#zoomCheckbox').attr('checked')){
                        stage.wheelZoom = 0.85; // 设置鼠标缩放比例
                    }else{
                        stage.wheelZoom = null; // 取消鼠标缩放比例
                    }
                });
                $("#upLoadImage").click(function() {//载入节点
                    $("#uploadmenu").toggle();
                });
                $("#uploadmenu ul").on("click", "li",function(e){
                    var x = 10,y = 150;
                    var str = $(this).text();
                    var img = $(this).attr("id");
                    var textPosition = "Bottom_Center";
                    var level = 6;
                    AddNode(x, y, str, img, textPosition,level);
                });
                $("#contextmenu .nav4").on("click", "li", function(){//设置level
                    var lev = $(this).attr("id");
                    currentNode.level = lev;
                });
                $("#contextmenu .nav5").on("click", "li", function(){//设置文字位置
                    var tex = $(this).attr("id");
                    currentNode.textPosition = tex;
                });
                $("#contextmenu .nav6").on("click", "li", function(){//设置告警等级,动画,颜色
                    var ala = $(this).text();
                    var curr = currentNode;
                    var color = $(this).attr("id");
                    curr.alarm = ala;
                    /*var anima = setInterval(function(){
                        if(curr.alarm == ala){
                        curr.alarm = null;
                        }else{
                        curr.alarm = ala;
                        }
                    }, 600);*/
                    if(color == 11){
                        curr.alarmColor = '252, 233, 58';
                    }else if(color == 22){
                        curr.alarmColor = '255, 97, 0';
                    }else if(color == 33){
                        curr.alarmColor = '255, 0, 0';
                    }
                    console.log(curr.alarmColor);
                });
                $("#saveJsonStr").click(function(){//保存----大小，角度------非必须
                    var a = scene;
                    var d="[";
                            //d+='"scene":]';
                            for(var e=0;e< a.childs.length;e++){
                                var f= a.childs[e];
                                d+="{";
                                if(f.elementType == 'node')
                                {
                                    f.id = f.x * f.y;
                                    d += "\"elementType\":"+ '"'+f.elementType+'"';
                                    d += ",\"x\":"+ f.x;
                                    d += ",\"y\":"+ f.y;
                                    d += ",\"id\":"+ f.id;
                                    d += ",\"Image\":"+ '"'+ f.Image+ '"';
                                    d += ",\"text\":"+ '"'+ f.text+ '"';
                                    d +=",\"textPosition\":"+ '"'+ f.textPosition+ '"';
                                    d +=",\"alarm\":"+ '"'+ f.alarm+ '"';
                                    d +=",\"level\":"+ f.level;
                                }else if(f.elementType == 'container')
                                {
                                    f.id = f.x * f.y;
                                    d += "\"elementType\":"+ '"'+f.elementType+'"';
                                    d += ",\"x\":"+ f.x;
                                    d += ",\"y\":"+ f.y;
                                    d += ",\"text\":"+ '"'+ f.text+ '"';
                                    d +=",\"textPosition\":"+ '"'+ f.textPosition+ '"';
                                }else if(f.elementType == 'link'){
                                    d += "\"elementType\":"+ '"'+ f.elementType+ '"';
                                    d += ",\"nodeAid\":"+ f.nodeA.id;
                                    d += ",\"nodeZid\":"+ f.nodeZ.id;
                                    d += ",\"text\":"+ '"'+ f.text+ '"';
                                    d +=",\"fontColor\":"+ '"'+ f.fontColor+ '"';
                                }
                                d+="},";
                            }
                            d= d.substring(0, d.length-1);
                            d+="]";
                            d = d.replace("\r\n", "\\r\\n");
                            console.log(d);
                            alert("保存成功");
                });

            }

            var runPrefixMethod = function(element, method) {
                var usablePrefixMethod;
                ["webkit", "moz", "ms", "o", ""].forEach(function(prefix) {
                    if (usablePrefixMethod) return;
                    if (prefix === "") {
                        // 无前缀，方法首字母小写
                        method = method.slice(0,1).toLowerCase() + method.slice(1);
                    }
                    var typePrefixMethod = typeof element[prefix + method];
                    if (typePrefixMethod + "" !== "undefined") {
                        if (typePrefixMethod === "function") {
                            usablePrefixMethod = element[prefix + method]();
                        } else {
                            usablePrefixMethod = element[prefix + method];
                        }
                    }
                }
            );

            return usablePrefixMethod;
            };
        });
