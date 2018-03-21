#!/usr/bin/python
import sys
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import time
import re
import pandas as pd

# count the arguments

arguments = len(sys.argv) - 1
if arguments==0:
   increment=10
elif arguments==1:
     try:
         increment=int(sys.argv[1])
     except:
         print('Error: Expect an integer for a number of metagenomes to retrieve')
         print('"%s" entered'%sys.argv[1])
         os.sys.exit(1)
else:
    print('Error: Too many arguments entered')
    os.sys.exit(1)


####SETTING-UP BROWSER ENVIRONMENT
#download_dir='/media/andriy/5E8D984477029FC2/scripts/Automate_the_boring_stuff_with_python/'
download_dir='/home/andriy/Downloads/'
ex_pt='/media/andriy/5E8D984477029FC2/scripts/Automate_the_boring_stuff_with_python/geckodriver'

fp = webdriver.FirefoxProfile()

fp.set_preference("browser.download.folderList",2)
fp.set_preference("browser.download.manager.showWhenStarting",False)
fp.set_preference("browser.download.dir",download_dir)
fp.set_preference("browser.helperApps.neverAsk.saveToDisk","text/csv application/x-download application/x-gzip")

browser = webdriver.Firefox(firefox_profile=fp, executable_path=ex_pt)
browser.minimize_window()

browser.get('https://signon.jgi.doe.gov/')
time.sleep(2)
emailElem = browser.find_element_by_id('login')
time.sleep(1)
emailElem.send_keys('andriy.sheremet@ucalgary.ca')
pwdElem=browser.find_element_by_id('password')
time.sleep(2)
pwdElem.send_keys('rEsTaRtEr12.')
signInElem=browser.find_element_by_class_name('submit')
time.sleep(1)
signInElem.click()

####STARTING DATA RETRIEVAL

retrieved=0
accessed=0
taxon_link_prefix='https://img.jgi.doe.gov/cgi-bin/mer/'

reset=False
try:
    if not reset:#read from previous
        data=pd.read_pickle('dynamic_metagenomes')
    else:
        data=pd.read_pickle('original_5375_metagenomes')
except:
    print('Error: Database corrupted')
    os.sys.exit(1)


#to_retreive=data[data['retrieved']==0].index
to_retreive=data[(data['retrieved']==0) & (data['error']<=5)].index

if len(to_retreive) == 0:
    print('Nothing to download. \nExiting...')
    os.sys.exit(0)

for i in to_retreive[:increment]:
    accessed+=1
    #data.loc[i, 'taxon_link']='data.loc[i, 'taxon_link']
    url=data.loc[i, 'taxon_link']
    print('Accessing [%d] :'%i, taxon_link_prefix+url)

    #checking if the file exists
#     fname=data.loc[i, 'filename']
#     if fname != '': #use previously obtained filename

#         file_path=download_dir+fname

#         #make it into a function since it is called twice
#         if os.path.exists(file_path) and os.path.getsize(file_path) > 0:#file exists
#             m='Warning: File %s already exists in the download directory. '%fname
#             print(m)
#             print('Skipping download...\n')
#             data.loc[i, 'retrieved']+=1
#             data.loc[i, 'warning']+=1
#             data.loc[i, 'warning_msg']=m+data.loc[i, 'warning_msg']
#             continue



    try:
        browser.get(taxon_link_prefix+url)
        time.sleep(1)
        downButton=browser.find_element_by_class_name('download-btn')
        data.loc[i, 'accessed']+=1
        time.sleep(1)
        downButton.click()
        time.sleep(2)
        download_lnk=browser.find_element_by_link_text('Download')
        download_lnk.click()
        time.sleep(2)
        agree_btn=browser.find_element_by_id('data_usage_policy:okButton')
        agree_btn.click()
        time.sleep(5)
        browser.execute_script('expandAll();')
        time.sleep(5)
    except:
        m="Error: Could Not Retrieve Data. Link: '"+taxon_link_prefix+data.loc[i, 'taxon_link']+"'. \n"
        print(m)
        data.loc[i, 'error_msg']=m+data.loc[i, 'error_msg']
        data.loc[i, 'error']+=1
        continue

    ####DATA DOWNLOADING PART
    search_text='.assembled.faa'
    assembled_links=browser.find_elements_by_partial_link_text(search_text)
    download_links=[]
    for link in assembled_links:
        link_text=link.text

        if link_text[-1*len(search_text):]==search_text:
            #print(link_text)
            download_links.append(link)

    if download_links == []:
        search_text='.tar.gz'
        tar_gz_links=browser.find_elements_by_partial_link_text(search_text)
        download_links=[]
        for link in tar_gz_links:
            link_text=link.text
            if link_text[-1*len(search_text):]==search_text:
                download_links.append(link)

        if download_links == []:

            m='Warning: No Data Available for Download. '
            print(m)
            print('Skipping...\n')
            data.loc[i, 'warning_msg']=m+data.loc[i, 'warning_msg']
            data.loc[i, 'warning']+=1
            continue

    if len(download_links) >1:
        m='\tWarning: Multiple download files present. '
        print(m)
        data.loc[i, 'warning']+=1
        data.loc[i, 'warning_msg']=m+data.loc[i, 'warning_msg']


    for download in download_links:


        fname=download.text.split()[-1] #capturing the filename
        if data.loc[i, ['filename']].str.contains(fname).bool():
            pass
        else:
            data.loc[i, 'filename']+=' '+fname
#         download_pg='https://genome.jgi.doe.gov'+assembled_aa_download[0]
#         data.loc[i, 'download_link']=download_pg
        print('\tDownloading:', fname)

        file_path=download_dir+fname

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:#file exists
            m='\tWarning: File %s already exists in the download directory. '%fname
            print(m)
            print('Skipping download...')
            data.loc[i, 'retrieved']+=1
            data.loc[i, 'warning']+=1
            data.loc[i, 'warning_msg']=m+data.loc[i, 'warning_msg']
            continue

        try:
            browser.set_page_load_timeout(25)
            download.click()
        except TimeoutException as te:
            te=str(te)
            print(te.strip())
            #browser.back()


        for _ in range(400):#wait at least 2000 seconds# wait longer
            time.sleep(5)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                data.loc[i, 'retrieved']+=1
                data.loc[i, 'download_date']=pd.datetime.now()
                retrieved+=1
                print('Downloaded:', fname)
                break



        if not os.path.exists(file_path):
            m="Error: Could not download file: '"+fname+"'. "
            print(m)
            data.loc[i, 'error']+=1
            data.loc[i, 'error_msg']=m+data.loc[i, 'error_msg']
    print('\n')


print('Retrieved %d out of %d links'%(retrieved, accessed))
data.to_pickle('dynamic_metagenomes')
data.to_csv('dynamic_metagenomes.csv')
browser.close()
