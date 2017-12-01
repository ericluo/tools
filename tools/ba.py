import pandas as pd
import numpy as np
pd.set_option('display.precision', 2)
pd.set_option('display.float_format', '{:,.2f}'.format)

from collections import ChainMap, namedtuple
import os

import plotly
plotly.offline.init_notebook_mode(connected=True)
import plotly.plotly as py
import plotly.tools as tls
import plotly.graph_objs as go
import cufflinks as cf
cf.set_config_file(offline=True, offline_link_text='', offline_show_link=False)

""" Bank Report Processing like Excel

    Bank Report Process tools like Excel.
"""

class Banxcel:

    DX_BANKS  = {"工商银行": 7, "农业银行": 8, "中国银行": 9, "建设银行": 10, "交通银行": 11}
    GFZ_BANKS = {'中信银行': 13, '平安银行': 17, '招商银行': 18, '浦发银行': 19, '兴业银行': 20, '民生银行': 21}
    ALL_BANKS = ChainMap(DX_BANKS, GFZ_BANKS)
    GOVS = {"D": DX_BANKS, "G": GFZ_BANKS, "A": ALL_BANKS}

    Table = namedtuple('Table', ['name', 'indicators'])
    FIVE_CLASS = Table("贷款质量五级分类情况表", {
        '各项贷款余额': 0, '正常贷款余额': 4, '关注类贷款': 8, '不良贷款余额': 12,
        '次级类贷款': 16, '可疑类贷款': 20, '损失类贷款': 24, '逾期贷款': 28, '逾期90天以上': 32})
    RESERVE = Table("资产减值准备情况表", {'贷款损失准备': 0, '新提准备金': 1, "冲销卖出": 2})
    BALANCE = Table("资产负债及存贷款情况简表", {
        '资产总额': 0, '负债总额': 6, '所有者权益': 12, '各项贷款': 17,
        '贴现及转贴现': 23,  '各项存款': 28, '单位存款': 34, '储蓄存款': 39, '本年利润': 44})
    TABLES = [FIVE_CLASS, RESERVE, BALANCE]

    def __init__(self, data_path, start_date = '20151231', end_date = '20171231'):
        self.data = []
        banks = self.ALL_BANKS

        for p in pd.date_range(start_date, end_date, freq='M').to_period():
            pdata = []

            for t in self.TABLES:
                f = "{}/{:4d}{:02d}_{}.xls".format(data_path, p.year, p.month, t.name)

                if(os.path.exists(f)):
                    df = pd.read_excel(f, index_col=0)
                    df = df.iloc[list(banks.values()), list(t.indicators.values())]
                    df.columns = t.indicators.keys()
                    df.index = banks.keys()

                    pdata.append(df)

            if len(pdata) > 0:
                dff = pd.concat(pdata, axis=1)
                dff['期数'] = p

                self.data.append(dff)

        self.data = pd.concat(self.data)
        self.data.index.name = '机构名称'
        self.data.reset_index(inplace=True)
        self.data.set_index(['期数', '机构名称'], inplace=True)

    """ 抽取给定单个指标的时间序列

        gs: 按机构分组进行筛选并排序
            A - 所有机构
            D - 大型银行
            G - 股份制银行
    """
    def get_indicator(self, ind, gs = 'A'):
        df = self.data[ind].unstack()
        govs = self.GOVS[gs]
        govs = sorted(govs.keys(), key = lambda k: govs[k])
        return(df.loc[:, govs])

    """ 抽取给定单个指标的时间序列，并计算增长率

        gs: 同上
        ps: 观测周期间隔期限
            1  - 环比上月
            12 - 同比上年
    """
    def get_indicator_chg_and_plot(self, ind, gs = 'A', ps = 12):
        df = self.get_indicator(ind, gs)
        df = df.pct_change(periods = ps).dropna()

        fig = df.iplot(asFigure = True)
        fig['layout']['yaxis1']['tickformat'] = ".2%"
        fig['layout']['xaxis1']['tickformat'] = "%Y%m"
        cf.iplot(fig)

if __name__ == "__main__":
    banxcel = Banxcel("h:/ba/2017")
    # print(banxcel.data)
    print(banxcel.get_indicator("各项贷款"))
