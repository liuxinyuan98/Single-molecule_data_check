# Version 3.1.7
# 2022.8.13
# 本程序的功能为将电导的.tdms文件中的电导变化曲线全部显示出来，并以可滚动窗口的形式呈现出来。
# v 2.9.5 已完成2.9版本留下的所有任务，并加入当前已处理已处理的文件的功能（点击“处理完毕！点击查看文件列表”标签，进入）。接下来要加入鼠标拖动查看局部数据的功能。
# v 2.9.9 已完成二维热图的优化，添加部分人性化功能。但鼠标拖动查看局部数据的功能仍未实现。后面还要加入Ctrl+鼠标滚轮改变窗口中数据点个数（用乘法，成倍数地变化），并用鼠标滚轮滚动窗口；如果局部数据查看功能无法实现，可以用这个方法代替
# v 3.0.0 完成数据窗口用Ctrl+鼠标滚轮缩放功能，并加入多种缩放和滚动、精确滚动等人性化功能，不再实现局部窗口功能了。接下来优化一下pyplot的白边问题。
# v 3.0.1 优化了画图的Plot(start)子图的页边距
# v 3.0.5 1、优化绘图细节（字体大小、轴边距随窗口变化）。2、优化数据处理细节。3、优化图像缩放、滚动细节。4、修复少量bug
# v 3.0.6 修复进度条显示bug
# v 3.0.8 1、修复部分显示遮挡。2、修复保存文件时命名的bug——当储存的路径中含有文件夹时，文件搜寻新编号的功能会出现问题。找到的原因是os.walk()函数会将该路径下的最后一个子文件夹的中的文件都遍历一遍，所以导致了问题。解决方案：将os.walk()中的topdown=False，这样就不会去找子文件夹了。3、修复二维热图bug
# v 3.1.0 1、为热图程序添加，绘制电导一维图的功能（本质是将二维图的数据映射给它），2、改变窗口的图标
# v 3.1.1 为一维图添加标尺
# v 3.1.5 1、修复全局图中右坐标出现左坐标轴刻度线的显示问题；2、修复参数修改窗口的问题：①固定窗口大小，②修改颜色若不填写就确认虽然有原始文本，但还是会报错（在IDE中没有问题，但是打包的程序有问题，可能出在打包的过程中）；3、主界面加载和处理显示进度条；4、显示程序正在启动（应该是在pyinstaller中实现，但是我没找到解决方案）；5、解决文件处理过程中窗口卡住的问题，一开始用threading多线程解决，发现会出现绘图在数据处理之前而程序出错的问题，然后使用threading.lock和join等方案，这样直接就让数据读取函数停止工作了（至于为什么，我还没有找到答案）。最后还是用window.update()函数，让窗口直接进入下个循环才解决这个窗口卡死的问题，也就是说原本的数据处理和绘图的顺序和逻辑依然不变。当然，只是解决了窗口拖动的问题，但窗口中的内容仍然无法使用
# v 3.1.6 1、给processData(channelIdx)公式添加索引的功能；2、优化数据处理函数；3、优化Plot(start)函数中当uplimit==downlimit时会出现的bug。
# v 3.1.7 加入自动滚动窗口的功能

# 未来把Python的面向对象学彻底，把一些模块打包，减小工作量

import numpy as np
from matplotlib import pyplot as plt
from nptdms import TdmsFile
from tkinter import filedialog as fd
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog as sd
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import configparser
import math
from mpl_toolkits.axisartist.parasite_axes import HostAxes, ParasiteAxes
from matplotlib.pyplot import MultipleLocator
import sys
import time



def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)



##### 提前创建窗口
window = tk.Tk()
window.title("多通道电导全图查看器V3.1.7")
window.geometry('1220x740')
try:
    window.iconbitmap(get_resource_path("icon.ico"))
except:
    pass


#############################################  全局变量区  ##############################################

# 实验测试相关参数
biasVoltage = 0.1               # 偏压默认为0.1 V

# 四参数盒子的拟合参数
FitPara_a1 = 3.0362                  # 对数放大器在正偏压下的拟合参数a1
FitPara_b1 = -13.642                 # 对数放大器在正偏压下的拟合参数b1
FitPara_a2 = -2.9609                 # 对数放大器在负偏压下的拟合参数a2
FitPara_b2 = -13.502                 # 对数放大器在负偏压下的拟合参数b2

# 九参数盒子的拟合参数
FitPara_na1 = 9.5882
FitPara_nb1 = -23.6098
FitPara_nc1 = 1.187e-11
FitPara_nd1 = 5.66361e-11
FitPara_na2 = -9.2337
FitPara_nb2 = -23.612
FitPara_nc2 = -4.1549e-10
FitPara_nd2 = -6.9759e-11
FitPara_ne = 0.02

# 数据处理与绘图设置
Data1_name = 'Conductance / log(G/G0)'
Data1_process = True
Data1_show = True
Data1_type = '四参数放大器输出转log(G/G0)'
Data1_color = 'red'
Data1_uplimit = 1
Data1_downlimit = -7
Data1_limitauto = False
Data1_formula = ''
Data1_grid = True
Data1_grid_color = 'Pink'

Data2_name = ' '
Data2_process = False
Data2_show = False
Data2_type = '原始数据'
Data2_color = '#2B579A'
Data2_uplimit = 1
Data2_downlimit = 0
Data2_limitauto = False
Data2_formula = ''
Data2_grid = False
Data2_grid_color = 'SkyBlue'

Data3_name = ' '
Data3_process = False
Data3_show = False
Data3_type = '原始数据'
Data3_color = 'green'
Data3_uplimit = 1
Data3_downlimit = 0
Data3_limitauto = False
Data3_formula = ''
Data3_grid = False
Data3_grid_color = 'LightGreen'

Data4_name = ' '
Data4_process = False
Data4_show = False
Data4_type = '原始数据'
Data4_color = 'orange'
Data4_uplimit = 1
Data4_downlimit = 0
Data4_limitauto = False
Data4_formula = ''
Data4_grid = False
Data4_grid_color = 'Yellow'

IniParaNameList = ('biasVoltage',
                   'FitPara_a1', 'FitPara_b1', 'FitPara_a2', 'FitPara_b2',
                   'FitPara_na1', 'FitPara_nb1', 'FitPara_nc1', 'FitPara_nd1', 'FitPara_na2', 'FitPara_nb2', 'FitPara_nc2', 'FitPara_nd2', 'FitPara_ne',
                   'Data1_name','Data1_process','Data1_show','Data1_type','Data1_color','Data1_uplimit','Data1_downlimit','Data1_limitauto','Data1_formula','Data1_grid','Data1_grid_color',
                   'Data2_name','Data2_process','Data2_show','Data2_type','Data2_color','Data2_uplimit','Data2_downlimit','Data2_limitauto','Data2_formula','Data2_grid','Data2_grid_color',
                   'Data3_name','Data3_process','Data3_show','Data3_type','Data3_color','Data3_uplimit','Data3_downlimit','Data3_limitauto','Data3_formula','Data3_grid','Data3_grid_color',
                   'Data4_name','Data4_process','Data4_show','Data4_type','Data4_color','Data4_uplimit','Data4_downlimit','Data4_limitauto','Data4_formula','Data4_grid','Data4_grid_color',
                   )    # 将ini文件中的所有参数名称记录下来，方便后面的读取和保存操作
IniParaList = []        # 将参数变量名变成参数变量
for IniParaName in IniParaNameList:
    IniParaList.append(locals()[IniParaName])

# 显示图像相关
ShowDataLength = 20000              # 窗口视图中要显示的数据点个数
CurrentStartIdx = -1                 # 当前图像起始的数据点位置
PlotType = tk.IntVar()              # 用来记录用户选择的绘图类型：0-折线图、1-散点图 等。
PlotType.set(0)                     # 默认画折线图

# 文件相关
FileList = []
CurrentSaveFolder = ''              # 当前保存页面
CurrentFileIdx = 0                  # 当前文件的

# 电导曲线数据相关
Data1 = np.array([])
Data2 = np.array([])
Data3 = np.array([])
Data4 = np.array([])
DataLength = 0          # 所有的电导数据长度

SliderPrecion = 4000    # 滑块滑动精度

# 窗口的长宽，并影响绘图的大小
window_size_width = 1225
window_size_height = 740

# 色表
colorsTable = '''#FFB6C1 LightPink 浅粉红
#FFC0CB Pink 粉红
#DC143C Crimson 深红/猩红
#FFF0F5 LavenderBlush 淡紫红
#DB7093 PaleVioletRed 弱紫罗兰红
#FF69B4 HotPink 热情的粉红
#FF1493 DeepPink 深粉红
#C71585 MediumVioletRed 中紫罗兰红
#DA70D6 Orchid 暗紫色/兰花紫
#D8BFD8 Thistle 蓟色
#DDA0DD Plum 洋李色/李子紫
#EE82EE Violet 紫罗兰
#FF00FF Magenta 洋红/玫瑰红
#FF00FF Fuchsia 紫红/灯笼海棠
#8B008B DarkMagenta 深洋红
#800080 Purple 紫色
#BA55D3 MediumOrchid 中兰花紫
#9400D3 DarkViolet 暗紫罗兰
#9932CC DarkOrchid 暗兰花紫
#4B0082 Indigo 靛青/紫兰色
#8A2BE2 BlueViolet 蓝紫罗兰
#9370DB MediumPurple 中紫色
#7B68EE MediumSlateBlue 中暗蓝色/中板岩蓝
#6A5ACD SlateBlue 石蓝色/板岩蓝
#483D8B DarkSlateBlue 暗灰蓝色/暗板岩蓝
#E6E6FA Lavender 淡紫色/熏衣草淡紫
#F8F8FF GhostWhite 幽灵白
#0000FF Blue 纯蓝
#0000CD MediumBlue 中蓝色
#191970 MidnightBlue 午夜蓝
#00008B DarkBlue 暗蓝色
#000080 Navy 海军蓝
#4169E1 RoyalBlue 皇家蓝/宝蓝
#6495ED CornflowerBlue 矢车菊蓝
#B0C4DE LightSteelBlue 亮钢蓝
#778899 LightSlateGray 亮蓝灰/亮石板灰
#708090 SlateGray 灰石色/石板灰
#1E90FF DodgerBlue 闪兰色/道奇蓝
#F0F8FF AliceBlue 爱丽丝蓝
#4682B4 SteelBlue 钢蓝/铁青
#87CEFA LightSkyBlue 亮天蓝色
#87CEEB SkyBlue 天蓝色
#00BFFF DeepSkyBlue 深天蓝
#ADD8E6 LightBlue 亮蓝
#B0E0E6 PowderBlue 粉蓝色/火药青
#5F9EA0 CadetBlue 军兰色/军服蓝
#F0FFFF Azure 蔚蓝色
#E0FFFF LightCyan 淡青色
#AFEEEE PaleTurquoise 弱绿宝石
#00FFFF Cyan 青色
#00FFFF Aqua 浅绿色/水色
#00CED1 DarkTurquoise 暗绿宝石
#2F4F4F DarkSlateGray 暗瓦灰色/暗石板灰
#008B8B DarkCyan 暗青色
#008080 Teal 水鸭色
#48D1CC MediumTurquoise 中绿宝石
#20B2AA LightSeaGreen 浅海洋绿
#40E0D0 Turquoise 绿宝石
#7FFFD4 Aquamarine 宝石碧绿
#66CDAA MediumAquamarine 中宝石碧绿
#00FA9A MediumSpringGreen 中春绿色
#F5FFFA MintCream 薄荷奶油
#00FF7F SpringGreen 春绿色
#3CB371 MediumSeaGreen 中海洋绿
#2E8B57 SeaGreen 海洋绿
#F0FFF0 Honeydew 蜜色/蜜瓜色
#90EE90 LightGreen 淡绿色
#98FB98 PaleGreen 弱绿色
#8FBC8F DarkSeaGreen 暗海洋绿
#32CD32 LimeGreen 闪光深绿
#00FF00 Lime 闪光绿
#228B22 ForestGreen 森林绿
#008000 Green 纯绿
#006400 DarkGreen 暗绿色
#7FFF00 Chartreuse 黄绿色/查特酒绿
#7CFC00 LawnGreen 草绿色/草坪绿
#ADFF2F GreenYellow 绿黄色
#556B2F DarkOliveGreen 暗橄榄绿
#9ACD32 YellowGreen 黄绿色
#6B8E23 OliveDrab 橄榄褐色
#F5F5DC Beige 米色/灰棕色
#FAFAD2 LightGoldenrodYellow 亮菊黄
#FFFFF0 Ivory 象牙色
#FFFFE0 LightYellow 浅黄色
#FFFF00 Yellow 纯黄
#808000 Olive 橄榄
#BDB76B DarkKhaki 暗黄褐色/深卡叽布
#FFFACD LemonChiffon 柠檬绸
#EEE8AA PaleGoldenrod 灰菊黄/苍麒麟色
#F0E68C Khaki 黄褐色/卡叽布
#FFD700 Gold 金色
#FFF8DC Cornsilk 玉米丝色
#DAA520 Goldenrod 金菊黄
#B8860B DarkGoldenrod 暗金菊黄
#FFFAF0 FloralWhite 花的白色
#FDF5E6 OldLace 老花色/旧蕾丝
#F5DEB3 Wheat 浅黄色/小麦色
#FFE4B5 Moccasin 鹿皮色/鹿皮靴
#FFA500 Orange 橙色
#FFEFD5 PapayaWhip 番木色/番木瓜
#FFEBCD BlanchedAlmond 白杏色
#FFDEAD NavajoWhite 纳瓦白/土著白
#FAEBD7 AntiqueWhite 古董白
#D2B48C Tan 茶色
#DEB887 BurlyWood 硬木色
#FFE4C4 Bisque 陶坯黄
#FF8C00 DarkOrange 深橙色
#FAF0E6 Linen 亚麻布
#CD853F Peru 秘鲁色
#FFDAB9 PeachPuff 桃肉色
#F4A460 SandyBrown 沙棕色
#D2691E Chocolate 巧克力色
#8B4513 SaddleBrown 重褐色/马鞍棕色
#FFF5EE Seashell 海贝壳
#A0522D Sienna 黄土赭色
#FFA07A LightSalmon 浅鲑鱼肉色
#FF7F50 Coral 珊瑚
#FF4500 OrangeRed 橙红色
#E9967A DarkSalmon 深鲜肉/鲑鱼色
#FF6347 Tomato 番茄红
#FFE4E1 MistyRose 浅玫瑰色/薄雾玫瑰
#FA8072 Salmon 鲜肉/鲑鱼色
#FFFAFA Snow 雪白色
#F08080 LightCoral 淡珊瑚色
#BC8F8F RosyBrown 玫瑰棕色
#CD5C5C IndianRed 印度红
#FF0000 Red 纯红
#A52A2A Brown 棕色
#B22222 FireBrick 火砖色/耐火砖
#8B0000 DarkRed 深红色
#800000 Maroon 栗色
#FFFFFF White 纯白
#F5F5F5 WhiteSmoke 白烟
#DCDCDC Gainsboro 淡灰色
#D3D3D3 LightGrey 浅灰色
#C0C0C0 Silver 银灰色
#A9A9A9 DarkGray 深灰色
#808080 Gray 灰色
#696969 DimGray 暗淡灰
#000000 Black 纯黑'''

#########################################################################################################

########################################    参数初始化区   #################################################

ParaConf = configparser.ConfigParser()
if os.path.exists('CheckAllDataParameters.ini'):    # 如果配置文件存在，就读取配置文件的内容
    try:
        ParaConf.read('CheckAllDataParameters.ini',encoding='utf-8')
        for IniParaName in IniParaNameList:
            if ParaConf.get('Parameters',IniParaName) == 'True':      # 注意ini文件中的值不会记录bool值，它只会记录字符串！所以一定要这么写。
                globals()[IniParaName] = True
            elif ParaConf.get('Parameters',IniParaName) == 'False':
                globals()[IniParaName] = False
            else:
                try:
                    globals()[IniParaName] = float(ParaConf.get('Parameters',IniParaName))      # 还有，不要忘记把数字类的字符串转变成数字
                except:
                    globals()[IniParaName] = ParaConf.get('Parameters',IniParaName)
    except:
        messagebox.showwarning("错误","配置文件CheckAllDataParameters.ini内部错误，请删除后该配置文件后重新运行程序！")
else:                                               # 如果不存在，就新建需要的结点
    ParaConf.add_section('Parameters')


#########################################################################################################

########################################    GUI主函数区   #################################################

######################### 拟合参数窗口 #########################
def ParatersModifyWindow():
    global biasVoltage, \
           FitPara_a1, FitPara_b1, FitPara_a2, FitPara_b2,\
           FitPara_na1, FitPara_nb1, FitPara_nc1, FitPara_nd1, FitPara_na2, FitPara_nb2, FitPara_nc2, FitPara_nd2, FitPara_ne, \
           Data1_name, Data1_process, Data1_show, Data1_type, Data1_color, Data1_uplimit, Data1_downlimit, Data1_limitauto, Data1_formula, Data1_grid, Data1_grid_color, \
           Data2_name, Data2_process, Data2_show, Data2_type, Data2_color, Data2_uplimit, Data2_downlimit, Data2_limitauto, Data2_formula, Data2_grid, Data2_grid_color, \
           Data3_name, Data3_process, Data3_show, Data3_type, Data3_color, Data3_uplimit, Data3_downlimit, Data3_limitauto, Data3_formula, Data3_grid, Data3_grid_color, \
           Data4_name, Data4_process, Data4_show, Data4_type, Data4_color, Data4_uplimit, Data4_downlimit, Data4_limitauto, Data4_formula, Data4_grid, Data4_grid_color

    ParametersWindow = tk.Tk()
    ParametersWindow.title("参数设置")
    ParametersWindow.geometry('1020x600')
    ParametersWindow.resizable(width=0, height=0)


    ##### 修改放大器拟合参数

    # 说明1
    def PromptInfomation1():
        messagebox.showinfo("拟合参数修改说明",
                            "1、四参数放大器：正偏压拟合参数a1和b1，负偏压拟合参数a2和b2。"
                            "\n2、九参数放大器：放大器输出>ne时，使用na1,nb1,nc1,nd1；放大器输出<ne时，使用na2,nb2,nc2,nd2；ne为判别参数。"
                            "\n3、确认当前输入框的内容：使用“Enter”键盘按键、鼠标右键或点击其它的输入框，如果内容不符合输入要求会出现报错提示，并复原。"
                            "\n4、新输入的配置都是临时的，若想保存当前的配置，方便下次使用，可在关闭当前窗口后，选择确定保存当前配置于配置文件中，即可在下次启动程序时自动加载配置。",
                            master=ParametersWindow)
    tk.Button(ParametersWindow, bg='Honeydew', text="说明1", font=('黑体', 12), width=6, height=1, command=PromptInfomation1).place(x=980, y=20, anchor='center')

    ##### 拟合参数框架
    frame_FitPara = tk.Frame(ParametersWindow,width=600,height=150)
    frame_FitPara.place(x=100, y=0, anchor='nw')
    ### 四参数
    # a1
    tk.Label(frame_FitPara, height=1, text='a1').place(x=50, y=35, anchor='center')
    entry_FitPara_a1 = tk.Entry(frame_FitPara, width=10, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_a1','FitPara_a1'))
    entry_FitPara_a1.insert(0,str(FitPara_a1))
    entry_FitPara_a1.place(x=100, y=35, anchor='center')
    # b1
    tk.Label(frame_FitPara, height=1, text='b1').place(x=150, y=35, anchor='center')
    entry_FitPara_b1 = tk.Entry(frame_FitPara, width=10, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_b1','FitPara_b1'))
    entry_FitPara_b1.insert(0, str(FitPara_b1))
    entry_FitPara_b1.place(x=200, y=35, anchor='center')
    # a2
    tk.Label(frame_FitPara, height=1, text='a2').place(x=50, y=60, anchor='center')
    entry_FitPara_a2 = tk.Entry(frame_FitPara, width=10, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_a2','FitPara_a2'))
    entry_FitPara_a2.insert(0, str(FitPara_a2))
    entry_FitPara_a2.place(x=100, y=60, anchor='center')
    # b2
    tk.Label(frame_FitPara, height=1, text='b2').place(x=150, y=60, anchor='center')
    entry_FitPara_b2 = tk.Entry(frame_FitPara, width=10, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_b2','FitPara_b2'))
    entry_FitPara_b2.insert(0, str(FitPara_b2))
    entry_FitPara_b2.place(x=200, y=60, anchor='center')


    ### 九参数
    # na1
    tk.Label(frame_FitPara, height=1, text='na1').place(x=55, y=95, anchor='center')
    entry_FitPara_na1 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_na1','FitPara_na1'))
    entry_FitPara_na1.insert(0, str(FitPara_na1))
    entry_FitPara_na1.place(x=115, y=95, anchor='center')
    # nb1
    tk.Label(frame_FitPara, height=1, text='nb1').place(x=175, y=95, anchor='center')
    entry_FitPara_nb1 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_nb1','FitPara_nb1'))
    entry_FitPara_nb1.insert(0, str(FitPara_nb1))
    entry_FitPara_nb1.place(x=235, y=95, anchor='center')
    # nc1
    tk.Label(frame_FitPara, height=1, text='nc1').place(x=295, y=95, anchor='center')
    entry_FitPara_nc1 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_nc1','FitPara_nc1'))
    entry_FitPara_nc1.insert(0, str(FitPara_nc1))
    entry_FitPara_nc1.place(x=355, y=95, anchor='center')
    # nd1
    tk.Label(frame_FitPara, height=1, text='nd1').place(x=415, y=95, anchor='center')
    entry_FitPara_nd1 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_nd1','FitPara_nd1'))
    entry_FitPara_nd1.insert(0,str(FitPara_nd1))
    entry_FitPara_nd1.place(x=475, y=95, anchor='center')
    # na2
    tk.Label(frame_FitPara, height=1, text='na2').place(x=55, y=120, anchor='center')
    entry_FitPara_na2 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_na2','FitPara_na2'))
    entry_FitPara_na2.insert(0, str(FitPara_na2))
    entry_FitPara_na2.place(x=115, y=120, anchor='center')
    # nb2
    tk.Label(frame_FitPara, height=1, text='nb2').place(x=175, y=120, anchor='center')
    entry_FitPara_nb2 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_nb2','FitPara_nb2'))
    entry_FitPara_nb2.insert(0, str(FitPara_nb2))
    entry_FitPara_nb2.place(x=235, y=120, anchor='center')
    # nc2
    tk.Label(frame_FitPara, height=1, text='nc2').place(x=295, y=120, anchor='center')
    entry_FitPara_nc2 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_nc2','FitPara_nc2'))
    entry_FitPara_nc2.insert(0, str(FitPara_nc2))
    entry_FitPara_nc2.place(x=355, y=120, anchor='center')
    # nd2
    tk.Label(frame_FitPara, height=1, text='nd2').place(x=415, y=120, anchor='center')
    entry_FitPara_nd2 = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_nd2','FitPara_nd2'))
    entry_FitPara_nd2.insert(0, str(FitPara_nd2))
    entry_FitPara_nd2.place(x=475, y=120, anchor='center')
    # ne
    tk.Label(frame_FitPara, height=1, text='ne').place(x=535, y=95, anchor='center')
    entry_FitPara_ne = tk.Entry(frame_FitPara, width=12, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_FitPara_ne','FitPara_ne'))
    entry_FitPara_ne.insert(0, str(FitPara_ne))
    entry_FitPara_ne.place(x=595, y=95, anchor='center')

    ### 标题
    tk.Label(ParametersWindow, height=1, font=('黑体', 12), text="放大器拟合参数（请在处理文件前完成该部分设置）：").place(x=1, y=1, anchor='nw')
    tk.Label(ParametersWindow, height=1, font=('黑体', 11), text="四参数拟合参数").place(x=20, y=37, anchor='nw')
    tk.Label(ParametersWindow, height=1, font=('黑体', 11), text="九参数拟合参数").place(x=20, y=97, anchor='nw')

    ##### 分割线1 ————————————————————————————————————————
    tk.Canvas(ParametersWindow, bg='DarkGray', height=1, width=760).place(x=20, y=140, anchor='nw')

    ##### 数据处理参数设置
    tk.Label(ParametersWindow, height=1, font=('黑体',12), text="数据处理设置（请在处理文件前完成该部分设置）：").place(x=1, y=150, anchor='nw')
    Options = ["四参数放大器输出转log(G/G0)","九参数放大器输出转log(G/G0)","原始数据","公式"]

    ### 数据处理参数设置技巧与提示
    def PromptInfomation2():
        messagebox.showinfo("数据处理参数设置技巧与提示",
                            "公式使用说明：通过键入Python或numpy(np)库或math库中的公式表达式实现对四个通道数据(Data1~4)的处理。支持一般表达式和索引表达式"
                            "\ne.g.1 一般表达式：在数据1的公式栏中键入公式：“np.log10(((Data1**2+1)//3*Data4-5)/6)”，则处理后的数据1变成：其原始数据的平方加1后整除3，之后乘上对应的数据，减5，再除以6，最后以10为底数取对数。"
                            "\ne.g.2 索引表达式：若Data1为偏压，Data2位电流，在Data3的公式栏中键入：“(Data2[i]-Data2[i-1])/(Data1[i]-Data1[i-1])”，可以求微分电导。"
                            "\ne.g.3 索引表达式：在Data的公式栏中键入：“np.mean(Data1[i:i+50])”，可以实现窗口为50个数据点的均值滤波。",
                            master=ParametersWindow)
    tk.Button(ParametersWindow,bg='Honeydew',text="说明2",font=('黑体',12),width=6,height=1,command=PromptInfomation2).place(x=980,y=165,anchor='center')

    ### 偏压设置
    tk.Label(ParametersWindow, height=1, text='偏压：').place(x=710, y=175, anchor='center')
    tk.Label(ParametersWindow, height=1, text='V').place(x=780, y=175, anchor='center')
    entry_biasVoltage = tk.Entry(ParametersWindow, width=6, justify='right', validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_biasVoltage','biasVoltage'))
    entry_biasVoltage.insert(0, str(biasVoltage))
    entry_biasVoltage.place(x=750, y=175, anchor='center')

    ### 字段1：数据处理开关
    tk.Label(ParametersWindow,text="勾选要读取和处理的\ntdms文件数据通道",height=2,font=('黑体',11)).place(x=100,y=190,anchor='center')
    # Data1
    Data1_process_tk = tk.BooleanVar(ParametersWindow,Data1_process)
    def Data1_Checkbutton():
        global Data1_process,Data1_show
        Data1_process = Data1_process_tk.get()
        Data1_show = Data1_process_tk.get()
    tk.Checkbutton(ParametersWindow, text="Data Channel 1", font=('Arial',12),variable=Data1_process_tk, onvalue=True, offvalue=False,command=Data1_Checkbutton).place(x=100,y=230,anchor='center')
    # Data2
    Data2_process_tk = tk.BooleanVar(ParametersWindow,Data2_process)
    def Data2_Checkbutton():
        global Data2_process,Data2_show
        Data2_process = Data2_process_tk.get()
        Data2_show = Data2_process_tk.get()
    tk.Checkbutton(ParametersWindow, text="Data Channel 2", font=('Arial',12),variable=Data2_process_tk, onvalue=True, offvalue=False,command=Data2_Checkbutton).place(x=100,y=280,anchor='center')
    # Data3
    Data3_process_tk = tk.BooleanVar(ParametersWindow, Data3_process)
    def Data3_Checkbutton():
        global Data3_process,Data3_show
        Data3_process = Data3_process_tk.get()
        Data3_show = Data3_process_tk.get()
    tk.Checkbutton(ParametersWindow, text="Data Channel 3", font=('Arial',12), variable=Data3_process_tk, onvalue=True, offvalue=False,command=Data3_Checkbutton).place(x=100, y=330, anchor='center')
    # Data4
    Data4_process_tk = tk.BooleanVar(ParametersWindow, Data4_process)
    def Data4_Checkbutton():
        global Data4_process,Data4_show
        Data4_process = Data4_process_tk.get()
        Data4_show = Data4_process_tk.get()
    tk.Checkbutton(ParametersWindow, text="Data Channel 4", font=('Arial',12), variable=Data4_process_tk, onvalue=True, offvalue=False,command=Data4_Checkbutton).place(x=100, y=380, anchor='center')

    ### 字段2：数据处理类型选项
    tk.Label(ParametersWindow,  text="数据读取后如何处理", height=2,font=('黑体',11)).place(x=300,y=190,anchor='center')
    # Data1
    Data1_type_tk = tk.StringVar(ParametersWindow,Data1_type)
    def Data1_OptionMenu(value):
        global Data1_type
        Data1_type = value
        NextParaNeedFill('Data1',230)
    opt_Data1 = tk.OptionMenu(ParametersWindow, Data1_type_tk, *Options, command=Data1_OptionMenu)
    opt_Data1.config(width=24,bg='white',height=2)
    opt_Data1.place(x=300,y=230,anchor='center')
    # Data2
    Data2_type_tk = tk.StringVar(ParametersWindow,Data2_type)
    def Data2_OptionMenu(value):
        global Data2_type
        Data2_type = value
        NextParaNeedFill('Data2',280)
    opt_Data2 = tk.OptionMenu(ParametersWindow, Data2_type_tk, *Options, command=Data2_OptionMenu)
    opt_Data2.config(width=24,bg='white',height=2)
    opt_Data2.place(x=300,y=280,anchor='center')
    # Data3
    Data3_type_tk = tk.StringVar(ParametersWindow,Data3_type)
    def Data3_OptionMenu(value):
        global Data3_type
        Data3_type = value
        NextParaNeedFill('Data3',330)
    opt_Data3 = tk.OptionMenu(ParametersWindow, Data3_type_tk, *Options, command=Data3_OptionMenu)
    opt_Data3.config(width=24,bg='white',height=2)
    opt_Data3.place(x=300,y=330,anchor='center')
    # Data4
    Data4_type_tk = tk.StringVar(ParametersWindow,Data4_type)
    def Data4_OptionMenu(value):
        global Data4_type
        Data4_type = value
        NextParaNeedFill('Data4',380)
    opt_Data4 = tk.OptionMenu(ParametersWindow, Data4_type_tk, *Options, command=Data4_OptionMenu)
    opt_Data4.config(width=24,bg='white',height=2)
    opt_Data4.place(x=300,y=380,anchor='center')


    ### 字段3：后面的参数
    # Data1
    label_Data1_keepBias = tk.Label(ParametersWindow, text="恒偏压模式")
    label_Data1_formula = tk.Label(ParametersWindow, text="输入公式：")
    entry_Data1_formula = tk.Entry(ParametersWindow, width=40, validate="focusout", validatecommand=lambda :entry_getString('entry_Data1_formula','Data1_formula'))
    entry_Data1_formula.insert(0,str(Data1_formula))
    # Data2
    label_Data2_keepBias = tk.Label(ParametersWindow, text="恒偏压模式")
    label_Data2_formula = tk.Label(ParametersWindow, text="输入公式：")
    entry_Data2_formula = tk.Entry(ParametersWindow, width=40, validate="focusout", validatecommand=lambda :entry_getString('entry_Data2_formula','Data2_formula'))
    entry_Data2_formula.insert(0,str(Data2_formula))
    # Data3
    label_Data3_keepBias = tk.Label(ParametersWindow, text="恒偏压模式")
    label_Data3_formula = tk.Label(ParametersWindow, text="输入公式：")
    entry_Data3_formula = tk.Entry(ParametersWindow, width=40, validate="focusout", validatecommand=lambda :entry_getString('entry_Data3_formula','Data3_formula'))
    entry_Data3_formula.insert(0,str(Data3_formula))
    # Data4
    label_Data4_keepBias = tk.Label(ParametersWindow, text="恒偏压模式")
    label_Data4_formula = tk.Label(ParametersWindow, text="输入公式：")
    entry_Data4_formula = tk.Entry(ParametersWindow, width=40, validate="focusout", validatecommand=lambda :entry_getString('entry_Data4_formula','Data4_formula'))
    entry_Data4_formula.insert(0,str(Data4_formula))

    BaseVarDict = locals()
    def NextParaNeedFill(DataName,yPosition):
        nonlocal BaseVarDict
        if globals()[DataName+'_type']=="四参数放大器输出转log(G/G0)" or globals()[DataName+'_type']=="九参数放大器输出转log(G/G0)" :
            BaseVarDict['label_'+DataName+'_keepBias'].place(x=450,y=yPosition,anchor='center')
            BaseVarDict['label_'+DataName+'_formula'].place_forget()
            BaseVarDict['entry_' + DataName + '_formula'].place_forget()
        elif globals()[DataName+'_type']=="公式":
            BaseVarDict['label_'+DataName+'_keepBias'].place_forget()
            BaseVarDict['label_'+DataName+'_formula'].place(x=450,y=yPosition,anchor='center')
            BaseVarDict['entry_' + DataName + '_formula'].place(x=620, y=yPosition, anchor='center')
        else:
            BaseVarDict['label_'+DataName+'_keepBias'].place_forget()
            BaseVarDict['label_'+DataName+'_formula'].place_forget()
            BaseVarDict['entry_' + DataName + '_formula'].place_forget()

    # 一开始的时候初始化显示后面的参数
    NextParaNeedFill('Data1',230)
    NextParaNeedFill('Data2', 280)
    NextParaNeedFill('Data3', 330)
    NextParaNeedFill('Data4', 380)



    # 分割线2  ————————————————————————————————————————————————————
    tk.Canvas(ParametersWindow, bg='DarkGray', height=1, width=850).place(x=20, y=410, anchor='nw')
    ##### 图像显示参数配置
    tk.Label(ParametersWindow, height=1, font=('黑体', 13), text="图像显示参数配置：").place(x=1, y=420, anchor='nw')
    ### 图像参数配置技巧与提示
    def PromptInfomation3():
        messagebox.showinfo("图像显示参数配置技巧与提示",
                            "1、图像显示参数无更新按钮，及改即更新。"
                            "\n2、纵向数轴显示请填写英文，否则会无法显示。"
                            "\n3、提供自动范围功能，能自动以当前视图中的最高和最低点为上下限。"
                            "\n4、颜色栏中可以填写颜色的名称，如：red、blue；也可以写16进制RGB值，如：MicroSoft Word的主题蓝色：#2B579A（记得不要忘记写最前面的“#”）",
                            master=ParametersWindow)

    tk.Button(ParametersWindow, bg='Honeydew', text="说明3", font=('黑体', 12), width=6, height=1,command=PromptInfomation3).place(x=980, y=420, anchor='center')

    ### 显示色表
    def ShowColorTable():

        colorsWindow = tk.Tk()
        colorsWindow.title("色表")
        i = 0
        colcut = 5
        for color in colorsTable.split('\n'):
            sp = color.split(' ')
            try:
                if sp[1] == 'Black' or sp[1] == 'MidnightBlue' or sp[1] == 'DarkBlue' or sp[1] == 'Navy' or sp[1] == 'Indigo':
                    tk.Label(colorsWindow, text=color, bg=sp[1], fg='white').grid(row=int(i / colcut), column=i % colcut, sticky=tk.W + tk.E + tk.N + tk.S)
                else:
                    tk.Label(colorsWindow, text=color, bg=sp[1]).grid(row=int(i / colcut), column=i % colcut, sticky=tk.W + tk.E + tk.N + tk.S)
            except:
                print('err', color)
                tk.Label(colorsWindow, text='ERR' + color).grid(row=int(i / colcut), column=i % colcut, sticky=tk.W + tk.E + tk.N + tk.S)
            i += 1
        colorsWindow.mainloop()
    tk.Button(ParametersWindow, bg='Honeydew', text="色表", font=('黑体', 12), width=5, height=1, command=ShowColorTable).place(x=920, y=420, anchor='center')


    ### 数据显示
    tk.Label(ParametersWindow, text="显示开关", height=1, font=('黑体', 11)).place(x=70, y=460, anchor='center')
    # Data1
    Data1_show_tk = tk.BooleanVar(ParametersWindow, Data1_show)
    def Data1_Checkbutton():
        global Data1_show
        Data1_show = Data1_show_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, text="Data1", font=('Arial',12), variable=Data1_show_tk, onvalue=True, offvalue=False, command=Data1_Checkbutton).place(x=70, y=490, anchor='center')
    # Data2
    Data2_show_tk = tk.BooleanVar(ParametersWindow, Data2_show)
    def Data2_Checkbutton():
        global Data2_show
        Data2_show = Data2_show_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, text="Data2", font=('Arial',12), variable=Data2_show_tk, onvalue=True, offvalue=False, command=Data2_Checkbutton).place(x=70, y=515, anchor='center')
    # Data3
    Data3_show_tk = tk.BooleanVar(ParametersWindow, Data3_show)
    def Data3_Checkbutton():
        global Data3_show
        Data3_show = Data3_show_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, text="Data3", font=('Arial',12), variable=Data3_show_tk, onvalue=True, offvalue=False, command=Data3_Checkbutton).place(x=70, y=540, anchor='center')
    # Data4
    Data4_show_tk = tk.BooleanVar(ParametersWindow, Data4_show)
    def Data4_Checkbutton():
        global Data4_show
        Data4_show = Data4_show_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, text="Data4", font=('Arial',12), variable=Data4_show_tk, onvalue=True, offvalue=False, command=Data4_Checkbutton).place(x=70, y=565, anchor='center')

    ### 纵向数轴标签
    tk.Label(ParametersWindow, text="纵向数轴标签", height=1, font=('黑体', 11)).place(x=230, y=460, anchor='center')
    # Data1
    entry_Data1_name = tk.Entry(ParametersWindow, width=30, validate="focusout", validatecommand=lambda :entry_getString('entry_Data1_name','Data1_name'))
    entry_Data1_name.insert(0, str(Data1_name))
    entry_Data1_name.place(x=230, y=490, anchor='center')
    # Data2
    entry_Data2_name = tk.Entry(ParametersWindow, width=30, validate="focusout", validatecommand=lambda :entry_getString('entry_Data2_name','Data2_name'))
    entry_Data2_name.insert(0, str(Data2_name))
    entry_Data2_name.place(x=230, y=515, anchor='center')
    # Data3
    entry_Data3_name = tk.Entry(ParametersWindow, width=30, validate="focusout", validatecommand=lambda :entry_getString('entry_Data3_name','Data3_name'))
    entry_Data3_name.insert(0, str(Data3_name))
    entry_Data3_name.place(x=230, y=540, anchor='center')
    # Data4
    entry_Data4_name = tk.Entry(ParametersWindow, width=30, validate="focusout", validatecommand=lambda :entry_getString('entry_Data4_name','Data4_name'))
    entry_Data4_name.insert(0, str(Data4_name))
    entry_Data4_name.place(x=230, y=565, anchor='center')

    ### 数轴上限
    tk.Label(ParametersWindow, text="数轴上限", height=1, font=('黑体', 11)).place(x=400, y=460, anchor='center')
    # Data1
    entry_Data1_uplimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data1_uplimit','Data1_uplimit'))
    entry_Data1_uplimit.insert(0, str(Data1_uplimit))
    entry_Data1_uplimit.place(x=400, y=490, anchor='center')
    # Data2
    entry_Data2_uplimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data2_uplimit','Data2_uplimit'))
    entry_Data2_uplimit.insert(0, str(Data2_uplimit))
    entry_Data2_uplimit.place(x=400, y=515, anchor='center')
    # Data3
    entry_Data3_uplimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data3_uplimit','Data3_uplimit'))
    entry_Data3_uplimit.insert(0, str(Data3_uplimit))
    entry_Data3_uplimit.place(x=400, y=540, anchor='center')
    # Data4
    entry_Data4_uplimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data4_uplimit','Data4_uplimit'))
    entry_Data4_uplimit.insert(0, str(Data4_uplimit))
    entry_Data4_uplimit.place(x=400, y=565, anchor='center')


    ### 数轴下限
    tk.Label(ParametersWindow, text="数轴下限", height=1, font=('黑体', 11)).place(x=480, y=460, anchor='center')
    # Data1
    entry_Data1_downlimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data1_downlimit','Data1_downlimit'))
    entry_Data1_downlimit.insert(0, str(Data1_downlimit))
    entry_Data1_downlimit.place(x=480, y=490, anchor='center')
    # Data2
    entry_Data2_downlimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data2_downlimit','Data2_downlimit'))
    entry_Data2_downlimit.insert(0, str(Data2_downlimit))
    entry_Data2_downlimit.place(x=480, y=515, anchor='center')
    # Data3
    entry_Data3_downlimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data3_downlimit','Data3_downlimit'))
    entry_Data3_downlimit.insert(0, str(Data3_downlimit))
    entry_Data3_downlimit.place(x=480, y=540, anchor='center')
    # Data4
    entry_Data4_downlimit = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getFloatNum('entry_Data4_downlimit','Data4_downlimit'))
    entry_Data4_downlimit.insert(0, str(Data4_downlimit))
    entry_Data4_downlimit.place(x=480, y=565, anchor='center')


    ### 自动范围
    tk.Label(ParametersWindow, text="自动范围", height=1, font=('黑体', 11)).place(x=560, y=460, anchor='center')
    # Data1
    Data1_limitauto_tk = tk.BooleanVar(ParametersWindow, Data1_limitauto)
    def Data1_Checkbutton():
        global Data1_limitauto
        Data1_limitauto = Data1_limitauto_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data1_limitauto_tk, onvalue=True, offvalue=False, command=Data1_Checkbutton).place(x=560, y=490, anchor='center')
    # Data2
    Data2_limitauto_tk = tk.BooleanVar(ParametersWindow, Data2_limitauto)
    def Data2_Checkbutton():
        global Data2_limitauto
        Data2_limitauto = Data2_limitauto_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data2_limitauto_tk, onvalue=True, offvalue=False, command=Data2_Checkbutton).place(x=560, y=515, anchor='center')
    # Data3
    Data3_limitauto_tk = tk.BooleanVar(ParametersWindow, Data3_limitauto)
    def Data3_Checkbutton():
        global Data3_limitauto
        Data3_limitauto = Data3_limitauto_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data3_limitauto_tk, onvalue=True, offvalue=False, command=Data3_Checkbutton).place(x=560, y=540, anchor='center')
    # Data4
    Data4_limitauto_tk = tk.BooleanVar(ParametersWindow, Data4_limitauto)
    def Data4_Checkbutton():
        global Data4_limitauto
        Data4_limitauto = Data4_limitauto_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data4_limitauto_tk, onvalue=True, offvalue=False, command=Data4_Checkbutton).place(x=560, y=565, anchor='center')


    ### 颜色
    tk.Label(ParametersWindow, text="颜色", height=1, font=('黑体', 11)).place(x=640, y=460, anchor='center')
    # Data1
    entry_Data1_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data1_color','Data1_color'))
    entry_Data1_color.insert(0, str(Data1_color))
    entry_Data1_color.place(x=640, y=490, anchor='center')
    # Data2
    entry_Data2_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data2_color','Data2_color'))
    entry_Data2_color.insert(0, str(Data2_color))
    entry_Data2_color.place(x=640, y=515, anchor='center')
    # Data3
    entry_Data3_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data3_color','Data3_color'))
    entry_Data3_color.insert(0, str(Data3_color))
    entry_Data3_color.place(x=640, y=540, anchor='center')
    # Data4
    entry_Data4_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data4_color','Data4_color'))
    entry_Data4_color.insert(0, str(Data4_color))
    entry_Data4_color.place(x=640, y=565, anchor='center')


    ### 颜色预览
    tk.Label(ParametersWindow, text="颜色预览", height=1, font=('黑体', 11)).place(x=720, y=460, anchor='center')
    label_Data1_color = tk.Label(ParametersWindow, bg=Data1_color, width=4, height=1)
    label_Data1_color.place(x=720, y=490, anchor='center')
    label_Data2_color = tk.Label(ParametersWindow, bg=Data2_color, width=4, height=1)
    label_Data2_color.place(x=720, y=515, anchor='center')
    label_Data3_color = tk.Label(ParametersWindow, bg=Data3_color, width=4, height=1)
    label_Data3_color.place(x=720, y=540, anchor='center')
    label_Data4_color = tk.Label(ParametersWindow, bg=Data4_color, width=4, height=1)
    label_Data4_color.place(x=720, y=565, anchor='center')



    ### 网格线
    tk.Label(ParametersWindow, text="网格线", height=1, font=('黑体', 11)).place(x=800, y=460, anchor='center')
    # Data1
    Data1_grid_tk = tk.BooleanVar(ParametersWindow, Data1_grid)
    def Data1_Checkbutton():
        global Data1_grid
        Data1_grid = Data1_grid_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data1_grid_tk, onvalue=True, offvalue=False, command=Data1_Checkbutton).place(x=800, y=490, anchor='center')
    # Data2
    Data2_grid_tk = tk.BooleanVar(ParametersWindow, Data2_grid)
    def Data2_Checkbutton():
        global Data2_grid
        Data2_grid = Data2_grid_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data2_grid_tk, onvalue=True, offvalue=False, command=Data2_Checkbutton).place(x=800, y=515, anchor='center')
    # Data3
    Data3_grid_tk = tk.BooleanVar(ParametersWindow, Data3_grid)
    def Data3_Checkbutton():
        global Data3_grid
        Data3_grid = Data3_grid_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data3_grid_tk, onvalue=True, offvalue=False, command=Data3_Checkbutton).place(x=800, y=540, anchor='center')
    # Data4
    Data4_grid_tk = tk.BooleanVar(ParametersWindow, Data4_grid)
    def Data4_Checkbutton():
        global Data4_grid
        Data4_grid = Data4_grid_tk.get()
        Plot(CurrentStartIdx)  # 绘图
    tk.Checkbutton(ParametersWindow, variable=Data4_grid_tk, onvalue=True, offvalue=False, command=Data4_Checkbutton).place(x=800, y=565, anchor='center')


    ### 网格颜色
    tk.Label(ParametersWindow, text="网格颜色", height=1, font=('黑体', 11)).place(x=880, y=460, anchor='center')
    # Data1
    entry_Data1_grid_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data1_grid_color','Data1_grid_color'))
    entry_Data1_grid_color.insert(0, str(Data1_grid_color))
    entry_Data1_grid_color.place(x=880, y=490, anchor='center')
    # Data2
    entry_Data2_grid_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data2_grid_color','Data2_grid_color'))
    entry_Data2_grid_color.insert(0, str(Data2_grid_color))
    entry_Data2_grid_color.place(x=880, y=515, anchor='center')
    # Data3
    entry_Data3_grid_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data3_grid_color','Data3_grid_color'))
    entry_Data3_grid_color.insert(0, str(Data3_grid_color))
    entry_Data3_grid_color.place(x=880, y=540, anchor='center')
    # Data4
    entry_Data4_grid_color = tk.Entry(ParametersWindow, width=8, validate="focusout", validatecommand=lambda :entry_getColorString('entry_Data4_grid_color','Data4_grid_color'))
    entry_Data4_grid_color.insert(0, str(Data4_grid_color))
    entry_Data4_grid_color.place(x=880, y=565, anchor='center')


    ### 格色预览
    tk.Label(ParametersWindow, text="格色预览", height=1, font=('黑体', 11)).place(x=960, y=460, anchor='center')
    label_Data1_grid_color = tk.Label(ParametersWindow, bg=Data1_grid_color, width=3, height=1)
    label_Data1_grid_color.place(x=960, y=490, anchor='center')
    label_Data2_grid_color = tk.Label(ParametersWindow, bg=Data2_grid_color, width=3, height=1)
    label_Data2_grid_color.place(x=960, y=515, anchor='center')
    label_Data3_grid_color = tk.Label(ParametersWindow, bg=Data3_grid_color, width=3, height=1)
    label_Data3_grid_color.place(x=960, y=540, anchor='center')
    label_Data4_grid_color = tk.Label(ParametersWindow, bg=Data4_grid_color, width=3, height=1)
    label_Data4_grid_color.place(x=960, y=565, anchor='center')



    BaseVarDict = locals()          # 注意，这里还是要写一下更新一下BaseVarDict，虽然数据处理模块写了，但是locals()只会包含在它之前创建的局部变量
    ### 图像显示参数更新
    def entry_getFloatNum(entryName, VarName):
        """改变数字型entery中的内容后的操作"""
        try:
            globals()[VarName] = float(BaseVarDict[entryName].get())
            Plot(CurrentStartIdx)  # 绘图
        except:
            BaseVarDict[entryName].delete(0, 'end')
            BaseVarDict[entryName].insert(0, str(globals()[VarName]))
            messagebox.showwarning("错误", "输入的不是一个数字！", master=ParametersWindow)
        return True

    def entry_getColorString(entryName, VarName):
        """改变字符串型entery中的内容后的操作"""
        try:
            BaseVarDict['label_'+VarName].config(bg=BaseVarDict[entryName].get())
        except:
            BaseVarDict[entryName].delete(0, 'end')
            BaseVarDict[entryName].insert(0, str(globals()[VarName]))
            messagebox.showwarning("错误", "输入的颜色或RGB编码不对！", master=ParametersWindow)
            return True
        globals()[VarName] = BaseVarDict[entryName].get()
        Plot(CurrentStartIdx)  # 绘图
        return True

    def entry_getString(entryName, VarName):
        globals()[VarName] = BaseVarDict[entryName].get()
        Plot(CurrentStartIdx)  # 绘图
        return True

    ################    ParametersWindow窗口事件区     ################33
    # 将该窗口下的Enter按键（"<Return>"事件）绑定一个事件使得一个组件得到焦点，从而使原本得到焦点的entry失焦，从而触发其失焦验证命令，完成entry的数据修改
    entery_for_focus = tk.Entry(ParametersWindow)
    entery_for_focus.place(x=6000,y=7000,anchor='nw')
    def loseFocus(event):
        entery_for_focus.focus()
    def destroyParaWindow():
        entery_for_focus.focus()
        ret = messagebox.askyesno("保存","是否将当前页面的内容保存到配置文件中，方便下次使用？",master=ParametersWindow)
        if ret:
            SavePara_into_ini()
        ParametersWindow.destroy()

    ParametersWindow.bind("<Return>", loseFocus)
    ParametersWindow.bind("<Button-3>", loseFocus)
    ParametersWindow.bind("<Deactivate>", loseFocus)
    ParametersWindow.protocol('WM_DELETE_WINDOW', destroyParaWindow)    # 改变window关闭窗口按钮（右上角的叉叉按钮）触发的事件，在调用destroy()函数之前，能给个提示。最好不要用事件ParametersWindow.bind("<Destroy>", destroyParaWindow)，因为这样的话就是在窗口已经关闭后才会执行绑定的函数，若函数中有对原始窗口中的控件进行的操作，就会报错（因为控件已经不存在了）。


    ##### 保存参数到ini文件中
    def SavePara_into_ini():
        """更新ini配置参数，并保存文件"""
        for IniParaName in IniParaNameList:
            ParaConf.set('Parameters', IniParaName, str(globals()[IniParaName]))
        ParaConf.write(open('CheckAllDataParameters.ini', mode='w', encoding='utf-8'))
        messagebox.showinfo(master=ParametersWindow, title="提示", message="已将该页面所有参数保存于配置文件中！")


    ParametersWindow.mainloop()

modifyParameters = tk.Button(window, text="修改参数", bg='MistyRose',width=7,height=1,command=ParatersModifyWindow).place(x=10,y=5,anchor='nw')

################################################################


#########################   菜单栏功能   #########################
##### 位置：在窗口上方，说明文字的下方

### 选择文件并处理
def processData(channelIdx):
    """ 根据处理选项，进行数据处理 """
    try:
        Data = globals()['Data' + str(channelIdx)]
        if globals()['Data' + str(channelIdx) + '_type'] == "四参数放大器输出转log(G/G0)":
            if biasVoltage > 0:
                for i in range(0,Data.shape[0]):
                    Data[i] = Data[i] * FitPara_a1 + FitPara_b1 + 4.11 - np.log10(biasVoltage)
            elif biasVoltage < 0:
                for i in range(0, Data.shape[0]):
                    Data[i] = Data[i] * FitPara_a2 + FitPara_b2 + 4.11 - np.log10(biasVoltage)
            else:
                for i in range(0, Data.shape[0]):
                    Data[i] = 0
        elif globals()['Data' + str(channelIdx) + '_type'] == "九参数放大器输出转log(G/G0)":
            for i in range(0,Data.shape[0]):
                try:
                    if Data[i] > FitPara_ne:
                        Data[i] = np.log10(abs(np.exp((Data[i] - FitPara_ne) * FitPara_na1 + FitPara_nb1)+(Data[i]-FitPara_ne)*FitPara_nc1+FitPara_nd1)) + 4.11 - np.log10(biasVoltage)
                    else:
                        Data[i] = np.log10(abs(np.exp((Data[i] - FitPara_ne) * FitPara_na2 + FitPara_nb2) + (Data[i] - FitPara_ne) * FitPara_nc2 + FitPara_nd2)) + 4.11 - np.log10(biasVoltage)
                except:
                    Data[i] = 0
        elif globals()['Data' + str(channelIdx) + '_type'] == "公式":
            if globals()['Data' + str(channelIdx) + '_formula'].__contains__('['):      # 当公式中存在[]，说明肯定是索引表达式
                for i in range(0,Data.shape[0]):
                    try:
                        Data[i] = eval(globals()['Data' + str(channelIdx) + '_formula'])
                        if Data[i]==np.inf or Data[i]==-np.inf or np.isnan(Data[i]):       # 如果a=1/0，则a最后还会是一个numpy类型的数据，但是会被标为infall，数据穿透了，正穿透inf，负穿透-inf，没有数据NaN。
                            Data[i] = 0
                    except:
                        Data[i] = 0         # 出错就定为：0
            else:
                try:
                    Data = eval(globals()['Data' + str(channelIdx) + '_formula'])
                except:
                    Data = np.zeros((Data.shape[0],), dtype=float, order='C')
                    messagebox.showwarning("错误", "通道" + str(channelIdx) + "中数据与公式冲突，请检查原始数据和公式，已将该通道全部计算结果定为0！")
        return Data

    except ZeroDivisionError:
        messagebox.showwarning("错误","存在除以0的情况，请检查偏压设置或公式")


def read_A_tdmsFile(Path):
    """读取tdms文件中已选择通道的数据。形参：(文件路径)"""
    Data1_single = np.array([],dtype="float64")
    Data2_single = np.array([],dtype="float64")
    Data3_single = np.array([],dtype="float64")
    Data4_single = np.array([],dtype="float64")
    LocalVarsDict = locals()
    Data_single_dic = {}
    with TdmsFile.open(Path) as TDMS:                           # 创建文件操作对象
        group = TDMS.groups()[0]                                # 获取组名，一般只有一个组，index从0开始
        channelNum = len(group)                                 # 有多少个channel
        try:
            for channelIdx in [1, 2, 3, 4]:
                if globals()['Data'+str(channelIdx)+'_process']:
                    if channelIdx <= channelNum:
                        Data_single_dic[channelIdx] = np.array(group.channels()[channelIdx-1])    # 读取原始数据
                    else:
                        dataLength = Data_single_dic[1].shape[0]
                        Data_single_dic[channelIdx] = np.zeros(dataLength)
        except:
            Data_single_dic[1] = np.array([],dtype="float64")
            Data_single_dic[2] = np.array([], dtype="float64")
            Data_single_dic[3] = np.array([], dtype="float64")
            Data_single_dic[4] = np.array([], dtype="float64")
            tk.messagebox.showinfo("提示", Path + " 文件损坏!")
    return Data_single_dic


def read_all_tdmsFile():
    """将所有读到原始数据，组合并成一个数组"""
    global Data1,Data2,Data3,Data4
    Data1 = np.array([],dtype="float64")
    Data2 = np.array([],dtype="float64")
    Data3 = np.array([],dtype="float64")
    Data4 = np.array([],dtype="float64")
    length = len(FileList)
    for i in range(0, length, 1):       # 先把所有的原始数据读进来
        try:
            Data_single_dic = read_A_tdmsFile(FileList[i])
            for channelIdx in [1, 2, 3, 4]:
                if globals()['Data' + str(channelIdx) + '_process']:
                    globals()['Data' + str(channelIdx)] = np.concatenate((globals()['Data' + str(channelIdx)], Data_single_dic[channelIdx]))
        except:
            pass
        progress_fileProcess.config(value=100 * 0.9 * (i + 1) / length)
        window.update()

    try:
        for channelIdx in [1, 2, 3, 4]:     # 处理原始数据
            if globals()['Data' + str(channelIdx) + '_process']:
                globals()['Data' + str(channelIdx)] = processData(channelIdx)
    except:
        pass
    progress_fileProcess.config(value=100)

def label_fileProcessInfo_callback(event):
    newWindow = tk.Tk()
    newWindow.title("已处理文件列表")
    newWindow.geometry('500x600')
    scrollbar_v = tk.Scrollbar(newWindow, orient=tk.VERTICAL)
    textbox = tk.Text(newWindow, takefocus=0, yscrollcommand=scrollbar_v.set)
    scrollbar_v.config(command=textbox.yview)                           # 记得绑定
    scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)                          # 先pack scrollbar，保证它一直存在
    textbox.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5,pady=5)
    for i in range(0,len(FileList)):
        path = FileList[i]
        pathLength = len(path)

        charBegIdx = pathLength - 1
        while charBegIdx >= 0:              # 找到最后一个'/'字符的位置
            if path[charBegIdx] == "/":
                break
            charBegIdx -= 1

        if i == 0:                                  # 打印路径
            fileFolder = path[0:charBegIdx]
            textbox.insert('1.0', "文件夹：" + fileFolder + '\n文件列表：\n')
        fileName = path[charBegIdx+1:pathLength]
        textbox.insert(str(i+3)+'.0', fileName + '\n')    # 打印文件名

    newWindow.mainloop()

label_fileProcessInfo = tk.Label(window, width=25, height=1, bg='white', text="文件处理信息提示与当前进度:")     #显示提示信息
label_fileProcessInfo.bind("<Button-1>",label_fileProcessInfo_callback)
label_fileProcessInfo.place(x=280, y=20, anchor='center')
progress_fileProcess = ttk.Progressbar(window, length=100, maximum=100)
progress_fileProcess.place(x=380,y=10,anchor='nw')

def GUI_getFile():
    global FileList,DataLength,CurrentStartIdx

    newFileList = fd.askopenfilenames(title="请选择需要处理的tdms文件")  # 打开系统的文件管理器窗口
    if len(newFileList)==0:
        label_fileProcessInfo.config(bg='white', text="未选择文件")  # 显示提示信息
        return
    FileList = newFileList

    label_fileProcessInfo.config(bg='yellow', text="数据处理中。。。请稍后")
    progress_fileProcess.config(value=100*0.05)
    window.update()         # 这里一定要更新一下界面，否者只能执行完函数，等到下一个mainloop()界面才会更新

    read_all_tdmsFile()

    DataLength = max(Data1.shape[0], Data2.shape[0], Data3.shape[0], Data4.shape[0])  # 更新总长度
    CurrentStartIdx = 0
    label_fileProcessInfo.config(bg='white',text="处理完毕！点击查看文件列表")
    try:
        s.config( to=DataLength - ShowDataLength - 1, tickinterval=(DataLength - ShowDataLength-1) // 10)               # 修改进度条的范围
        s_value.set(0)              # 将进度条的滑块置于0
        modify_CurrentStartIdx(0)
    except:
        pass

tk.Button(window,text="选择处理的文件", bg='LightYellow',width=13, height=1, command=GUI_getFile).place(x=80,y=5,anchor='nw')


# 修改显示的数据点长度
def modify_ShowDataLength():
    global ShowDataLength, SliderPrecion, CurrentStartIdx
    result = sd.askinteger(title="修改参数", prompt="请输入窗口中需要显示的数据点个数：", initialvalue=str(ShowDataLength))
    if result==None:
        return
    ShowDataLength = result
    SliderPrecion = result//5              # 同时将滑块的滑动精度调整成窗口大小的1/10（要整除，得到一个整数）
    s.config(resolution=SliderPrecion, to=DataLength - ShowDataLength - 1, tickinterval=(DataLength - ShowDataLength-1) // 10)
    if CurrentStartIdx>DataLength-ShowDataLength-1:
        CurrentStartIdx = DataLength - ShowDataLength - 1
        s_value.set(CurrentStartIdx)
    Plot(CurrentStartIdx)

tk.Button(window, bg='LightGray',text="修改窗口中数据点个数",width=18, height=1, command=modify_ShowDataLength).place(x=500,y=5,anchor='nw')

def changePlotType():
    global CurrentStartIdx
    Plot(CurrentStartIdx)

# 选择显示视图的模式：折线图、散点图
tk.Label(window,text="图像绘制类型：", width=16, height=1,font=('黑体',12)).place(x=720, y=20, anchor='center')
radBut_1 = tk.Radiobutton(window,text="折线图",variable=PlotType,value=0,command=changePlotType).place(x=810, y=10, anchor='center')
radBut_2 = tk.Radiobutton(window,text="散点图",variable=PlotType,value=1,command=changePlotType).place(x=810, y=30, anchor='center')


##### 自动滚动播放功能
AutoPlay = False
AutoPlayTime = 0.25
def AutoPlayFunction():
    global AutoPlay
    while AutoPlay:
        newCurrentStartIdx = CurrentStartIdx + SliderPrecion
        if newCurrentStartIdx > DataLength - 1 - ShowDataLength:    # 验证是否超出上限
            break
        modify_CurrentStartIdx(newCurrentStartIdx)
        window.update()
        time.sleep(AutoPlayTime)
    AutoPlay = False
    button_AutoPlay.config(text="自动滚动", bg='MediumAquamarine')

def StartAutoPlay():
    global AutoPlay, AutoPlayTime
    if AutoPlay:            # 如果正在滚动就停止
        AutoPlay = False
        button_AutoPlay.config( text="自动滚动", bg='MediumAquamarine')
    else:                   # 否则开启滚动
        if DataLength == 0:
            messagebox.showinfo(title="提示",message="请先处理文件！",master=window)
        else:
            AutoPlay = True
            button_AutoPlay.config(text="点击结束", bg = 'Red')
            AutoPlayFunction()

button_AutoPlay = tk.Button(window, text="自动滚动", bg='MediumAquamarine', width=8, height=1, command=StartAutoPlay)
button_AutoPlay.place(x=860,y=5,anchor='nw')

def modify_AutoPlayTime():
    global AutoPlayTime
    t = sd.askfloat(title="输入参数", prompt="请输入每次滚动的时间间隔，单位：秒：")
    if t == None:
        return
    AutoPlayTime = t

button_AutoPlayTime = tk.Button(window, text="滚动间隔", bg='Silver', width=8, height=1, command=modify_AutoPlayTime)
button_AutoPlayTime.place(x=928,y=5,anchor='nw')


#########################   绘制二维图，全部在新的窗口中执行   #########################

########   一些关于该功能的全局变量   #########

# 两个调整强度图强度比例范围的tk.Scale的参数。因为如果设置成0~1之间，常常会有一大段的调整区间（0.2~1之间），图像依然显示地不清晰，所以还不如放弃这段区间
LargestIntensityRatio = 1     # 最大可调控到的强度比例
LowestIntensityRatio = 0        # 最小可调控到的强度比例

# 绘图参数
x_bin_length = 0.005             # 热图中每个格点的横向分割间隔
y_bin_length = 0.05              # 纵向间隔

HeatMap_x_downlimit = -0.25             # 热图横坐标左限，单位：s（秒）
HeatMap_x_uplimit = 1.5                 # 热图横坐标右限，单位：s（秒）
HeatMap_y_downlimit = -7
HeatMap_y_uplimit = 3
HeatMap_ylabel = ''

UsecolumnIdx = 1
UsecolumnDataType = '原始数据'

##########################################

# 将读取的所有txt文件，得到所有的x和y
def Txts2XY(TxtFileList,SamplingRate):
    x = np.array([])
    y = np.array([])
    for TxtFile in TxtFileList:
        NameLength = len(TxtFile)
        if TxtFile[NameLength - 1] == 't' and TxtFile[NameLength - 2] == 'x' and TxtFile[NameLength - 3] == 't' and TxtFile[NameLength - 4] == '.':     # 判断后缀是否为.txt
            append_y = np.loadtxt(TxtFile, delimiter=',', usecols=(int(UsecolumnIdx)-1,))
            y = np.concatenate((y,append_y))
            dataLength = append_y.shape[0]
            if UsecolumnDataType == '硬接触电导':
                # 判断单条电导曲线的0位移点zeroPointIdx（这里直接使用append_y在掉到-2之前的最后一个在0附近的点作为zeroPointIdx），并生成对应的append_x序列
                zeroPointIdx = -1
                i = 0
                while append_y[i]>-1 and i<dataLength:
                    if append_y[i]>-0.1 and append_y[i]<0.1:
                        zeroPointIdx = i
                    i += 1
                if zeroPointIdx==-1:
                    zeroPointIdx = i
                append_x = np.linspace(-1*zeroPointIdx/SamplingRate,(dataLength-zeroPointIdx)/SamplingRate,dataLength)
                x = np.concatenate((x,append_x))
            else:
                append_x = np.linspace(0, dataLength/SamplingRate, dataLength)
                x = np.concatenate((x, append_x))
    return x,y


##### 绘制二维图按钮，启动新的窗口，全部相关操作在该窗口中执行
def PlotHeatMapWindow():
    HeatMapWindow = tk.Tk()
    HeatMapWindow.geometry('1100x690')
    HeatMapWindow.title("绘制二维图")
    try:
        HeatMapWindow.iconbitmap(get_resource_path("icon.ico"))
    except:
        pass

    def PromptInfomation():
        messagebox.showinfo("热图参数设置与提示",
                            "1、绘制二维图前，需要准备单条曲线的txt数据文件。"
                            "\n2.1、采样频率点击标签修改；"
                            "\n2.2、选择“硬接触电导”处理模式，能够自动对齐零点，输入的数据无需严格对齐。"
                            "\n3、左半部分分区为数据处理模块，请在处理文件之前完成设置；右半部分为绘图参数设置区。"
                            "\n4、热图重绘过程极度消耗算力，无法实时调整，请在调整好参数后点击“重新绘图”按钮，完成参数的绘图更新和图片的重新绘制。"
                            "\n5、点击“绘制一维图”，会将当前二维图中的数据向y轴压缩，达到数据聚合的作用，对于电导数据则结果就是生成了一张一维电导统计分布图。注意：由于是将二维图数据压扁成一维图，所以修改一维图的范围和疏密都是在二维图界面中进行的。",
                            master=HeatMapWindow)
    button_PromptInfomation = tk.Button(HeatMapWindow, bg='Honeydew', text="说明", font=('黑体', 12), width=4, height=1, command=PromptInfomation)
    button_PromptInfomation.place(x=1075, y=20, anchor='center')

    HeatMap_canvas = tk.Canvas(HeatMapWindow,bg='white',width=900,height=600)
    HeatMap_canvas.place(x=5, y=80, anchor='nw')   # 初始空白画布

    ### 数据处理部分的 修改参数
    # 修改采样频率
    SamplingRate = 20000  # 默认的采样频率
    tk.Label(HeatMapWindow, text='采样频率/Hz', font=('黑体', 11)).place(x=50, y=12, anchor='center')
    def modify_SamplingRate(event):
        nonlocal SamplingRate
        result = sd.askfloat(title="输入参数", prompt="请输入仪器数据系统的采样频率，单位：Hz：", initialvalue=str(SamplingRate))
        if result != None:
            SamplingRate = result
        label_SamplingRate.config(text=str(SamplingRate))

    label_SamplingRate = tk.Label(HeatMapWindow,bg='white',text=str(SamplingRate),width=12,height=1)
    label_SamplingRate.place(x=50,y=40,anchor='center')
    label_SamplingRate.bind("<Button-1>",modify_SamplingRate)

    # 选择处理第几列的数据
    tk.Label(HeatMapWindow,text='处理第几列数据',font=('黑体',11)).place(x=175,y=12,anchor='center')
    UsecolumnIdx_tk = tk.StringVar(HeatMapWindow, UsecolumnIdx)
    def UsecolumnIdx_OptionMenu(value):
        global UsecolumnIdx
        UsecolumnIdx = value
    opt_UsecolumnIdx = tk.OptionMenu(HeatMapWindow, UsecolumnIdx_tk, '1', '2','3', '4', command=UsecolumnIdx_OptionMenu)
    opt_UsecolumnIdx.config(width = 8, bg='white')
    opt_UsecolumnIdx.place(x=175, y=40, anchor='center')

    # 选择数据类型
    tk.Label(HeatMapWindow, text='数据处理模式', font=('黑体', 11)).place(x=310, y=12, anchor='center')
    UsecolumnDataType_tk = tk.StringVar(HeatMapWindow, UsecolumnDataType)
    def UsecolumnDataType_OptionMenu(value):
        global UsecolumnDataType, HeatMap_ylabel
        UsecolumnDataType = value
        if value == '硬接触电导':
            HeatMap_ylabel = 'Conductace / log(G/G0)'
            entry_HeatMap_ylabel.delete(0, 'end')
            entry_HeatMap_ylabel.insert(0, 'Conductace / log(G/G0)')
    opt_UsecolumnDataType = tk.OptionMenu(HeatMapWindow, UsecolumnDataType_tk, '硬接触电导', '原始数据', command=UsecolumnDataType_OptionMenu)
    opt_UsecolumnDataType.config(width = 10, bg='white')
    opt_UsecolumnDataType.place(x=310,y=40,anchor='center')

    ### 输入文件、数据处理 和 绘图相关
    # 画二维热图，并输出到画布上
    heatMapIntensty_max = tk.DoubleVar()        # 准备参数，下面的两个tk.Scale依然要用
    heatMapIntensty_min = tk.DoubleVar()
    bin_max = 0

    hist2D_originData = np.array([])
    heatMap_fig = plt.figure(figsize=(9, 6), dpi=100)
    new_canvas_mid = FigureCanvasTkAgg(heatMap_fig, HeatMapWindow)
    def PlotHeatMap(x, y):
        if x.shape[0] == 0:
            return

        plt.style.use('_mpl-gallery-nogrid')
        global x_bin_length, y_bin_length, HeatMap_x_downlimit, HeatMap_x_uplimit, HeatMap_y_downlimit, HeatMap_y_uplimit, HeatMap_canvas
        nonlocal bin_max, new_canvas_mid, hist2D_originData

        hist2D_originData, x_edges, y_edges = np.histogram2d(x, y, bins=(np.arange(HeatMap_x_downlimit, HeatMap_x_uplimit, x_bin_length), np.arange(HeatMap_y_downlimit, HeatMap_y_uplimit, y_bin_length)))     # 主要是要获取hist2D_originData，方便对原始数据的保存。
        bin_max = hist2D_originData.max()        # 获取二维数组中的最大值方便使用滑块控制

        new_canvas_mid.figure.clf()
        heatMap_ax = new_canvas_mid.figure.add_subplot(1, 1, 1)
        heatMap_ax.hist2d(x,y,bins=(np.arange(HeatMap_x_downlimit, HeatMap_x_uplimit, x_bin_length), np.arange(HeatMap_y_downlimit, HeatMap_y_uplimit, y_bin_length)),vmax=heatMapIntensty_max.get()*bin_max,vmin=heatMapIntensty_min.get()*bin_max)
        heatMap_ax.set_xlabel("Time / s")
        heatMap_ax.set_ylabel(HeatMap_ylabel)
        new_canvas_mid.draw()
        HeatMap_canvas = new_canvas_mid.get_tk_widget()
        HeatMap_canvas.config(width=HeatMapWindow_size_width-200, height = HeatMapWindow_size_height-90)
        HeatMap_canvas.place(x=5, y=80, anchor='nw')


    # 请求选择文件，并处理成图片
    x = np.array([])
    y = np.array([])
    def AskForPlotingHeatMap():
        nonlocal x,y
        TxtFileList = fd.askopenfilenames(title="请选择需要处理的txt文件",master=HeatMapWindow)
        if len(TxtFileList)==0:
            return
        x,y = Txts2XY(TxtFileList,SamplingRate)
        PlotHeatMap(x, y)
    tk.Button(HeatMapWindow, text="选择需要\n处理的文件",bg='LightYellow', width=13, height=3, font=("黑体",12), command=AskForPlotingHeatMap).place(x=470,y=35,anchor='center')


    ### 分割线  ——————————————————————————————
    tk.Canvas(HeatMapWindow, bg='DarkGray', height=55, width=1).place(x=550, y=5, anchor='nw')

    ### 绘图相关参数
    tk.Label(HeatMapWindow, text="x轴").place(x=580, y=33, anchor='center')
    tk.Label(HeatMapWindow, text="y轴").place(x=580, y=58, anchor='center')

    # x轴、y轴下限
    tk.Label(HeatMapWindow, text="轴下限", height=1, font=('黑体', 11)).place(x=630, y=10, anchor='center')
    # x轴
    entry_HeatMap_x_downlimit = tk.Entry(HeatMapWindow, width=6, validate="focusout", validatecommand=lambda: entry_getFloatNum('entry_HeatMap_x_downlimit', 'HeatMap_x_downlimit'))
    entry_HeatMap_x_downlimit.insert(0, str(HeatMap_x_downlimit))
    entry_HeatMap_x_downlimit.place(x=630, y=33, anchor='center')
    # y轴
    entry_HeatMap_y_downlimit = tk.Entry(HeatMapWindow, width=6, validate="focusout", validatecommand=lambda: entry_getFloatNum('entry_HeatMap_y_downlimit', 'HeatMap_y_downlimit'))
    entry_HeatMap_y_downlimit.insert(0, str(HeatMap_y_downlimit))
    entry_HeatMap_y_downlimit.place(x=630, y=58, anchor='center')

    # x轴、y轴上限
    tk.Label(HeatMapWindow, text="轴上限", height=1, font=('黑体', 11)).place(x=700, y=10, anchor='center')
    # x轴
    entry_HeatMap_x_uplimit = tk.Entry(HeatMapWindow, width=6, validate="focusout", validatecommand=lambda: entry_getFloatNum('entry_HeatMap_x_uplimit', 'HeatMap_x_uplimit'))
    entry_HeatMap_x_uplimit.insert(0, str(HeatMap_x_uplimit))
    entry_HeatMap_x_uplimit.place(x=700, y=33, anchor='center')
    # y轴
    entry_HeatMap_y_uplimit = tk.Entry(HeatMapWindow, width=6, validate="focusout", validatecommand=lambda: entry_getFloatNum('entry_HeatMap_y_uplimit', 'HeatMap_y_uplimit'))
    entry_HeatMap_y_uplimit.insert(0, str(HeatMap_y_uplimit))
    entry_HeatMap_y_uplimit.place(x=700, y=58, anchor='center')

    # bin长度
    tk.Label(HeatMapWindow, text="bin长度", height=1, font=('黑体', 11)).place(x=770, y=10, anchor='center')
    # x轴
    entry_x_bin_length = tk.Entry(HeatMapWindow, width=6, validate="focusout", validatecommand=lambda: entry_getFloatNum('entry_x_bin_length', 'x_bin_length'))
    entry_x_bin_length.insert(0, str(x_bin_length))
    entry_x_bin_length.place(x=770, y=33, anchor='center')
    # y轴
    entry_y_bin_length = tk.Entry(HeatMapWindow, width=6, validate="focusout", validatecommand=lambda: entry_getFloatNum('entry_y_bin_length', 'y_bin_length'))
    entry_y_bin_length.insert(0, str(y_bin_length))
    entry_y_bin_length.place(x=770, y=58, anchor='center')

    # 轴标签
    tk.Label(HeatMapWindow, text="轴标签", height=1, font=('黑体', 11)).place(x=890, y=10, anchor='center')
    # x轴：固定为时间Time/s
    tk.Label(HeatMapWindow, text="Time / s",bg='white',width=20,height=1,justify='left').place(x=890, y=33, anchor='center')
    # y轴
    entry_HeatMap_ylabel = tk.Entry(HeatMapWindow, width=20, validate="focusout", validatecommand=lambda: entry_getString('entry_HeatMap_ylabel', 'HeatMap_ylabel'))
    entry_HeatMap_ylabel.insert(0, str(HeatMap_ylabel))
    entry_HeatMap_ylabel.place(x=890, y=58, anchor='center')




    # 失焦执行函数
    BaseVarDict = locals()
    def entry_getFloatNum(entryName, VarName):
        """改变数字型entery中的内容后的操作"""
        newNum = 0
        try:
            newNum = float(BaseVarDict[entryName].get())
        except:
            BaseVarDict[entryName].delete(0, 'end')
            BaseVarDict[entryName].insert(0, str(globals()[VarName]))
            messagebox.showwarning("错误", "输入的不是一个数字！", master=HeatMapWindow)
            return True
        globals()[VarName] = newNum
        return True

    def entry_getString(entryName, VarName):
        globals()[VarName] = BaseVarDict[entryName].get()
        return True

    # 将该窗口下的Enter按键（"<Return>"事件）绑定一个事件使得一个组件得到焦点，从而使原本得到焦点的entry失焦，从而触发其失焦验证命令，完成entry的数据修改
    entery_for_focus = tk.Entry(HeatMapWindow)
    entery_for_focus.place(x=6000, y=7000, anchor='nw')
    def loseFocus(event):
        entery_for_focus.focus()
    HeatMapWindow.bind("<Return>", loseFocus)

    ### 调整热图强度上下限的滑块
    def modify_heatMapIntensty_max(value):
        nonlocal heatMapIntensty_max,heatMapIntensty_min
        if x.shape[0] == 0:
            heatMapIntensty_Scale_max.set(0.2)
            return
        if heatMapIntensty_Scale_max.get() <= heatMapIntensty_Scale_min.get():
            heatMapIntensty_Scale_max.set(0.2)
            heatMapIntensty_max.set(0.2)
            tk.messagebox.showwarning(title="warning",message="上限不能小等于下限", master=HeatMapWindow)
            return
        heatMapIntensty_max.set(value)

    def modify_heatMapIntensty_min(value):
        nonlocal heatMapIntensty_max, heatMapIntensty_min
        if x.shape[0] == 0:
            heatMapIntensty_Scale_min.set(LowestIntensityRatio)
            return
        if heatMapIntensty_Scale_max.get() <= heatMapIntensty_Scale_min.get():
            heatMapIntensty_Scale_min.set(LowestIntensityRatio)
            heatMapIntensty_min.set(LowestIntensityRatio)
            tk.messagebox.showwarning(title="warning", message="上限不能小等于下限", master=HeatMapWindow)
            return
        heatMapIntensty_min.set(value)


    heatMapIntensty_Scale_max = tk.Scale(HeatMapWindow, from_=LargestIntensityRatio, to=LowestIntensityRatio, orient=tk.VERTICAL, length=300, showvalue=1, resolution=0.001, variable=heatMapIntensty_max,command=modify_heatMapIntensty_max)
    heatMapIntensty_Scale_min = tk.Scale(HeatMapWindow, from_=LargestIntensityRatio, to=LowestIntensityRatio, orient=tk.VERTICAL, length=300,showvalue=1, tickinterval=(LargestIntensityRatio-LowestIntensityRatio)/5, resolution=0.001, variable=heatMapIntensty_min,command=modify_heatMapIntensty_min)
    heatMapIntensty_Scale_max.set(LargestIntensityRatio)
    heatMapIntensty_Scale_min.set(LowestIntensityRatio)
    heatMapIntensty_max.set(LargestIntensityRatio)
    heatMapIntensty_min.set(LowestIntensityRatio)
    heatMapIntensty_Scale_min.place(x=930,y=140,anchor='nw')
    heatMapIntensty_Scale_max.place(x=1020,y=140,anchor='nw')
    label_heatMapIntensty_Scale_min = tk.Label(HeatMapWindow,text="调整\n强度\n下限",width=4,height=3)
    label_heatMapIntensty_Scale_min.place(x=1010,y=105,anchor='center')
    label_heatMapIntensty_Scale_max = tk.Label(HeatMapWindow, text="调整\n强度\n上限", width=4, height=3)
    label_heatMapIntensty_Scale_max.place(x=1060, y=105, anchor='center')


    ### 重新绘图按钮
    def button_replotHeatMap_getFocus(event):
        button_replotHeatMap.focus()
    def ReplotHeatMap():
        if x.shape[0] == 0:
            tk.messagebox.showinfo(title="提示",message="请先处理文件，再进行绘图！",master=HeatMapWindow)
            return
        PlotHeatMap(x, y)
    button_replotHeatMap = tk.Button(HeatMapWindow,text="重新绘图",bg='Silver',width=14,height=2,font=("黑体",12))
    button_replotHeatMap.bind('<Button-1>',button_replotHeatMap_getFocus)       # 给Button多绑定一个事件，点击按钮一下，就会在两次循环中分别执行button_replotHeatMap_getFocus()和ReplotHeatMap()函数——在前一个HeatMapWindow.mainloop()循环中执行button_replotHeatMap_getFocus()失焦操作，然后再是重新绘图操作。如果将两个函数合并，就会出现失焦操作和重绘图操作合并，而我们需要失焦来完成参数更新，然后画出来的图才是对的。
    button_replotHeatMap.config(command=ReplotHeatMap)
    button_replotHeatMap.place(x=920,y=660,anchor='center')


    ### 绘制一维图 按钮
    def PlotHist():
        ## 数据与创建窗口
        nonlocal y
        hist1D_originData = np.array([])
        hist1D_x_edges = np.array({})
        y_uplimit = 0
        Cursor_x = 0


        HistWindow = tk.Tk()
        HistWindow.master = HeatMapWindow
        HistWindow.title("绘制一维图")
        HistWindow.geometry('910x660')
        HistWindow.resizable(width=0, height=0)
        try:
            HistWindow.iconbitmap(get_resource_path("icon.ico"))
        except:
            pass

        ## 绘图
        fig_1DHist = plt.Figure(figsize=(9, 6), dpi=100)
        canvas_mid_1DHist = FigureCanvasTkAgg(fig_1DHist, HistWindow)
        def Plot_1DHist(y):
            if y.shape[0] == 0:
                return
            plt.style.use('_mpl-gallery')
            global y_bin_length, HeatMap_y_downlimit, HeatMap_y_uplimit
            nonlocal hist1D_originData, hist1D_x_edges,canvas_mid_1DHist, y_uplimit
            hist1D_originData, hist1D_x_edges = np.histogram(y, bins=np.arange(HeatMap_y_downlimit, HeatMap_y_uplimit, y_bin_length))
            if y_uplimit == 0:
                y_uplimit = hist1D_originData.max()*1.1
            canvas_mid_1DHist.figure.clf()
            ax = canvas_mid_1DHist.figure.add_axes([0.1,0.1,0.8,0.8])
            ax.hist(y, bins=np.arange(HeatMap_y_downlimit, HeatMap_y_uplimit, y_bin_length))
            ax.set(xlim=(HeatMap_y_downlimit, HeatMap_y_uplimit),ylim=(0, y_uplimit))
            ax.set_xlabel(HeatMap_ylabel)
            ax.set_ylabel('Counts')
            if Checkbutton_Cursor_var.get():
                ax.vlines([Cursor_x], 0, y_uplimit, linestyles='dashed', colors='red')

            canvas_mid_1DHist.draw()
            canvas = canvas_mid_1DHist.get_tk_widget()
            canvas.place(x=5, y=50, anchor='nw')

        ## 保存原始数据
        def Save1DHistData():
            path = fd.askdirectory(title="请选择保存的文件夹", master=HistWindow)
            if path == "":
                return
            pathName = path + "/1DHistData.txt"
            np.savetxt(pathName, np.column_stack((hist1D_x_edges[0:hist1D_x_edges.shape[0]-1], hist1D_originData)),fmt='%f', delimiter=',')
            tk.Label(HistWindow, bg='LightYellow',text="图片数据已保存!",width=13, height=1).place(x=500, y=20, anchor='center')

        button_Save1DHistData = tk.Button(HistWindow, text="保存图片数据", bg='LightSkyBlue', width=12, height=1, command=Save1DHistData)
        button_Save1DHistData.place(x=150, y=20, anchor='center')

        ## 修改y轴高度按钮
        def modify_y_uplimit():
            nonlocal y_uplimit, y
            new_y_uplimit = sd.askfloat(title="修改参数", prompt="请输入新的y轴上限：", initialvalue=str(y_uplimit))
            if new_y_uplimit == None:
                return
            if new_y_uplimit <= 0:
                messagebox.showerror("错误","请输入一个正数！", master=HistWindow)
                return
            y_uplimit = new_y_uplimit
            Plot_1DHist(y)

        tk.Button(HistWindow, text="修改上限",width=8, height=1, command=modify_y_uplimit).place(x=50, y=20, anchor='center')

        ## 标尺功能
        # 标尺开关
        Checkbutton_Cursor_var = tk.BooleanVar(HistWindow,False)
        Checkbutton_Cursor = tk.Checkbutton(HistWindow, text="打开横坐标定位光标", variable=Checkbutton_Cursor_var, onvalue=True, offvalue=False,command=lambda :Plot_1DHist(y))
        Checkbutton_Cursor.place(x=300, y=20, anchor='center')

        def modify_Cursor_x():
            nonlocal Cursor_x, y
            new_Cursor_x = sd.askfloat(title="修改参数", prompt="请输入新的横坐标定位光标的位置：", initialvalue=str(Cursor_x))
            if new_Cursor_x == None:
                return
            Cursor_x = new_Cursor_x
            Plot_1DHist(y)

        tk.Button(HistWindow, text="修改横坐标定位光标位置",width=20, height=1, command=modify_Cursor_x).place(x=450, y=20, anchor='center')

        Plot_1DHist(y)
        HistWindow.mainloop()

    button_plotHist = tk.Button(HeatMapWindow, text="绘制一维图", bg='SteelBlue', width=14, height=2, font=("黑体", 12), command=PlotHist)
    button_plotHist.place(x=1000, y=580, anchor='center')

    ### 保存功能按键
    label_Save_info = tk.Label(width=18,height=1,bg='white')
    # 保存图片
    def Savefig():
        path = fd.askdirectory(title="请选择保存的文件夹", master=HeatMapWindow)
        if path == "":
            return
        pathName = path + "/HeatMap.png"
        plt.savefig(pathName)
        label_Save_info.config(text="图片已保存!")
        label_Save_info.place(x=HeatMapWindow.winfo_width()-100, y=HeatMapWindow.winfo_height()-85, anchor='center')
    button_Savefig = tk.Button(HeatMapWindow, text="保存当前图片", bg='LightSkyBlue', width=12, height=1, command=Savefig)
    button_Savefig.place(x=1075, y=635, anchor='center')

    # 保存原始数据
    def SaveOriginData():
        path = fd.askdirectory(title="请选择保存的文件夹", master=HeatMapWindow)
        if path == "":
            return
        pathName = path + "/HeatMapOriginData.txt"
        np.savetxt(pathName,hist2D_originData)
        label_Save_info.config(text="图片数据已保存!")
        label_Save_info.place(x=HeatMapWindow.winfo_width() - 100, y=HeatMapWindow.winfo_height() - 85, anchor='center')
    button_SaveOriginData = tk.Button(HeatMapWindow, text="保存图片数据", bg='LightSkyBlue', width=12, height=1, command=SaveOriginData)
    button_SaveOriginData.place(x=1075, y=668, anchor='center')



    #################    窗口事件   ####################
    HeatMapWindow_size_width = 0
    HeatMapWindow_size_height = 0
    def event_HeatMapWindow_resize(self, event=None):
        nonlocal HeatMapWindow_size_width, HeatMapWindow_size_height, x, y
        if HeatMapWindow_size_width != HeatMapWindow.winfo_width() or HeatMapWindow_size_height != HeatMapWindow.winfo_height():
            HeatMapWindow_size_width = HeatMapWindow.winfo_width()
            HeatMapWindow_size_height = HeatMapWindow.winfo_height()
            # 更新画布
            HeatMap_canvas.config(width=HeatMapWindow_size_width-200, height = HeatMapWindow_size_height-90)
            new_canvas_mid.figure.set_figwidth((HeatMapWindow_size_width - 200)/100)
            new_canvas_mid.figure.set_figheight((HeatMapWindow_size_height-90)/100)
            PlotHeatMap(x, y)
            # 更新进度条长度和位置
            heatMapIntensty_Scale_max.config(length=HeatMapWindow_size_height - 350)
            heatMapIntensty_Scale_max.place(x=HeatMapWindow_size_width-80, anchor='nw')
            heatMapIntensty_Scale_min.config(length=HeatMapWindow_size_height - 350)
            heatMapIntensty_Scale_min.place(x=HeatMapWindow_size_width-170, anchor='nw')
            # 更新一些组件的位置
            button_PromptInfomation.place(x=HeatMapWindow_size_width - 25, y=20, anchor='center')
            label_heatMapIntensty_Scale_min.place(x=HeatMapWindow_size_width-90, anchor='center')
            label_heatMapIntensty_Scale_max.place(x=HeatMapWindow_size_width-40, anchor='center')
            button_replotHeatMap.place(x=HeatMapWindow_size_width-100, y=HeatMapWindow_size_height-170, anchor='center')
            button_plotHist.place(x=HeatMapWindow_size_width-100, y=HeatMapWindow_size_height-110, anchor='center')
            button_Savefig.place(x=HeatMapWindow_size_width-100, y=HeatMapWindow_size_height-55, anchor='center')
            button_SaveOriginData.place(x=HeatMapWindow_size_width-100, y=HeatMapWindow_size_height-22, anchor='center')

    HeatMapWindow.bind('<Configure>',event_HeatMapWindow_resize)

    HeatMapWindow.mainloop()

button_PlotHeatMapWindow = tk.Button(window,text="将截取的数据\n绘制成二维图",width=16,height=2,bg='SteelBlue',command=PlotHeatMapWindow)
button_PlotHeatMapWindow.place(x=1150, y=27, anchor='center')




#########################   图片与滑块控制区   #########################
##### 位置：中部和下部

### 初始白画板
canvas_init = tk.Canvas(window,bg='white',width=1200,height=540)
canvas_init.place(x=10, y=75, anchor='nw')

### 可滑动进度条

fig = plt.Figure(figsize=(10, 4.5), dpi=120)
canvas_mid = FigureCanvasTkAgg(fig, window)     # 创建画布中间件
def Plot(start):
    """画图函数"""
    if start<0:
        return
    global ShowDataLength, PlotType, canvas_mid
    canvas_mid.figure.clf()                   # 每次清空一下图片，以免重复绘图（曲线以外的内容，如：坐标轴、标题等）
    end = start + ShowDataLength
    x = np.linspace(start, end-1, ShowDataLength)

    ax_host = HostAxes(canvas_mid.figure,[0.065,0.12,0.75,0.85])     # 原始参数：0.07,0.12,0.75,0.85
    ax_host.set(xlim=(start, end))                  # 调整x的范围
    ax_host.set_xlabel('Data Points Index')         # 设置主图x轴标题
    ax_host.axis['bottom'].label.set_size(int(window_size_width/1200*7))
    ax_host.axis['bottom'].label.set_pad(int(window_size_width/1200*6))
    ax_host.axis['bottom'].major_ticklabels.set_size(int(window_size_width/1200*7))
    ax_host.axis['bottom'].major_ticklabels.set_pad(int(window_size_width/1200*8))
    ax_host.ticklabel_format(style='plain', axis='x')

    currentPlotIdx = -1
    for channelIdx in [1, 2, 3, 4]:
        if globals()['Data' + str(channelIdx) + '_show']:
            currentPlotIdx += 1

        if currentPlotIdx == 0 and globals()['Data' + str(channelIdx) + '_show']:                     # 当为第一个数据时，在主图上进行操作
            # 准备数据
            y = globals()['Data'+str(channelIdx)][start:end]
            # 显示图
            canvas_mid.figure.add_axes(ax_host)
            # 数轴
            ax_host.set_ylabel(globals()['Data'+str(channelIdx)+'_name'])                                       # 主轴标签
            ax_host.axis['left'].label.set_color(globals()['Data' + str(channelIdx) + '_color'])                # 主轴标签颜色
            ax_host.axis['left'].label.set_size(int(window_size_width/1200*7))                                                              # 主轴标签字体大小
            ax_host.axis['left'].line.set_color(globals()['Data' + str(channelIdx) + '_color'])                 # 主轴线颜色
            ax_host.axis['left'].major_ticklabels.set_color(globals()['Data' + str(channelIdx) + '_color'])     # 主轴刻度标签颜色
            ax_host.axis['left'].major_ticklabels.set_size(int(window_size_width/1200*7))                                                   # 主轴刻度标签字体大小
            ax_host.tick_params(axis='y', colors=globals()['Data' + str(channelIdx) + '_color'])                # 主轴刻度颜色和主刻度间距
            ax_host.axis['right'].major_ticks.set_visible(False)                                                # 关掉右轴刻度

            # 设置范围
            uplimit = 1
            downlimit = 0
            if globals()['Data' + str(channelIdx) + '_limitauto']:      # 自动上下限时，将上下限设置为该窗口中的最大和最小值
                uplimit = y.max()
                downlimit = y.min()
            else:
                uplimit = globals()['Data' + str(channelIdx) + '_uplimit']
                downlimit = globals()['Data' + str(channelIdx) + '_downlimit']
            if uplimit==downlimit:      # 上下限相同的情况要考虑，否则当真的存在时会出错，2022.8.9
                uplimit += 0.01
                downlimit -= 0.01
            ax_host.set_ylim(downlimit, uplimit)
            ## 横向网格线
            # 线对数轴进行分割，分出几个主刻度
            if globals()['Data' + str(channelIdx) + '_type'] == "四参数放大器输出转log(G/G0)" or globals()['Data' + str(channelIdx) + '_type'] == "九参数放大器输出转log(G/G0)":
                ax_host.yaxis.set_major_locator(MultipleLocator(1))
            else:
                ax_host.yaxis.set_major_locator(MultipleLocator((uplimit-downlimit)/10))
            # 再画网格线
            if globals()['Data' + str(channelIdx) + '_grid']:
                ax_host.grid(axis='y', linestyle='--', color=globals()['Data' + str(channelIdx) + '_grid_color'])
            # 画曲线
            if PlotType.get() == 0:
                ax_host.plot(x, y, color=globals()['Data'+str(channelIdx)+'_color'], linewidth=1.0)
            elif PlotType.get() == 1:
                ax_host.scatter(x, y, c=globals()['Data'+str(channelIdx)+'_color'], s=0.5)

        elif currentPlotIdx > 0 and globals()['Data' + str(channelIdx) + '_show']:  # 当为第二个数据时，就在右侧创建寄生轴
            # 先关闭掉主图的右轴
            ax_host.axis['right'].set_visible(False)
            # 准备数据
            y = globals()['Data' + str(channelIdx)][start:end]
            # 数轴
            locals()['par' + str(currentPlotIdx)] = ParasiteAxes(ax_host, sharex=ax_host)       # 创建寄生轴对象
            ax_host.parasites.append(locals()['par' + str(currentPlotIdx)])                     # 将寄生轴对象添加给主图ax_host
            locals()['par' + str(currentPlotIdx)].set_ylabel(globals()['Data'+str(channelIdx)+'_name'])    # 寄生轴标签
            new_axisline = locals()['par' + str(currentPlotIdx)]._grid_helper.new_fixed_axis    # 显示寄生轴
            locals()['par' + str(currentPlotIdx)].axis['right' + str(currentPlotIdx)] = new_axisline(loc='right', axes=locals()['par' + str(currentPlotIdx)], offset=(int(window_size_width/1200*45)*(currentPlotIdx-1),0))   # 设置寄生轴显示位置（右轴、间距等）
            locals()['par' + str(currentPlotIdx)].axis['right' + str(currentPlotIdx)].major_ticklabels.set_color(globals()['Data'+str(channelIdx)+'_color'])   # 刻度值颜色
            locals()['par' + str(currentPlotIdx)].axis['right' + str(currentPlotIdx)].major_ticklabels.set_size(int(window_size_width/1200*7))                                             # 刻度值字体大小
            locals()['par' + str(currentPlotIdx)].axis['right' + str(currentPlotIdx)].line.set_color(globals()['Data' + str(channelIdx) + '_color'])           # 轴的颜色
            locals()['par' + str(currentPlotIdx)].axis['right' + str(currentPlotIdx)].label.set_color(globals()['Data' + str(channelIdx) + '_color'])          # 标签的颜色
            locals()['par' + str(currentPlotIdx)].axis['right' + str(currentPlotIdx)].label.set_size(int(window_size_width/1200*7))                                                        # 标签的字体大小
            locals()['par' + str(currentPlotIdx)].tick_params(axis='y', colors=globals()['Data'+str(channelIdx)+'_color'])                                     # 轴刻度的颜色
            # 设置范围
            uplimit = 1
            downlimit = 0
            if globals()['Data' + str(channelIdx) + '_limitauto']:
                uplimit = y.max()
                downlimit = y.min()
            else:
                uplimit = globals()['Data' + str(channelIdx) + '_uplimit']
                downlimit = globals()['Data' + str(channelIdx) + '_downlimit']
            if uplimit==downlimit:      # 上下限相同的情况要考虑，否则当真的存在时会出错，2022.8.9
                uplimit += 0.01
                downlimit -= 0.01
            locals()['par' + str(currentPlotIdx)].set_ylim(downlimit, uplimit)
            ## 横向网格线
            # 线对数轴进行分割，分出几个主刻度
            if globals()['Data' + str(channelIdx) + '_type'] == "四参数放大器输出转log(G/G0)" or globals()['Data' + str(channelIdx) + '_type'] == "九参数放大器输出转log(G/G0)":
                locals()['par' + str(currentPlotIdx)].yaxis.set_major_locator(MultipleLocator(1))
            else:
                locals()['par' + str(currentPlotIdx)].yaxis.set_major_locator(MultipleLocator((uplimit - downlimit)/10))
            # 再画网格线
            if globals()['Data' + str(channelIdx) + '_grid']:
                locals()['par' + str(currentPlotIdx)].grid(axis='y', linestyle='--', color=globals()['Data' + str(channelIdx) + '_grid_color'])
            # 画曲线
            if PlotType.get() == 0:
                locals()['par' + str(currentPlotIdx)].plot(x, y, color=globals()['Data' + str(channelIdx) + '_color'], linewidth=1.0)
            elif PlotType.get() == 1:
                locals()['par' + str(currentPlotIdx)].scatter(x, y, c=globals()['Data' + str(channelIdx) + '_color'], s=0.5)

    canvas_mid.draw()
    canvas = canvas_mid.get_tk_widget()             # 拿到tkinter的Canvas组件，旧的canvas对象被覆盖了以后，被自动回收。
    canvas.config(width=window_size_width-20, height = window_size_height-200)
    canvas.place(x=10, y=75, anchor='nw')
    canvas_init.place_forget()
    ###  canvas图像绑定：
    canvas.bind("<Double-Button-1>",SaveCurrentData)      # 双击绑定，保存图像。不能绑定到window上，会出现冲突。



### 修改当前开始的位置
def modify_CurrentStartIdx(value):
    global CurrentStartIdx
    CurrentStartIdx = int(value)
    if CurrentStartIdx < 0:                                # 验证：超出下限
        CurrentStartIdx = 0
    elif CurrentStartIdx > DataLength - 1 - ShowDataLength:    # 验证：超出上限
        CurrentStartIdx = DataLength - 1 - ShowDataLength
    if DataLength>0:
        Plot(CurrentStartIdx)             # 执行绘图
    s_value.set(CurrentStartIdx)                            # 记得同步修改滑块数值
# 混动条
s_value = tk.DoubleVar()
s = tk.Scale(window, label="滑动查看所有电导", from_=0, to=DataLength-SliderPrecion-1, orient=tk.HORIZONTAL, length=1200, showvalue=1, tickinterval=0, resolution=SliderPrecion, variable=s_value, command=modify_CurrentStartIdx)
s.place(x=10,y=650,anchor='nw')

# 修改滑块精度
def modify_SilderPrecion():
    global SliderPrecion
    newPrecion = sd.askinteger(title="修改参数", prompt="请输入滑块滑动的精度：", initialvalue=str(SliderPrecion))
    if newPrecion == None:
        return
    SliderPrecion = newPrecion
    s.config(resolution=SliderPrecion, to=DataLength-ShowDataLength-1, tickinterval=(DataLength - ShowDataLength-1) // 10)
button_modify_SilderPrecion = tk.Button(window, bg='LightGray',text="修改滑动精度", width=12, height=1, command=modify_SilderPrecion)
button_modify_SilderPrecion.place(x=280, y=650, anchor='center')

# 两个微调滑块位置的按钮
def LeftMoveSlider(*kwargs):
    global CurrentStartIdx,s_value
    CurrentStartIdx -= SliderPrecion
    modify_CurrentStartIdx(CurrentStartIdx)

button_LeftMoveSlider = tk.Button(window,text="<",bg='DarkGray',font=('Arial',12,'bold'),width=3,height=1, repeatdelay=500, repeatinterval=100, command=LeftMoveSlider)
button_LeftMoveSlider.place(x=150, y=650, anchor='center')

def RightMoveSlider(*kwargs):
    global CurrentStartIdx,s_value
    CurrentStartIdx += SliderPrecion
    modify_CurrentStartIdx(CurrentStartIdx)

button_RightMoveSlider = tk.Button(window,text=">",bg='DarkGray',font=('Arial',12,'bold'),width=3,height=1, repeatdelay=500, repeatinterval=100, command=RightMoveSlider)
button_RightMoveSlider.place(x=190, y=650, anchor='center')


#########################   保存当前窗口的数据功能区   #########################
##### 位置：窗口右下下方，滚动条上方

# 保存路径的提示
l_currentSavePath = tk.Label(window,text="当前保存路径为："+CurrentSaveFolder,height=1)
l_currentSavePath.place(x=700, y=630, anchor='nw')
l_CurrentSaveFolder=tk.Label(window,text=CurrentSaveFolder,height=1)
l_CurrentSaveFolder.place(x=700, y=650, anchor='nw')

# 保存的数据形式
SaveDataType = tk.IntVar()
SaveDataType.set(0)
l_SaveDataType = tk.Label(window,text="保存类型：", width=9, height=1,font=('黑体',10))
l_SaveDataType.place(x=520, y=650, anchor='center')
radBut_dataType_1 = tk.Radiobutton(window,text="当前页面所有数据",variable=SaveDataType,value=0)
radBut_dataType_1.place(x=550, y=630, anchor='nw')
radBut_dataType_2 = tk.Radiobutton(window,text="当前页面显示数据",variable=SaveDataType,value=1)
radBut_dataType_2.place(x=550, y=650, anchor='nw')


def modify_CurrentSaveFolder():
    """修改全局变量CurrentSaveFolder"""
    global CurrentSaveFolder,l_CurrentSaveFolder
    path = fd.askdirectory(title="请选择要保存的文件夹")
    CurrentSaveFolder = path
    l_CurrentSaveFolder.config(text=CurrentSaveFolder)

def getFilesInFolder(Folder):
    """获取传入的Folder中的所有文件名"""
    fileList = []
    for root, dirs, fileList in os.walk(Folder, topdown=False):
        pass
    return fileList

def get_a_non_exist_Idx(fileList):
    """获取文件列表中没有的序号"""
    num = -1
    length = len(fileList)
    for i in range(0, length, 1):
        fileName = fileList[i]
        NameLength = len(fileName)
        if fileName[NameLength - 1] == 't' and fileName[NameLength - 2] == 'x' and fileName[NameLength - 3] == 't' and fileName[NameLength - 4] == '.':     # 判断后缀是否为.txt
            fileNameWithoutSuffix = fileName[0:NameLength - 4]
            if fileNameWithoutSuffix.isnumeric():
                newNum = int(fileNameWithoutSuffix)
                if newNum > num:
                    num = newNum
    return num+1

label_saveData_info = tk.Label(window,bg='white',width=15)
label_saveData_info_show = False
def saveDataCommand():
    global Data1,CurrentStartIdx,CurrentSaveFolder,CurrentFileIdx,ShowDataLength,label_saveData_info_show

    if CurrentSaveFolder=='':           # 如果文件夹路径为空，则先让用户先选择文件夹路径
        modify_CurrentSaveFolder()
        return
    # tk.Label(window, bg='yellow', text="正在保存。。。", width=15).place(x=1000, y=650, anchor='center')  # 提示信息：正在保存  ## 这段话多余，因为tk.Button只有完成command的时候才会更新界面，否则就会卡住，所以这个Label不会先出来，而是会和下面的Label一起出来。如果这样的话，它确实就没有用了。后面加time.sllep()依然是这样。
    # 获取一个文件夹中没有的文件名——已有的所有的.txt文件的序号的最大值+1
    Files_in_CurrentSaveFolder = getFilesInFolder(CurrentSaveFolder)    # 获取当前文件夹中所有文件的名称列表
    newIdx = get_a_non_exist_Idx(Files_in_CurrentSaveFolder)            # 返回一个新的文件名
    newFileName = str(newIdx)+'.txt'
    newPath = CurrentSaveFolder + '/'+newFileName

    Data1_current = np.array([])
    Data2_current = np.array([])
    Data3_current = np.array([])
    Data4_current = np.array([])
    saveDataCommand_localVarDic = locals()
    savaDataList = []
    if SaveDataType.get()==0:
        for i in [1,2,3,4]:
            if globals()['Data'+str(i)+'_process']:
                Data = globals()['Data'+str(i)]
                saveDataCommand_localVarDic['Data' + str(i) + '_current'] = Data[CurrentStartIdx:CurrentStartIdx + ShowDataLength]
                savaDataList.append(saveDataCommand_localVarDic['Data'+str(i)+'_current'])
    elif SaveDataType.get()==1:
        for i in [1, 2, 3, 4]:
            if globals()['Data' + str(i) + '_show']:
                Data = globals()['Data' + str(i)]
                saveDataCommand_localVarDic['Data' + str(i) + '_current'] = Data[CurrentStartIdx:CurrentStartIdx + ShowDataLength]
                savaDataList.append(saveDataCommand_localVarDic['Data' + str(i) + '_current'])
    np.savetxt(newPath, np.column_stack(tuple(savaDataList)), fmt='%f', delimiter=',')    # 保存
    label_saveData_info.config(text="已保存为："+newFileName, width=15)                   # 保存完毕，显示提示信息
    label_saveData_info.place(x=1000, y=window_size_height-100, anchor='center')
    label_saveData_info_show = True


button_CurrentSave = tk.Button(window,text="保存当前页面数据", bg='LightSkyBlue',width=14, height=1, command=saveDataCommand)
button_CurrentSave.place(x=420, y=650, anchor='center')
button_modify_CurrentSaveFolder = tk.Button(window,text="更改保存路径",bg='MistyRose',width=10,height=1,command=modify_CurrentSaveFolder)
button_modify_CurrentSaveFolder.place(x=1150,y=650, anchor='center')


#########################    窗口事件区    #########################
#####  窗口尺寸变化
def event_window_resize(self, event=None):
    global window_size_width, window_size_height, fig, canvas_mid
    if window_size_width != window.winfo_width() or window_size_height != window.winfo_height():
        window_size_width = window.winfo_width()
        window_size_height = window.winfo_height()
        # 更新画布
        canvas_mid.figure.set_figwidth((window_size_width - 20)/120)
        canvas_mid.figure.set_figheight((window_size_height-200)/120)
        Plot(CurrentStartIdx)           # 修改中间件对应的画布的大小，要等到canvas = canvas_mid.get_tk_widget()后，才能通过修改canvas来实现，所以画布大小修改在Plot(start)函数中
        canvas_init.config(width=window_size_width - 20, height=window_size_height - 200)
        # 更新进度条的长度和位置
        s.config(length = window_size_width - 20)
        s.place(x=10,y=window_size_height-90,anchor='nw')
        # 更新"保存当前窗口的数据功能区"中组件的位置
        button_modify_SilderPrecion.place(x=280, y=window_size_height-90, anchor='center')
        button_LeftMoveSlider.place(x=150, y=window_size_height-90, anchor='center')
        button_RightMoveSlider.place(x=190, y=window_size_height-90, anchor='center')
        l_currentSavePath.place(x=700, y=window_size_height-110, anchor='nw')
        l_CurrentSaveFolder.place(x=700, y=window_size_height-90, anchor='nw')
        l_SaveDataType.place(x=520, y=window_size_height-90, anchor='center')
        radBut_dataType_1.place(x=550, y=window_size_height-110, anchor='nw')
        radBut_dataType_2.place(x=550, y=window_size_height-90, anchor='nw')
        button_CurrentSave.place(x=420, y=window_size_height-90, anchor='center')
        button_modify_CurrentSaveFolder.place(x=window_size_width-70, y=window_size_height-90, anchor='center')
        if label_saveData_info_show:
            label_saveData_info.place(x=1000, y=window_size_height - 90, anchor='center')
        # 右上角的两个按钮
        button_mianwindow_PromptInfomation.place(x=window_size_width-160, y=18, anchor='center')
        button_PlotHeatMapWindow.place(x=window_size_width-70, y=27, anchor='center')
window.bind('<Configure>',event_window_resize)      # 窗口大小变化时更新画布大小和进度条大小和下方组件的位置



#####  绑定键盘和鼠标事件
###   canvas图像滚动、缩放、保存功能
def RollingDataPlot(event):
    global CurrentStartIdx
    if DataLength > 0:
        if event.delta < 0 :        # 鼠标下滚得负数
            modify_CurrentStartIdx(CurrentStartIdx + SliderPrecion)
        elif event.delta > 0 :      # 鼠标上滚得正数
            modify_CurrentStartIdx(CurrentStartIdx - SliderPrecion)

def SaveCurrentData(event):
    if DataLength > 0:
        saveDataCommand()

def KeyPress_left(event):
    LeftMoveSlider()

def KeyPress_right(event):
    RightMoveSlider()

def ZoomingDataPlot(event):
    global ShowDataLength, SliderPrecion
    newShowDataLength = ShowDataLength
    if DataLength > 0:
        if event.delta > 0 :
            newShowDataLength /= 1.1
        elif event.delta < 0 :
            newShowDataLength *= 1.1
        newShowDataLength = newShowDataLength // 1
        ShowDataLength = int(newShowDataLength)
        SliderPrecion = newShowDataLength // 5
        s.config(resolution=SliderPrecion, to=DataLength - ShowDataLength - 1, tickinterval=(DataLength - ShowDataLength-1) // 10)
        if CurrentStartIdx > DataLength - 1 - ShowDataLength :
            modify_CurrentStartIdx(DataLength - 1 - ShowDataLength)
        else:
            Plot(CurrentStartIdx)

def RollingDataPlot_precise(event):
    if DataLength > 0:
        if event.delta < 0:  # 鼠标下滚得负数
            modify_CurrentStartIdx(CurrentStartIdx + SliderPrecion//20)
        elif event.delta > 0:  # 鼠标上滚得正数
            modify_CurrentStartIdx(CurrentStartIdx - SliderPrecion//20)

def LeftMove_precise(event):
    if DataLength > 0:
        modify_CurrentStartIdx(CurrentStartIdx - SliderPrecion // 20)

def RightMove_precise(event):
    if DataLength > 0:
        modify_CurrentStartIdx(CurrentStartIdx + SliderPrecion // 20)

def ZoomingBig(event):
    global ShowDataLength, SliderPrecion
    newShowDataLength = ShowDataLength
    if DataLength > 0:
        newShowDataLength /= 1.1
        newShowDataLength = newShowDataLength // 1
        ShowDataLength = int(newShowDataLength)
        SliderPrecion = newShowDataLength // 5
        s.config(resolution=SliderPrecion, to=DataLength - ShowDataLength - 1, tickinterval=(DataLength - ShowDataLength-1) // 10)
        if CurrentStartIdx > DataLength - 1 - ShowDataLength :
            modify_CurrentStartIdx(DataLength - 1 - ShowDataLength)
        else:
            Plot(CurrentStartIdx)

def ZoomingSmall(event):
    global ShowDataLength, SliderPrecion
    newShowDataLength = ShowDataLength
    if DataLength > 0:
        newShowDataLength *= 1.1
        newShowDataLength = newShowDataLength // 1
        ShowDataLength = int(newShowDataLength)
        SliderPrecion = newShowDataLength // 5
        s.config(resolution=SliderPrecion, to=DataLength - ShowDataLength - 1, tickinterval=(DataLength - ShowDataLength-1) // 10)
        if CurrentStartIdx > DataLength - 1 - ShowDataLength :
            modify_CurrentStartIdx(DataLength - 1 - ShowDataLength)
        else:
            Plot(CurrentStartIdx)


### 绑定
window.bind("<Return>",SaveCurrentData)
window.bind("<KeyPress-Left>",KeyPress_left)
window.bind("<KeyPress-Right>",KeyPress_right)
window.bind("<MouseWheel>",RollingDataPlot)
window.bind("<Control-MouseWheel>", ZoomingDataPlot)
window.bind("<Shift-MouseWheel>", RollingDataPlot_precise)
window.bind("<Shift-KeyPress-Left>", LeftMove_precise)        # 精细左滑动
window.bind("<Shift-KeyPress-Right>", RightMove_precise)        # 精细右滑动
window.bind("<Control-KeyPress-Up>", ZoomingBig)
window.bind("<Control-KeyPress-Down>", ZoomingSmall)





############   说明
def mianwindow_PromptInfomation():
    messagebox.showinfo("数据处理与图像快捷操作提示",
                        "1、数据处理：点击“修改参数”并完成 数据处理参数（放大器拟合参数和数据处理设置） 的修改后，才可以点击“选择处理文件按钮，开始处理文件”。"
                        "\n2、数据缩放：通过点击“修改窗口中数据点个数”来修改窗口中显示的数据点的多少，点击“修改滑动精度”修改窗口滚动的速度。快捷键：Ctrl + 鼠标滚轮 或者 Ctrl + 上下方向键"
                        "\n3、数据滚动：提供多种滚动方式，为您的科研生活增添乐趣：鼠标滚轮、左右方向键、底部滑块、底部“<”和“>”按钮"
                        "\n4、数据精滚动：提供精细滚动方式：Shift + 鼠标滚轮 或者 Shift + 左右方向键"
                        "\n5、数据保存：点击“保存当前页面数据按钮，即可保存当前页面的数据位txt（多通道数据分列记录）。有两个可选项——“当前页面对应的所有通道的数据”和”当前页面中显示的通道的数据“，快捷方式：鼠标双击画布 或者 连敲两下Enter键",
                        master=window)

button_mianwindow_PromptInfomation = tk.Button(window, bg='Honeydew', text="说明", font=('黑体', 12), width=4, height=1, command=mianwindow_PromptInfomation)
button_mianwindow_PromptInfomation.place(x=1060,y=19,anchor='center')

#########################   加入防伪标志   #########################
canvas_anti_fake_label = tk.Canvas(window,bg='white',height=66,width=66)
canvas_anti_fake_label.create_line(11,11,11,56,28,56,42,38,width=5)
canvas_anti_fake_label.create_line(28,38,42,56,58,56,58,11,width=5)
canvas_anti_fake_label.create_line(43,11,43,25,58,25,width=5)
canvas_anti_fake_label.place(x=4000,y=0,anchor='nw')


window.mainloop()


