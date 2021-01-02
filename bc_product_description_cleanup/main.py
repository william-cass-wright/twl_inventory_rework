'''
Author: William Wright

Cleans product descriptions formatting in html, based off of standard patterns. 
Edge cases to be evaluated separately. 
'''

import re
import os

import numpy as np
import pandas as pd
import imgkit
import sys
from PIL import Image

from my_utils import list_files_in_directory, process_cols_v2
from my_configs import prod_ids_filepaths, product_export_file, output_folder_html, \
                        output_folder_results, imgs_bool, regex_dict
from clean_description import clean_description


def product_df(filepath):
    '''product_df docstring
    return most recent product export from bigcommerce'''
    df = pd.read_csv(filepath)
    df.columns = process_cols_v2(df.columns)
    df = df.loc[df.item_type == 'Product']
    return df

def gen_preview_image(old_html,new_html,base_name,output_folder_results,output_folder_html):
    '''docstring for gen_preview_image'''
    # print('gen images')
    image_names = [output_folder_html+'/'+base_name+'_old.png', output_folder_html+'/'+base_name+'_new.png']
    imgkit.from_string(old_html, image_names[0])
    imgkit.from_string(new_html, image_names[1])
    images = [Image.open(x) for x in image_names]
    widths, heights = zip(*(i.size for i in images))
    total_width = max(widths)
    max_height = sum(heights) + 10
    new_im = Image.new('RGB', (total_width, max_height))
    offset = 0
    for im in images:
        new_im.paste(im, (0,offset))
        offset += im.size[1]+ 10
    # print(output_folder_results+'/'+base_name+'.png')
    new_im.save(output_folder_results+'/'+base_name+'.png')

def run_process(df,prod_ids,output_folder_results,output_folder_html,folder_name):
    '''run_process docstring'''
    res = {}
    # print('run')
    for _id in prod_ids:
        temp = df.loc[df.product_id == _id]
        if len(temp)>0:
            _name = process_cols_v2(temp.product_name)[0]
            _sku = str(temp.product_code_sku.values[0])
            _cateogry = str(temp.category.values[0])
            base_name = str(_id)+'_'+_name+'_'+_sku
            old_html = temp.product_description.values[0]
            if isinstance(old_html,str):
                desc = clean_description(old_html, regex_dict)
                d = desc.flight_chars_dict()
                new_html = desc.clean()
                _data = [temp.product_name.values[0],_sku,_cateogry,base_name,old_html,new_html,
                    len(re.findall('please note',new_html.lower())),
                    len(re.findall('flight characteristics',new_html.lower())),
                    len(re.findall('information about',new_html.lower()))
                    ]
                _data_cols = ['id','name','sku','category','base_name','old_html','new_html','count_please_note',
                    'count_flight_chars','count_info_about'
                    ]
                if len(d)==4:
                    res[_id] = _data+[d[i] for i in d]
                    flight_char_cols = [i for i in d]
                else:
                    res[_id] = _data+[np.nan]*4
                
                if imgs_bool:
                    try:
                        # videos incompatible with command line tool
                        old_html = re.sub('<p><!-- mceItemMediaService.+?mceItemMediaService --></p>','',old_html)
                        gen_preview_image(old_html,new_html,base_name,output_folder_results,output_folder_html)
                    except OSError as e:
                        print(e)
            else:
                print(base_name,' skipped')
        else:
            print(_id, ' --> no match found')
    df = pd.DataFrame(res).T
    df.reset_index(inplace=True)
    df.columns = _data_cols+flight_char_cols
    df['href_check'] = df.new_html.apply(lambda x: 'href' in x)
    df.to_csv(folder_name+'.csv',index=False)

def create_directory(folders):
    '''create_directory docstring'''
    for folder in folders:
        try:
            os.mkdir(folder)
        except FileExistsError as e:
            print(e)

def main():
    '''main docstring'''
    df = product_df(product_export_file)
    for prod_ids_filepath in prod_ids_filepaths:
        prod_ids = list(product_df(prod_ids_filepath).product_id) # disc golf set 01
        folder_name = prod_ids_filepath.split('/')[-1].replace('.csv','')
        folders = [
            'results',
            'results/'+folder_name,
            'results/'+folder_name+'/'+output_folder_results,
            'results/'+folder_name+'/'+output_folder_html
            ]
        create_directory(folders)
        # print('start')
        try:
            cwd = os.getcwd()
            os.chdir(cwd+'/results/'+folder_name)
            run_process(df,prod_ids,output_folder_results,output_folder_html,folder_name)
            # print('done')
        finally:
            os.chdir(cwd)

if __name__ == '__main__':
    main()