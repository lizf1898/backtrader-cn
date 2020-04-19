# -*- coding: utf-8 -*-
import gevent.pool
import gevent.monkey
gevent.monkey.patch_all()

import tushare as ts
# 设置token，只需设置一次! 初始化接口
# ts.set_token('1afa396cfef9804ec51c1e51b5d85187fb5aea6bac4b8238a00143f8')
ts.set_token('ac16b470869c5d82db5033ae9288f77b282d2b5519507d6d2c72fdd7')

pro = ts.pro_api()

import backtradercn.datas.tushare as bdt
from backtradercn.libs.log import get_logger
from backtradercn.libs import models
from backtradercn.settings import settings as conf



logger = get_logger(__name__)


def download_delta_data(stocks, pool_size=40):
    """
    Download delta data for all stocks collections of all libraries.
    :param stocks: stock code list.
    :param pool_size: the pool size of gevent.pool.Pool.
    :return: None
    """

    pool = gevent.pool.Pool(pool_size)
    for i in range(len(stocks) // pool_size + 1):
        start = i * pool_size
        end = (i + 1) * pool_size
        lst = stocks[start:end]
        logger.debug(f'download delta data for stock list: {lst}')
        for stock in lst:
            pool.spawn(bdt.TsHisData.download_one_delta_data, stock)
        pool.join(timeout=30)


if __name__ == '__main__':
    # make sure the library exists
    models.get_or_create_library(conf.CN_STOCK_LIBNAME)

    # download_delta_data(['000651', '000001'])

    # hs300s = ts.get_hs300s()
    # stock_pools = hs300s['code'].tolist() if 'code' in hs300s else []

    # 查询当前所有正常上市交易的股票列表
    data = pro.stock_basic(exchange='SZSE', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    stock_pools = data['ts_code'].tolist() if 'ts_code' in data else []

    # stock_pools = ['600000.SH','600036.SH']

    if not stock_pools:
        logger.warning('can not stock pools return empty.')
        stock_pools = models.get_cn_stocks()
    download_delta_data(stock_pools)
