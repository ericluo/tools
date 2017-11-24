import pandas as pd
import numpy as np

from collections import OrderedDict
import os

pd.set_option('display.precision', 2)
pd.set_option('display.float_format', '{:,.2f}'.format)

ALL_BANKS = OrderedDict([("工商银行", 7), ("农业银行", 8), ("中国银行", 9), ("建设银行", 10),
                         ("交通银行",11), ('中信银行', 13), ('光大银行', 14), ('华夏银行', 15),
                         ('平安银行', 17), ('招商银行', 18), ('浦发银行', 19), ('兴业银行', 20),
                         ('民生银行', 21)])
DX_BANKS  = OrderedDict([("工商银行", 7), ("农业银行", 8), ("中国银行", 9), ("建设银行", 10),
                         ("交通银行",11)])
GFZ_BANKS = OrderedDict([('中信银行', 13), ('平安银行', 17), ('招商银行', 18), ('浦发银行', 19),
                         ('兴业银行', 20), ('民生银行', 21)])

indicators = [("贷款质量五级分类情况表", OrderedDict([('各项贷款余额', 0), ('正常贷款余额', 4), ('关注类贷款', 8), ('不良贷款余额', 12),
                             ('次级类贷款', 16), ('可疑类贷款', 20), ('损失类贷款', 24), ('逾期贷款', 28), ('逾期90天以上', 32)])),
              ("资产减值准备情况表", OrderedDict([('贷款损失准备', 0), ('新提准备金', 1), ("冲销卖出", 2)])),
              ( "资产负债及存贷款情况简表", OrderedDict([('本年利润', 44)]))
             ]

def populate_data(data_path, start_date = '20151231', end_date = '20171231'):

    periods = pd.date_range(start_date, end_date, freq='M')

    by_half_year = pd.date_range(start_date, end_date, freq='2Q')
    by_quarter = pd.date_range(start_date, end_date, freq='Q')
    by_year = pd.date_range(start_date, end_date, freq='A')

    banks = ALL_BANKS

    data = []
    for p in periods:
        pdata = []

        for ind in indicators:
            f = "{}/{:4d}{:02d}_{}.xls".format(data_path, p.year, p.month, ind[0])

            if(os.path.exists(f)):
                df = pd.read_excel(f, index_col=0)
                df = df.iloc[list(banks.values()), list(ind[1].values())]
                df.columns = ind[1].keys()
                df.index = banks.keys()

                pdata.append(df)

        if len(pdata) > 0:
            dff = pd.concat(pdata, axis=1)
            dff['期数'] = p

            data.append(dff)

    data = pd.concat(data)
    data.index.name = '机构名称'
    data = data.reset_index().set_index(['期数', '机构名称'])
    return(data)

if __name__ == '__main__':
    print(populate_data("H:/ba/2017/").tail())
