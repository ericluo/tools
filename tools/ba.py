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


def share_legend_for(figs):
    """ share legend for across subplots

        Refer to: <https://github.com/plotly/plotly.py/issues/800>
    """
    for i, fig in enumerate(figs):
        for trace in fig['data']:
            trace['legendgroup'] = trace['name']
            if( i != 0):
                trace['showlegend'] = False

def set_tickformat(figs, xformat, yformat):
    """ set tickformat for xaxis and yaxis

        :sp:        sp = cf.subplots()
        :xformat:   tickformat for xaxis
        :yformat:  tickformats for yaxis
    """
    for key in figs['layout']:
        if key.startswith('xaxis'):
            figs['layout'][key].update(tickformat = xformat)
        if key.startswith('yaxis'):
            figs['layout'][key].update(tickformat = yformat)


def plot_data_with_subplots(dfs, sub_titles, yoy = False, title = None,
                            xformat = None, yformat = None):
    if(yoy):
        dfs = [df.pct_change(periods = 12).dropna() for df in dfs]
        yformats = '.2%'
    # geneate figure data and share legend
    figs = [df.iplot(asFigure = True) for df in dfs]
    share_legend_for(figs)

    # config xaxis and yaxis tickformat
    figs = cf.subplots(figs, subplot_titles = sub_titles, shared_xaxes = True, shared_yaxes=True)
    set_tickformat(figs, xformat, yformat)
    # set title for the plot
    if(title):
        figs['layout'].update(title = title)

    cf.iplot(figs)

class Banxcel:

    """ Bank Report Processing like Excel

    Bank Report Process tools like Excel.
    """

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

        for p in pd.period_range(start_date, end_date, freq='M'):
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

        self.init_indicators()

    def init_indicators(self):
        self.data['逾期贷款率'] = self.data['逾期贷款'] / self.data['各项贷款余额']
        self.data['90天以上逾期贷款率'] = self.data['逾期90天以上'] / self.data['各项贷款余额']
        self.data['关注贷款率'] = self.data['关注类贷款'] / self.data['各项贷款余额']
        self.data['不良贷款率'] = self.data['不良贷款余额'] / self.data['各项贷款余额']
        self.data['核销率'] = self.data['冲销卖出'] / self.data['各项贷款余额']
        self.data['核销前关注不良率'] = (self.data['关注类贷款'] + self.data['不良贷款余额'] + self.data['冲销卖出']) / self.data['各项贷款余额']
        self.data['核销前逾期贷款率'] = (self.data['逾期90天以上'] + self.data['冲销卖出']) / self.data['各项贷款余额']
        self.data['拨备覆盖率'] = self.data['贷款损失准备'] / self.data['不良贷款余额']
        self.data['拨贷率'] = self.data['贷款损失准备'] / self.data['各项贷款余额']
        self.data['关注+不良贷款占比'] = (self.data['关注类贷款'] + self.data['不良贷款余额']) / self.data['各项贷款余额']

        self.data['拨备前利润'] = self.data['本年利润'] / 0.75 + self.data['新提准备金']

    def get_indicator(self, ind, gs = 'A'):
        """ 抽取给定单个指标的时间序列

            gs: 按机构分组进行筛选并排序
                A - 所有机构
                D - 大型银行
                G - 股份制银行
        """
        df = self.data[ind].unstack()

        govs = self.GOVS[gs]
        govs = sorted(govs.keys(), key = lambda k: govs[k])
        return(df.loc[:, govs])

    def get_indicators(self, inds, gs = 'A'):
        return([self.get_indicator(ind, gs) for ind in inds])

    def plot_indicators_with_subplots(self, inds, gs = 'A', yoy = False,
                                        xformat = '%Y%m', yformat = None):

        dfs = self.get_indicators(inds, gs)
        if(yoy):
            dfs = [df.pct_change(periods = 12).dropna() for df in dfs]
            yformat = '.2%'
        # geneate figure data and share legend
        figs = [df.iplot(asFigure = True) for df in dfs]
        share_legend_for(figs)

        figs = cf.subplots(figs, subplot_titles = inds)
        set_tickformat(figs, xformat, yformat)
        cf.iplot(figs)


    def plot_indicator_with_subplots(self, ind, gs = 'A', yoy = False,
                                        xformat = None, yformat = None):
        df = self.get_indicator(ind, gs)
        banks = list(self.GOVS[gs].keys())

        df2 = df.set_index([df.index.month, df.index.year])
        dfs = [df2.unstack()[b] for b in banks]

        if(yoy):
            dfs = [df.pct_change(periods = 12).dropna() for df in dfs]
            yformats = '.2%'
        # geneate figure data and share legend
        figs = [df.iplot(asFigure = True) for df in dfs]
        share_legend_for(figs)

        # config xaxis and yaxis tickformat
        figs = cf.subplots(figs, shared_xaxes = True, subplot_titles = banks)
        set_tickformat(figs, xformat, yformat)
        # set title for the plot
        figs['layout'].update(title = ind)

        cf.iplot(figs)


if __name__ == "__main__":
    banxcel = Banxcel("h:/ba/2017")
    # print(banxcel.data)
    print(banxcel.get_indicator("各项贷款"))
