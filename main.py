import requests
from bs4 import BeautifulSoup
from lxml import etree
from fake_useragent import UserAgent
import time
import json


def getHTMLText(url: str) -> str:
    # noinspection PyBroadException
    try:
        # 伪装头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE '
        }
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except Exception as e:
        return str(e)


def parseHTML(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup


def getProxies(page) -> list:
    all_ips = []
    # http://www.66ip.cn/1.html
    for i in range(1, page + 1):
        s = etree.HTML(getHTMLText('http://www.66ip.cn/{}.html'.format(i)))
        ip_xpath = '//table/tr[position()>1]/td[1]/text()'
        port_xpath = '//table/tr[position()>1]/td[2]/text()'
        ips = s.xpath(ip_xpath)
        ports = s.xpath(port_xpath)
        all_ips += ([ip + ':' + port for ip, port in zip(ips, ports)])
    res_ips = []
    for ip in all_ips:
        proxies = {"http": "http://{}".format(ip), "https": "https://{}".format(ip)}
        try:
            r = requests.get("https://www.baidu.com/", headers={'User-Agent': str(UserAgent(verify_ssl=False).random)},
                             proxies=proxies,
                             timeout=20)
            r.raise_for_status()
            res_ips.append(ip)
        except Exception as e:
            print(e)
    return res_ips


def getPrice(departure='hkg', destination='lax', date=None):
    time.sleep(3)
    url = 'https://flights.ctrip.com/online/list/oneway-{}-{}?depdate=2022-07-24&cabin=y_s&adult=1&child=0&infant=0'.format(
        departure, destination)
    r = getHTMLText(url)
    print(r)
    s = etree.HTML(r)
    # flight_xpath = "//div[contains(@class,'flight-box')]//div[contains(@class,'flight-airline')]/text()"
    flight_xpath = "//div/text()"
    print(s.xpath(flight_xpath))


getPrice()
