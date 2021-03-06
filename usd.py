#!/usr/bin/env python
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from datetime import datetime
from decimal import Decimal as D, Context
from statistics import mean
import re
import json


def parse_rate(text):    
    if type(text) is float:
        return D(text).quantize(D('1.00'))

    try:
        # leave only the last 2 digits after the last .
        if ',' in text and '.' in text:
            text = text.replace('.' , '').replace(',','.') 
        elif ',' not in text and '.' in text and text.count('.') > 1:
            text = text.replace('.', '',  text.count('.')-1)

        return D(text)
    except Exception as e:
        print(f'{e}')


def open_rate_source(url):
    try:
        source = Request(url, headers={'User-Agent' : "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"})
        return urlopen(source)
    except HTTPError as e: 
        print(f'Http error opening {source}. Error: {e.code} {e.reason}')
        print(f'Http error, headers: {e.headers}')
        return None
    except: 
        return None


def string_rateparser(start_prefix, string):
    start_pos = string.index(start_prefix) + len(start_prefix)
    return string[start_pos:].strip()


def enparalelovzla_rateparser(text):
    return string_rateparser('Bs. ', text) 


def bcv_rateparser(text):
    return string_rateparser('USD', text) 


def fetch_ig_rate(username, regex, rateparser):    
    source = open_rate_source(f'https://www.instagram.com/{username}')
    if source is None: 
        return D()

    try:
        html_contents = source.read().decode('utf-8').strip()
        m = re.search(regex, html_contents)
        rate = parse_rate(rateparser(m.group(0)))
        #print(f'{username}:{rate}')
        return rate
    except HTTPError as e:
        print(f'{e}')
        return D()
    except Exception as e:
        print(f'!!! could not fetch rate from instagram. Is user: {username} available or reachable?')
        print(f'Error: {e}')
        return D()


def fetch_bcv_rate():
    source = open_rate_source('http://www.bcv.org.ve')
    if(source):
        soup = BeautifulSoup(source,'lxml')
        rate = soup.find('',{'id':'dolar'}).strong.text.strip()
        return parse_rate(rate)
    else: 
        # try instagram?
        try:
            print(f'!!! trying instagram')
            return fetch_ig_rate('bcv.org.ve', r'USD ([0-9.,]*)', bcv_rateparser)
        except: 
            D()


def fetch_dolartoday_url_js():
    return 'https://dxj1e0bbbefdtsyig.woldrssl.net/custom/rate.js'


def fetch_dolartoday_rate():
    source = open_rate_source(fetch_dolartoday_url_js())
    if (source):
        soup = BeautifulSoup(source, 'lxml')
        js_snippet = soup.p.text.strip()
        dt = json.loads(js_snippet[js_snippet.index('{'):])
        return parse_rate(dt["USD"]["dolartoday"])
    else: 
        return D()


def diff_rate(lower, higher):
    diff = higher-lower
    return (diff, diff/lower*100)


if (__name__ == '__main__'):
    print(f'{datetime.now():%d/%m/%Y %H:%M}\n')

    rates = {   
                'bcv' : fetch_bcv_rate(), 
                'dolartoday': fetch_dolartoday_rate(), 
                'enparalelovzla' : fetch_ig_rate('enparalelovzla', r'(AM|PM) PROMEDI(C|O) Bs. ([0-9.,]*)', enparalelovzla_rateparser) 
            }

    for source, rate in rates.items():
        print(f'{source:<15} : {rate:<10,.2f}')
    
    print(f'\n{"Mean / Promedio":<15} : {mean([v for v in rates.values() if v > 0]):<10,.2f}\n')
    
    bcv_diff, pct_diff  = diff_rate(rates["bcv"], rates["dolartoday"])
    print(f'{"dolartoday-bcv":<25}: {bcv_diff:,.2f} ({pct_diff:.2f}%)')

    bcv_diff, pct_diff  = diff_rate(rates["bcv"], rates["enparalelovzla"])
    print(f'{"enparalelovzla-bcv":<25}: {bcv_diff:,.2f} ({pct_diff:.2f}%)')
    
    rates = [('dolartoday',rates['dolartoday']), ('enparalelovzla', rates['enparalelovzla'])]
    max_rate = max(rates, key=lambda rate: rate[1])
    min_rate = min(rates, key=lambda rate: rate[1])

    rate_diff, pct_diff = diff_rate(min_rate[1], max_rate[1])
    print(f'{max_rate[0]}-{min_rate[0]}: {rate_diff:,.2f} ({pct_diff:.2f}%)\n')

