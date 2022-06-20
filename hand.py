from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import date, timedelta
from prettytable import PrettyTable
import requests
import json
from tqdm import tqdm


def getPrices(departure='hkg', arrival='lax', central_date='2022-08-10', day_range=5, focus_airlines=None):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    browser = webdriver.Chrome(options=opts)
    # browser = webdriver.Chrome()
    recent_min_airlines = []
    one_way_airlines = []
    focus_min_airlines = []
    for _ in range(len(focus_airlines)):
        focus_min_airlines.append([])
    for i in tqdm(range(-day_range, day_range + 1)):
        time.sleep(2)
        delta = timedelta(days=i)
        depart_date = (date(int(central_date.split('-')[0]), int(central_date.split('-')[1]),
                            int(central_date.split('-')[2])) + delta).strftime('%Y-%m-%d')
        browser.get(
            'https://flights.ctrip.com/online/list/oneway-{}-{}?depdate={}&cabin=y_s&adult=1&child=0&infant=0'.format(
                departure, arrival, depart_date))
        time.sleep(5)
        try:
            browser.find_element(By.XPATH, '//div[@class="notice-footer"]/div[@class="btn-group"]').click()
        except Exception as e:
            pass
        time.sleep(2)
        check_height = "return action=document.body.scrollHeight"
        # 初始化现在滚动条所在高度为0
        height = 0
        # 当前窗口总高度
        new_height = browser.execute_script(check_height)

        while height < new_height:
            # 将滚动条调整至页面底部
            for h in range(height, new_height, 650):
                browser.execute_script('window.scrollTo(0, {})'.format(h))
                time.sleep(1)
            height = new_height
            time.sleep(2)
            new_height = browser.execute_script(check_height)

        airline_names = [flight.text for flight in browser.find_elements(By.XPATH, '//div[@class="airline-name"]')]
        airline_idxes = [i for i in range(len(airline_names))]
        depart_times = [flight.text for flight in
                        browser.find_elements(By.XPATH, '//div[@class="depart-box"]/div[@class="time"]')]
        depart_airports = [flight.text for flight in
                           browser.find_elements(By.XPATH, '//div[@class="depart-box"]/div[@class="airport"]')]
        turnarounds = [flight.text for flight in browser.find_elements(By.XPATH, '//div[@class="arrow-box"]')]
        arrive_times = [flight.text for flight in
                        browser.find_elements(By.XPATH, '//div[@class="arrive-box"]/div[@class="time"]')]
        arrive_airports = [flight.text for flight in
                           browser.find_elements(By.XPATH, '//div[@class="arrive-box"]/div[@class="airport"]')]
        flight_times = [flight.text for flight in browser.find_elements(By.XPATH, '//div[@class="flight-consume"]')]
        prices = [flight.text for flight in
                  browser.find_elements(By.XPATH, '//div[@class="flight-price"]//span[contains(@class, "price")]')]
        original_airlines = zip(airline_idxes, airline_names, depart_times, depart_airports, turnarounds, arrive_times,
                                arrive_airports,
                                flight_times,
                                prices)
        airlines = []
        for flight in original_airlines:
            airline = {'price': flight[8][1:], 'airline_name': flight[1], 'time': depart_date,
                       'one_way': 'no' if len(flight[4]) > 0 else 'yes',
                       'depart_airport': flight[3], 'depart_time': flight[2],
                       'arrive_time': flight[5].split('\n')[0], 'notice': '需过境签' if '需过境签' in flight[4] else 'None',
                       'turnaround_cnt': 'None' if len(flight[4]) == 0 else flight[4].split('\n')[
                           0] if '需过境签' not in flight[4] else flight[4].split('\n')[1],
                       'turnaround_time': 'None' if len(flight[4]) == 0 else ' '.join(
                           flight[4].split('\n')[1:]) if '需过境签' not in flight[4] else ' '.join(
                           flight[4].split('\n')[2:]),
                       'jet_lag': 'no jet-lag' if len(flight[5].split('\n')) == 1 else flight[5].split('\n')[1],
                       'arrive_airport': flight[6], 'flight_time': flight[7], 'airline_idx': flight[0]}
            airlines.append(airline)
        recent_min_airlines.append(sorted(airlines, key=lambda x: int(x['price']))[0])
        today_one_way = [a for a in airlines if a['one_way'] == 'yes']
        if len(today_one_way) > 0:
            one_way_airlines.append(sorted(today_one_way, key=lambda x: int(x['price']))[0])
        for ids in range(len(focus_airlines)):
            focus_min_airlines[ids] += [airline for airline in airlines if
                                        airline['airline_name'] == focus_airlines[ids]]

    browser.close()
    return recent_min_airlines, one_way_airlines, focus_min_airlines


# 时间 航空公司 起飞时间 落地时间 飞行时间 价格
def prettyPrint(airlines):
    t = PrettyTable(["时间", "航空公司", "起飞时间", "落地时间", "飞行时间", "是否直飞", "价格"])
    for air in airlines:
        t.add_row([air['time'], air['airline_name'], air['depart_time'], air['arrive_time'], air['flight_time'],
                   air['one_way'],
                   air['price']])
    return str(t)


def pushMessage(title, content):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/79.0.3945.93 Mobile Safari/537.36",
        'Content-Type': 'application/json'
    }
    url = 'http://www.pushplus.plus/send/'
    data = {'token': 'ceabecf946cd4950a6257693e85ced27', 'title': title, 'content': content, 'template': 'html'}
    res = requests.post(headers=headers, url=url, data=json.dumps(data), timeout=10)


def getPricesAndPushMessage(departure='hkg', arrival='lax', central_date='2022-08-10', day_range=5,
                            focus_airlines=None):
    begin_date = (date(int(central_date.split('-')[0]), int(central_date.split('-')[1]),
                       int(central_date.split('-')[2])) + timedelta(days=-day_range)).strftime('%Y年%m月%d日')
    end_date = (date(int(central_date.split('-')[0]), int(central_date.split('-')[1]),
                     int(central_date.split('-')[2])) + timedelta(days=day_range)).strftime('%Y年%m月%d日')
    recent_airlines, one_airlines, concerned_airlines = getPrices(departure=departure, arrival=arrival,
                                                                  central_date=central_date,
                                                                  day_range=day_range, focus_airlines=focus_airlines)
    min_recent_price = sorted(recent_airlines, key=lambda x: int(x['price']))[0]['price']
    title = departure + '->' + arrival
    content = '在{}到{}日期范围内，最低的价格是{}元'.format(begin_date, end_date, min_recent_price)
    content += '\n航班信息如下:\n'
    content += prettyPrint([air for air in recent_airlines if air['price'] == min_recent_price])
    if len(one_airlines) > 0:
        min_one_price = sorted(one_airlines, key=lambda x: int(x['price']))[0]['price']
        content += '\n在{}到{}日期范围内，直飞最低的价格是{}元'.format(begin_date, end_date, min_one_price)
        content += '\n直飞航班信息如下:\n'
        content += prettyPrint([air for air in one_airlines if air['price'] == min_one_price])
    for idx in range(len(focus_airlines)):
        min_price = sorted(concerned_airlines[idx], key=lambda x: int(x['price']))[0]['price']
        content += '\n在{}到{}日期范围内，{}最低的价格是{}元'.format(begin_date, end_date, focus_airlines[idx], min_price)
        content += '\n航班信息如下:\n'
        content += prettyPrint([air for air in concerned_airlines[idx] if air['price'] == min_price])
    pushMessage(title, content)


if __name__ == "__main__":
    getPricesAndPushMessage(focus_airlines=['卡塔尔航空', '新加坡航空', '国泰航空'])
    # getPricesAndPushMessage(arrival='man', central_date='2022-09-12', focus_airlines=['卡塔尔航空', '国泰航空'])
