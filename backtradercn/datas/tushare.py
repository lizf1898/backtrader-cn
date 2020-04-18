# -*- coding: utf-8 -*-
import datetime as dt
import tushare as ts

import backtradercn.datas.utils as bdu
from backtradercn.settings import settings as conf
from backtradercn.libs.log import get_logger
from backtradercn.libs.models import get_or_create_library

pro = ts.pro_api()
logger = get_logger(__name__)


class TsHisData(object):
    """
    Mapping one collection in 'ts_his_lib' library, download and
    maintain history data from tushare, and provide other modules with the data.
    columns: open, high, close, low, volume
    Attributes:
        coll_name(string): stock id like '000651' for gree.

    """

    def __init__(self, coll_name):
        self._lib_name = conf.CN_STOCK_LIBNAME
        self._coll_name = coll_name
        self._library = get_or_create_library(self._lib_name)
        # self._unused_cols = ['price_change', 'p_change', 'ma5', 'ma10', 'ma20',
        #                      'v_ma5', 'v_ma10', 'v_ma20', 'turnover']
        self._unused_cols = ['pre_close', 'change', 'pct_chg', 'amount']
        self._new_added_colls = []

    @classmethod
    def download_one_delta_data(cls, coll_name):
        """
        Download all the collections' delta data.
        :param coll_name: a stock code
        :return: None
        """
        ts_his_data = TsHisData(coll_name)
        ts_his_data.download_delta_data()

    @classmethod
    def download_all_delta_data(cls, *coll_names):
        """
        Download all the collections' delta data.
        :param coll_names: list of the collections.
        :return: None
        """
        for coll_name in coll_names:
            ts_his_data = TsHisData(coll_name)
            ts_his_data.download_delta_data()

    def download_delta_data(self):
        """
        Get yesterday's data and append it to collection,
        this method is planned to be executed at each day's 8:30am to update the data.
        1. Connect to arctic and get the library.
        2. Get today's history data from tushare and strip the unused columns.
        3. Store the data to arctic.
        :return: None
        """

        self._init_coll()

        if self._coll_name in self._new_added_colls:
            return

        # 15:00 PM can get today data
        # start = latest_date + 1 day
        latest_date = self.get_data().index[-1]
        start_date = latest_date + dt.timedelta(days=1)
        start_date = dt.datetime.strftime(start_date, '%Y%m%d')
        # start_date = '20200416'

        # his_data = ts.get_hist_data(
        #     code=self._coll_name,
        #     start=start,
        #     retry_count=5
        # )
        his_data = ts.pro_bar(
            ts_code=self._coll_name,
            adj='qfq',
            start_date=start_date
        )

        # delta data is empty
        if len(his_data) == 0:
            logger.info(
                f'delta data of stock {self._coll_name} is empty, after {start_date}')
            return

        his_data = bdu.Utils.strip_unused_cols(his_data, *self._unused_cols)

        logger.info(f'got delta data of stock: {self._coll_name}, after {start_date}')
        self._library.append(self._coll_name, his_data)

    def get_data(self):
        """
        Get all the data of one collection.
        :return: data(DataFrame)
        """

        data = self._library.read(self._coll_name).data
        # parse the date

        # data.index = data.index.map(bdu.Utils.parse_date)
        data.index = data.trade_date.map(bdu.Utils.parse_date)

        return data

    def _init_coll(self):
        """
        Get all the history data when initiate the library.
        1. Connect to arctic and create the library.
        2. Get all the history data from tushare and strip the unused columns.
        3. Store the data to arctic.
        :return: None
        """

        # if collection is not initialized
        if self._coll_name not in self._library.list_symbols():
            self._new_added_colls.append(self._coll_name)
            # his_data = ts.get_hist_data(code=self._coll_name, retry_count=5).sort_index()
            his_data = ts.pro_bar(ts_code=self._coll_name, adj='qfq').sort_index()

            if len(his_data) == 0:
                logger.warning(
                    f'data of stock {self._coll_name} when initiation is empty'
                )
                return

            his_data = bdu.Utils.strip_unused_cols(his_data, *self._unused_cols)

            logger.debug(f'write history data for stock: {self._coll_name}.')
            self._library.write(self._coll_name, his_data)
