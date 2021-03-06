import tushare as ts
import time
import sql_model
import pandas as pd
import common
import debug
import traceback
import datetime
from urllib.request import ProxyHandler, build_opener, install_opener
import requests
import code_ssdb
import threading
import os


def get_h_week_data(code, threadName, conn):
    # 从这个股票已有数据的最后一个日期开始获取
    engine = sql_model.get_conn()
    sql = "select * from stock_weekly_data where sCode = '" + code + "' order by tDateTime desc limit 1"
    print("%s %s" % (threadName, sql))
    df = pd.read_sql(sql, engine)
    if not df.empty:
        start_date = df.loc[0, ['tDateTime']].values[0] + datetime.timedelta(days=1)
        start_time = datetime.datetime.strptime(str(start_date), "%Y-%m-%d")
    else:
        start_date = "1990-01-01"
        start_time = datetime.datetime.strptime(str(start_date), "%Y-%m-%d")

    while start_time < datetime.datetime.now():
        try:
            end_time = start_time + datetime.timedelta(days=365)
            print("%s %s %s %s 开始" % (threadName, code, start_time, end_time))

            stock_data = ts.bar(code, conn=conn, freq='W', start_date=str(start_time), end_date=str(end_time),
                                adj='hfq')
            # stock_data = ts.get_h_data(code, start=str(start_time), end=str(end_time), autype='hfq')
            # stock_data['sCode'] = code
            stock_data['tDateTime'] = stock_data.index
            stock_data2 = stock_data.sort_index(ascending=True)
            stock_data2.rename(columns={'code': 'sCode', 'open': 'iOpeningPrice', 'high': 'iMaximumPrice', 'close': 'iClosingPrice',
                                        'low': 'iMinimumPrice', 'vol': 'iVolume', 'amount': 'iAmount'}, inplace=True)
            # 存入数据库
            tosql_res = None
            if len(stock_data2) > 1:
                tosql_res = stock_data2.to_sql('stock_weekly_data', engine, if_exists='append', index=False)
                if tosql_res:
                    common.file_write("tosql_" + threadName, tosql_res)
            print("%s %s %s" % (threadName, __name__, str(tosql_res)))

        except IOError:
            traceback.print_exc()
            # print("IOError等待60秒")
            # time.sleep(60)
            proxy_address = requests.get("http://112.124.4.247:5010/get/").text
            print("%s 更换代理 %s" % (threadName, proxy_address))

            # 请求接口获取数据
            proxy = {
                # 'http': '106.46.136.112:808'
                # 'https': "https://112.112.236.145:9999",
                "http": proxy_address
            }
            print(proxy)
            # 创建ProxyHandler
            proxy_support = ProxyHandler(proxy)
            # 创建Opener
            opener = build_opener(proxy_support)
            # 安装OPener
            install_opener(opener)
        else:
            print("\n")
            print("%s %s %s %s 成功" % (threadName, code, start_time, end_time))
            start_time = end_time + datetime.timedelta(days=1)


# 获取所有股票
def get_data(threadName, conn):
    while 1 == 1:
        code = code_ssdb.get_next_code()
        if code:
            print("%s: %s begin" % (threadName, code))
            get_h_week_data(code, threadName, conn)
            print("%s: %s end" % (threadName, code))
        else:
            break


if __name__ == '__main__':
    # 建立一个新数组
    threads = []
    n = 1
    counter = 1
    while counter <= n:
        name = "Thread-" + str(counter)
        conn = ts.get_apis()
        threads.append(threading.Thread(target=get_data, args=(name, conn)))
        counter += 1
        # thing1 = threading.Thread(target=get_data, args=("Thread-1",))
        # threads.append(thing1)
        # thing2 = threading.Thread(target=get_data, args=("Thread-2",))
        # threads.append(thing2)
        # thing3 = threading.Thread(target=get_data, args=("Thread-3",))
        # threads.append(thing3)
        # thing4 = threading.Thread(target=get_data, args=("Thread-4",))
        # threads.append(thing4)
        # thing5 = threading.Thread(target=get_data, args=("Thread-5",))
        # threads.append(thing5)
    # 写个for让两件事情都进行
    for thing in threads:
        # setDaemon为主线程启动了线程matter1和matter2
        # 启动也就是相当于执行了这个for循环
        thing.setDaemon(True)
        thing.start()

    for thing in threads:
        thing.join()

#
# # 创建两个线程
# try:
#     _thread.start_new_thread(get_data, ("Thread-1",))
#     _thread.start_new_thread(get_data, ("Thread-2",))
# except:
#     print("Error: 无法启动线程")
# exit()

# 获取单个股票
# get_h_data('600077')
