"""
drawingutil.py
qlsignalNew_20240808
Created by huanghx on 2024/8/26
Copyright © 2024 huanghx. All rights reserved.
"""
try:
    import matplotlib.pyplot as plt
    from matplotlib.dates import MonthLocator, DayLocator, DateFormatter
    from matplotlib.font_manager import FontProperties
except ImportError:
    plt = None
    MonthLocator = None
    DayLocator = None
    DateFormatter = None
    FontProperties = None

import dfutil
import pandas as pd

# 设置中文字体，fname是我的电脑中的字体的路径
import os
import platform

font_name = '/System/Library/Fonts/STHeiti Medium.ttc'
if not os.path.exists(font_name):
    # 如果指定路径不存在（例如在Windows上），尝试使用系统默认中文字体
    if platform.system() == 'Windows':
        font_name = 'SimHei'  # 黑体
    else:
        font_name = 'SimHei'  # 其他系统尝试黑体

if FontProperties:
    if os.path.exists(font_name):
        font = FontProperties(fname=font_name, size=10)
    else:
        # 如果是字体名称而不是路径
        font = FontProperties(family=font_name, size=10)
else:
    font = None


def draw_yield_curve_chart(this_strategy_df, reference_df, key_indicators_df, save_path=None):
    """
    绘制收益率曲线
    @param this_strategy_df: 基准数据
    @param reference_df: 基准数据key
    @param key_indicators_df: 基准名称
    @param save_path: 图片保存路径 (可选)
    """
    if plt is None:
        dfutil.log("matplotlib not installed, skipping draw_yield_curve_chart")
        return

    """
        fig = plt.figure(figsize=(10, 5))  # 设置图形大小
        # gs = gridspec.GridSpec(4, 1)
        # 获取系统中所有可用的字体
        # font_list = matplotlib.font_manager.get_fontconfig_fonts()
        # names = [font.name for font in font_list]

        # 设置字体为宋体
        # plt.rcParams['font.family'] = ['serif']  # 设置字体为有衬线字体（宋体是有衬线字体之一）
        # plt.rcParams['font.serif'] = ['SimSun']  # 设置有衬线字体为宋体
        # # 下面的是设置字体为黑体
        # plt.rcParams['font.family'] = ['sans-serif']  # 设置字体为无衬线字体（黑体是无衬线字体之一）
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置无衬线字体为黑体
        # matplotlib.rc('font', family='Microsoft YaHei')

        # # 设置公式格式
        # plt.rcParams['mathtext.fontset'] = 'stix'
        #
        # 正常显示负号
        plt.rcParams['axes.unicode_minus'] = False
        # plt.rcParams['font.size'] = 18  # 设 置字体字号
        # plt.rcParams['xtick.labelsize'] = 16  # 设置横坐标轴字体字号
        # plt.rcParams['ytick.labelsize'] = 16  # 设置纵坐标轴字体字号
        #
        # # 设置线条宽度
        # plt.rcParams['lines.linewidth'] = 1
        # # 设置线条颜色
        # plt.rcParams['lines.color'] = 'green'
        # # 设置线条样式 - 会报错
        # # plt.rcParams['lines.linestytle'] = '-'
        plt.plot(this_strategy_df.index, this_strategy_df['收益率'], color='red', label='本策略')
        plt.plot(this_strategy_df.index, reference_df['收益率'], color='blue', label='沪深300')
        plt.title = '总收益率曲线'
        plt.xlabel('日期')
        plt.ylabel('收益率')
        # 添加图例（通过bbox_to_anchor精细调整图例位置）
        # plt.legend(this_strategy_df.columns,  # 运用说明文字来添加列表
        #            loc='center',  # 粗略调整图例的位置在右上方
        #            bbox_to_anchor=[0, 1],  # 精细调整图例在整张画布的位置
        #            ncol=4)  # 将图例分成4列
        plt.legend()  # 显示图例（比如：“本策略”和“沪深300”默认显示在右上角）
        """

    # 在matplotlib画布基础上渲染目标数据框的表格图
    fig, ax = plt.subplots(figsize=(20, 5))  # 会创建新的表格 并 设置图形大小
    # fig.set_size_inches(20, 5)  # 设置图形大小

    # Ensure pandas matplotlib converters are registered
    try:
        from pandas.plotting import register_matplotlib_converters
        register_matplotlib_converters()
    except ImportError:
        pass

    # Ensure indices are converted to datetime if they are not already (double check)
    if not isinstance(this_strategy_df.index, pd.DatetimeIndex):
        try:
            this_strategy_df.index = pd.to_datetime(this_strategy_df.index)
        except Exception:
            pass
            
    if not isinstance(reference_df.index, pd.DatetimeIndex):
        try:
            reference_df.index = pd.to_datetime(reference_df.index)
        except Exception:
            pass

    # 显示刻度
    plt.xticks()

    # 设置刻度朝里，我喜欢朝里，默认的朝外感觉有点丑
    plt.tick_params(which="major", direction='in', length=5, bottom=True, left=True)
    plt.rcParams['font.sans-serif'] = [font.get_name()]  # ['SimHei']无效，matplotlib可能没有该字体  # 设置无衬线字体为黑体
    plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号
    # todo 待优化：ValueError(f"x and y must have same first dimension, but "
    # ValueError: x and y must have same first dimension, but have shapes (242,) and (197,)
    ax.plot(this_strategy_df.index, this_strategy_df['收益率'], color='red', label='本策略')
    ax.plot(reference_df.index, reference_df['收益率'], color='blue', label='沪深300')
    # 设置X轴日期格式
    ax.xaxis.set_major_locator(MonthLocator())  # 设置主刻度线
    # ax.xaxis.set_minor_locator(DayLocator())    # 设置次刻度线

    # 通过判断交易回测的天数来调整收益曲线图的显示样式 add by hhx 2024.12.17
    date_formatter = '%Y-%m-%d'
    if dfutil.len_safe(this_strategy_df) > 250:
        # 如果交易回测的天数大于一年的交易日（大概250日左右），则只显示年月 且 垂直显示，避免日期重叠
        """
        以下3个方法都可以，但是方法1和方法2会出现一个警告：
        UserWarning: set_ticklabels() should only be used with a fixed number of ticks, 
        i.e. after set_ticks() or using a FixedLocator.
        原因是：set_xticks 和 set_xticklabels必须同时使用，缺一不可。
        """
        # ax.set_xticks(this_strategy_df.index.values) # 要转换成年-月 且 要去重
        # 方法1
        # ax.set_xticklabels(this_strategy_df.index, rotation=90)
        # 方法2
        # ax.set_xticklabels(ax.get_xticklabels(), rotation=90)

        # 方法3：显示刻度 并 将x轴标签旋转90度
        plt.xticks(rotation=90)
        date_formatter = '%Y-%m'

    ax.xaxis.set_major_formatter(DateFormatter(date_formatter))  # 设置主标签的格式
    # ax.xaxis.set_minor_formatter(DateFormatter('%Y-%m'))  # 设置次标签的格式
    plt.title('总收益率曲线 (Dynamic Regime Switching + Optimized Params)', fontdict={'family': font.get_name(), 'size': 16, 'color': 'black', 'weight': 'bold'})
    plt.xlabel('日期', fontdict={'family': font.get_name(), 'size': 14, 'color': 'black'})
    plt.ylabel('收益率', fontdict={'family': font.get_name(), 'size': 14, 'color': 'black'})
    plt.legend(prop=font)  # 显示图例（比如：“本策略”和“沪深300”默认显示在右上角），prop=font可加可不加

    # ax = plt.gca()  # 在图表下方插入表格
    # bbox精细调整图例在整张画布的位置，如果此参数有值，则会覆盖loc参数
    gray = '#E0E0E0'
    white = "w"
    green = white  # '#95C13E' 把绿色改为白色
    col_colours = [gray, gray, gray, gray, gray, gray, gray, gray, gray, gray, gray]
    cell_colours = [[white, green, white, green, white, green, white, green, white, green, white],
                    [white, green, white, green, white, green, white, green, white, green, white]]  # 2行11列
    table = ax.table(cellText=key_indicators_df.values, colLabels=key_indicators_df.columns, loc='bottom',
                     cellLoc='center', bbox=[0, -0.6, 1, 0.3], colColours=col_colours, cellColours=cell_colours)

    # 修改表的列标签的字体颜色
    for i, j in zip(table.properties()['celld'], table.properties()['children']):
        if i[0] == 0:
            j.get_text().set_color('blue')
            j.get_text().set_weight('bold')

    table.auto_set_font_size(False)
    table.set_fontsize(14)
    # ax.axis('off') # 会去掉收益率曲线图的x,y坐标
    fig.tight_layout()  # 规整排版，这句不能少，否则底部的表格要么不可见，要么与曲线重叠
    # fig.tight_layout(pad=1, w_pad=10, h_pad=3)  # 规整排版
    # 美化图表
    # plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    
    if save_path:
        try:
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path)
            # print(f"图表已保存至: {save_path}") # 避免这里打印，由调用者打印
        except Exception as e:
            print(f"保存图表失败: {e}")
    else:
        # 仅在未提供保存路径时显示，或者根据需要调整
        # plt.show()  # 显示图形 - 暂时注释掉以避免阻塞自动化流程
        pass
        
    plt.close() # 关闭图形，释放内存
