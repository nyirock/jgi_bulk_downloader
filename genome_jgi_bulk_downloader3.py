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
#download_dir='/home/andriy/Downloads/'
#download_dir='/home/pi/bulk_downloader/bulk_downloader/Downloads/'
#download_dir='K:\\Downloads' #### windows
#ex_pt='/media/andriy/5E8D984477029FC2/scripts/Automate_the_boring_stuff_with_python/geckodriver'
#ex_pt='/home/pi/bulk_downloader/bulk_downloader/geckodriver'
#ex_pt='K:\\bulk_downloader\\win\\geckodriver.exe' ### windows

#download_dir='/home/andriy/Downloads/finished_bact_genomes/'
#ex_pt='/media/andriy/5E8D984477029FC2/scripts/jgi_bulk_downloader/geckodriver'

download_dir="/home/dunfield/Documents/andriy/selected_genomes/"
ex_pt="/home/dunfield/PycharmProjects/jgi_bulk_downloader/geckodriver"


fp = webdriver.FirefoxProfile()

fp.set_preference("browser.download.folderList",2)
fp.set_preference("browser.download.manager.showWhenStarting",False)
fp.set_preference("browser.download.dir",download_dir)
fp.set_preference("browser.helperApps.neverAsk.saveToDisk","text/csv application/x-download application/x-gzip")

browser = webdriver.Firefox(firefox_profile=fp, executable_path=ex_pt)
#browser.minimize_window()
#browser.set_window_position(25000, 0)
browser.get('https://signon.jgi.doe.gov/')
time.sleep(2)
emailElem = browser.find_element_by_id('login')
time.sleep(1)
#emailElem.send_keys('andriy.sheremet@ucalgary.ca')
emailElem.send_keys('dunfield.bio@gmail.com')
pwdElem=browser.find_element_by_id('password')
time.sleep(2)
#pwdElem.send_keys('rEsTaRtEr12.')
pwdElem.send_keys('dunfield2014')
signInElem=browser.find_element_by_class_name('submit')
time.sleep(1)
signInElem.click()

####STARTING DATA RETRIEVAL
#download_bundle.tar.gz goes as a priority download

retrieved=0
accessed=0
taxon_link_prefix='https://img.jgi.doe.gov/cgi-bin/mer/'

reset=False
try:
    if not reset:#read from previous
        data=pd.read_pickle('2365_selected_genomes')
    else:
        data=pd.read_pickle('2365_original_selected_bacterial_genomes')
except:
    print('Error: Database corrupted')
    os.sys.exit(1)


#to_retreive=data[data['retrieved']==0].index
to_retreive=data[(data['retrieved']==0) & (data['error']<=15)].index

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
    search_text = 'download_bundle.tar.gz'
    assembled_links=browser.find_elements_by_partial_link_text(search_text)
    download_links=[]
    for link in assembled_links:
        link_text=link.text

        if link_text[-1*len(search_text):]==search_text:
            #print(link_text)
            download_links.append(link)

    if download_links == []:
        search_text=str(data.loc[i, 'taxon_oid'])+'.tar.gz'
        tar_gz_links=browser.find_elements_by_partial_link_text(search_text)
        download_links=[]
        for link in tar_gz_links:
            link_text=link.text
            if link_text[-1*len(search_text):]==search_text:
                download_links.append(link)


    if download_links == []:
        search_text = '.tar.gz'
        tar_gz_links = browser.find_elements_by_partial_link_text(search_text)
        download_links = []
        for link in tar_gz_links:
            link_text = link.text
            if link_text[-1 * len(search_text):] == search_text:
                download_links.append(link)

        if download_links == []:

            m='Warning: No Data Available for Download. '
            print(m)
            print('Skipping...\n')
            data.loc[i, 'warning_msg']=m+data.loc[i, 'warning_msg']
            data.loc[i, 'warning']+=1
            continue

    if len(download_links) >1:
        m='Warning: Multiple download files present. '
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

                if fname == 'download_bundle.tar.gz':
                    new_name = str(data.loc[i, 'taxon_oid']) + "_" + fname
                    print("Renaming " + fname + " to " + new_name)

                    old_file = os.path.join(download_dir, fname)
                    new_file = os.path.join(download_dir, new_name)



                    data.loc[i, 'filename'] += ' ' + new_name
                    fname = new_name
                    file_path = download_dir + fname

                    #basic renaming instead of more complicated case works
                    os.rename(old_file, new_file)

                    ##################little more complicated than option to account overwriting
                    # try:
                    #     os.rename(old_file, new_file)
                    # except:
                    #     if os.path.exists(file_path) and os.path.getsize(file_path) > 0:  # file exists
                    #         m = '\tWarning: Renaming warning. File %s already exists in the download directory. ' % fname
                    #         print(m)
                    #         data.loc[i, 'warning'] += 1
                    #         data.loc[i, 'warning_msg'] = m + data.loc[i, 'warning_msg']
                    #     else:
                    #         m = '\tError: Renaming error. File %s already exists in the download directory. ' % fname
                    #         retrieved -= 1
                    #         data.loc[i, 'error'] += 1
                    #         data.loc[i, 'error_msg'] = m + data.loc[i, 'error_msg']
                    #         #deleting download_bundle.tar.gz
                    #         os.remove(old_file)

                break

        if not os.path.exists(file_path):
            m="Error: Could not download file: '"+fname+"'. "
            print(m)
            data.loc[i, 'error']+=1
            data.loc[i, 'error_msg']=m+data.loc[i, 'error_msg']
    
    
    if accessed % 5 == 0:
        data.to_pickle('finished_genomes')
    print('\n')


print('Retrieved %d out of %d links'%(retrieved, accessed))
data.to_pickle('2365_selected_genomes')
data.to_csv('2365_selected_genomes.csv')
browser.close()
