# -*- coding: utf-8 -*-
"""
Created on Tue May 19 13:55:38 2020

@author: XYZ
"""

import scrapy
from massmednew.items import MassmednewItem
from selenium import webdriver
from scrapy import Selector
import json
import re
import pandas as pd
import datetime

#driver = webdriver.Chrome(r'C:\Users\xyzal\Downloads\chromedriver_win32\chromedriver.exe')

#driver = webdriver.Chrome(executable_path=r'C:\Users\xyzal\Downloads\chromedriver_win32\chromedriver.exe')


class MassMedScrape(scrapy.Spider):
    name = 'massmednew'
    csv = '.csv'
    allowed_domains = ['massmed.org']
    start_urls = ['http://www.massmed.org/Continuing-Education-and-Events/Online-CME/Online-CME-Courses/#.Xrw_oKhKhyx']
    #start_urls = webdriver.get('http://www.massmed.org/Continuing-Education-and-Events/Online-CME/Online-CME-Courses/#.Xrw_oKhKhyx')
        
    
    def start_requests( self ):
        urls = ['http://www.massmed.org/Continuing-Education-and-Events/Online-CME/Online-CME-Courses/#.Xrw_oKhKhyx']
        for url in urls:
            yield scrapy.Request( url = url, callback = self.parse)        
    
    def parse(self, response):
        self.driver = webdriver.Chrome()
        self.driver.get(response.url)
        for a in response.xpath('//*[@id="ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolderContent_mainContent"]/a'):
            href = a.xpath('./@href')
            url = href[0].extract()
            #baseUrl = 'massmed.org'
            yield response.follow(url = url, callback = self.parse_pages)
        self.driver.close()
        
    def parse_pages(self, response):    
        #driver = webdriver.Chrome(executable_path=r'C:\Users\xyzal\Downloads\chromedriver_win32\chromedriver.exe')
        c = MassmednewItem()
        content = response.css('div.modCourseModule')
            #title_all = response.xpath('//*[@id="ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolderContent_mainContent"]/a/text()').extract()
            #title_set = pd.Series(title_all)
            #info_str = response.xpath('//*[@id="ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolderContent_mainContent"]/h6/text()').extract()
            #info_set = pd.Series(info_str)
        try:
            c['title'] = response.xpath('//*[@id="aspnetForm"]/div[3]/div[2]/div[3]/div[3]/div/h1/text()').get()
        except:
            c['title'] = 'Title field not found'
                
            #credit_prep = info_str.split('|')[0].strip()
            #credit = credit_prep.split(' ')[0]
            #form = info_str.split('|')[2].strip()
            #item['Title'] = title_set.values
            #item['Credit'] = credit
            #item['Format'] = form
            #c['Info'] = info_set.values
        
        #CREDIT
        try:
            credit_title = content.xpath('.//*[contains(text(), "CME Credit")]')
            credit = credit_title.xpath('./following-sibling::text()').get().strip('\n ')
            c['credit'] = credit
        except:
            c['credit'] = 'Credit field not found'
        
        #OBJECTIVES
        try:
            obj_title = response.xpath('//*[contains(text(), "Learning Objectives")]')
            obj_list = obj_title.xpath('./following::ul/li/text()').getall()
            str_obj = ''.join(str(e) for e in obj_list)
            str_obj = str_obj.replace('.', '. ')
            str_obj = str_obj.strip(' Subsidiaries & AffiliatesToolsFind UsNotices')
            c['educational_objectives'] = str_obj
        except:
            c['educational_objectives'] = 'Objectives field not found'
        
        #OVERVIEW
        try:
            list_overview = response.xpath('//*[@id="aspnetForm"]/div[3]/div[2]/div[3]/div[3]/div/div[2]/p[1]/text()').getall()
            str_overview = ''.join(str(e) for e in list_overview)
            c['overview'] = str_overview
        except:
            c['overview'] = 'Overview field not found'
        
        #TITLE
        try:
            aud_title = response.xpath('//*[contains(text(), "Intended Audience")]')
            #p tag
            aud_p = aud_title.xpath('./following::p[1]/text()').get()
            #br tag
            aud_br = aud_title.xpath('./following::br[0]/text()').get()
            if len(aud_p) > 1:
                c['audience'] = aud_p
            elif len(aud_br) > 1:
                c['audience'] = aud_br
        except:
            c['audience'] = 'Audience field not found'
        
        #FORMAT
        try:
            format_title = response.xpath('//*[contains(text(), "Format")]')
            format_pb = format_title.xpath('./following-sibling::text()').get().strip(': ')
            c['fmat'] = format_pb
        except:
            c['fmat'] = 'Format field not found'
        
        #FEE
        try:
            fee_title = response.xpath('//*[contains(text(), "Fees")]')
            #free
            fee_free = fee_title.xpath('./following-sibling::text()').get().strip(': ')
            if fee_free == 'Free':
                c['member_price'] = 'Free'
                c['non-member_price'] = 'Free'
            else:
                fee_list = fee_title.xpath('./following-sibling::text()').getall()
                member_list = fee_title.xpath('./following-sibling::text()').getall()
                new_mem_list = [item.replace(' \xa0', ' ') for item in member_list]
                new_mem_list = [item.replace('\xa0', '') for item in new_mem_list]
                mem_phy_matchers = ['Massachusetts Medical Society (MMS) Member Physician']
                mem_res_student_matchers = ['MMS Resident/Student Member']
                non_mem_phy_matchers = ['Non-MMS Member Physician']
                non_mem_res_student_matchers = ['Non-Member Resident/Student']
                other_matchers = [' Allied Health Professional/Other']
                mem_phy_matching = [s for s in new_mem_list if any(xs in s for xs in mem_phy_matchers)]
                mem_res_student_matching = [s for s in new_mem_list if any(xs in s for xs in mem_res_student_matchers)]
                non_mem_phy_matching = [s for s in new_mem_list if any(xs in s for xs in non_mem_phy_matchers)]
                non_mem_res_student_matching = [s for s in new_mem_list if any(xs in s for xs in non_mem_res_student_matchers)]
                other_matching = [s for s in new_mem_list if any(xs in s for xs in other_matchers)]
                def price(price_list):
                    return str(price_list).split(': ')[1].strip("']$")
                if len(mem_phy_matching)>1:
                    mem_phy_price = price(mem_phy_matching)
                else:
                    mem_phy_price = 'N/A'
                if len(mem_res_student_matching)>1:
                    mem_res_student_price = price(mem_res_student_matching)
                else:
                    mem_res_student_price = 'N/A'
                if len(non_mem_phy_matching)>1:
                    non_mem_phy_price = price(non_mem_phy_matching)
                else:
                    non_mem_phy_price = 'N/A'
                if len(non_mem_res_student_matching)>1:
                    non_mem_res_student_price = price(non_mem_res_student_matching)
                else:
                    non_mem_res_student_price = 'N/A'
                if len(other_matching)>1:
                    other_price = price(other_matching)
                else:
                    other_price = 'N/A'
                c['member_price'] = {"Physician":mem_phy_price, "Resident/Student":mem_res_student_price}
                c['non_member_price'] = {"Physician":non_mem_phy_price, "Resident/Student":non_mem_res_student_price, "Applied Health Professional/Other":other_price}
        except:
            c['member_price'] = 'Member field not found'
        #DATE
        try:
            activity_term = content.xpath('.//*[contains(text(), "Original Release Date: ")]')
            date_list = activity_term.xpath('./text()').getall()
            release_date = date_list[0].strip('\n\nOriginal Release Date:')
            release_date_format = datetime.strptime(release_date, '%B %d, %Y')
            release_date = release_date_format.strftime('%m/%d/%Y')
            expiration_date = date_list[2].strip('\n\nTermination Date:')
            expiration_date_format = datetime.strptime(expiration_date, '%B %d, %Y')
            expiration_date = expiration_date_format.strftime('%m/%d/%Y')
            c['release_date'] = release_date
            c['expiry_date'] = expiration_date
        except:
            c['release_date'] = 'Release field not found'
        c['link'] = response.url
        c['educational_provider'] = 'Massachusetts Medical Society'
        c['date_scraped'] = datetime.datetime.today().strftime('%m/%d/%Y')
        yield c