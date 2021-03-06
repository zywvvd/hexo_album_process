import config
import json
import os 
import cv2
import shutil
import logging
import time
from getinfo import PhotoExifInfo


def log_init():
    """
    initialize logging 
    save the logging object in `config.Parameters.Logging_Object`
    
    after this operation,
    we could save logs with sample orders such as `logging.debug('test debug')` `logging.info('test info')` 
    logging level : debug < info < warning <error < critica
    """
    log_file_path = os.path.join(config.Parameters.Uploading_Temp_Image_Path, config.Parameters.Log_File_Name)
    if os.path.exists(log_file_path):
        # open log file as  mode of append
        open_type = 'a'
    else:
        # open log file as  mode of write
        open_type = 'w'
        
    logging.basicConfig(
    
        # 日志级别,logging.DEBUG,logging.ERROR
        level = logging.INFO,  

    # 日志格式: 时间、代码所在文件名、代码行号、日志级别名字、日志信息
        #format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        format = '%(asctime)s : %(message)s',
        
        # 打印日志的时间
        datefmt = '%Y-%m-%d %H:%M:%S',
    
        # 日志文件存放的目录（目录必须存在）及日志文件名
        filename = log_file_path, 
    
        # 打开日志文件的方式
        filemode = open_type
    )    
    
    config.Parameters.Logging_Object = logging


def log(message):
    """
    print message to console and than save it to log 
    """
    print(message)
    if config.Parameters.Logging_Object:
        config.Parameters.Logging_Object.info(message)
    else:
        raise TypeError('there is sth wrong with the object of logging in config ')


def dir_check(dir_path):
    """
    check if `dir_path` is a real directory path
    """
    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path) 
        except Exception as err:
            print(f'failed to make dir {dir_path}, error {err}')
        finally:
            log(f'{dir_path} does not exist and we have built it for you ')
            
            
def environment_check():
    """
    check album environment, try to fix the matters if sth goes wrong
    """
    
    ## check important dirs
    assert os.path.isdir(config.Parameters.Image_Root_Path) ,f"image root dir {config.Parameters.Image_Root_Path} does not exist"
    assert os.path.isdir(config.Parameters.Hexo_Root_Path) ,f"hexo root dir {config.Parameters.Hexo_Root_Path} does not exist"
    
    dir_check(config.Parameters.Uploading_Temp_Image_Path)
    
    ## check image width, I think it shold not < 200
    config.Parameters.Image_Resize_Width = max(int(config.Parameters.Image_Resize_Width), 200)
    
    ## initialize logging
    log_init()
    
    ## image_info_get object
    config.Parameters.Image_Info_Get_Object = PhotoExifInfo()
    
      
def init_json_create(json_path):
    """
    init a json file to `json_path`
    """
    assert os.path.basename(json_path).split('.')[-1]=='json',f'{json_path} should be a path of json file '
    assert os.path.isdir(os.path.split(json_path)[0]), 'the folder does not exist'
    
    now = time.localtime()
    info_dict={}
    
    ## time
    my_time={
        'year':now.tm_year,\
        'month':now.tm_mon,\
        'day':now.tm_mday
          }
    info_dict['time'] = my_time
    
    ## type
    info_dict['type'] = 'album type'
    
    ## model
    info_dict['model'] = ''
    
    ## position
    position = {
        'city':'beijing',\
        'street':'Tiananmen'
    }
    info_dict['position'] = position
    
    ## title
    info_dict['title'] = 'Album title'
    
    ## balabala
    info_dict['balabala'] = 'description of album'
    
    with open(json_path, mode='w') as fp:
        json.dump(info_dict, fp, indent=3)
        log(f'make initial json file {json_path}')
            
            
def image_compression_and_save(src_dir, tar_dir):
    """
    compress and move images from src to tar 
    """
    sub_image_dirs = os.listdir(src_dir)
    
    for sub_image_dir in sub_image_dirs:
        src_sub_image_path = os.path.join(src_dir, sub_image_dir)
        tar_sub_image_path = os.path.join(tar_dir, sub_image_dir)
        
        ## check tar dir
        dir_check(tar_sub_image_path)
        
        file_list = os.listdir(src_sub_image_path)
        for item in file_list:
            extension = item.split('.')[-1]
            
            if extension.lower() in config.Parameters.Image_Extension_List:
                ## is image file
                image_path = os.path.join(src_sub_image_path, item)
                
                tar_image_path = os.path.join(tar_sub_image_path, item)
                
                if not os.path.exists(tar_image_path) or config.Parameters.Whether_Overwrite_Old_Temp_File:
                    ## new file or overwrite
                    
                    image = cv2.imread(image_path)
                    image_shape = image.shape
                    
                    if image_shape[1] >= config.Parameters.Image_Resize_Width:
                        ## need compression
                        new_width = int(config.Parameters.Image_Resize_Width)
                        new_height = int(config.Parameters.Image_Resize_Width/image_shape[1]*image_shape[0])
                        
                        new_image = cv2.resize(image,(new_width, new_height) )
                        cv2.imwrite(tar_image_path, new_image)
                        log(f'image {os.path.join(sub_image_dir,item)} has been resized to {(new_width, new_height)} and moved to temp dir')
                        
                    else:
                        ## small image, copy directly
                        shutil.copy(image_path, tar_image_path)
                        log(f'image {os.path.join(sub_image_dir,item)} has been moved to temp dir')
                           
        
def deal_with_sub_json(src_dir, tar_dir):
    """
    deal with sub json files in each sub dir
    """
    sub_image_dirs = os.listdir(src_dir)
    
    for sub_image_dir in sub_image_dirs:
        
        src_sub_image_path = os.path.join(src_dir, sub_image_dir)
        tar_sub_image_path = os.path.join(tar_dir, sub_image_dir)
        
        ## check tar dir
        dir_check(tar_sub_image_path)    
        
        src_info_json_file_path = os.path.join(src_sub_image_path, config.Parameters.Album_Ddescription_File_Name)
        
        if not os.path.exists(src_info_json_file_path):
            init_json_create(src_info_json_file_path)
        else:
            print(f'{src_info_json_file_path} found')
            
        with open(src_info_json_file_path) as fp:
            album_info = json.load(fp)
        
        file_list = os.listdir(src_sub_image_path)
        
        image_info_list = []
        
        for item in file_list:
            extension = item.split('.')[-1]
            
            if extension.lower() in config.Parameters.Image_Extension_List:
                ## is image file
                image_path = os.path.join(src_sub_image_path, item)
                
                assert not config.Parameters.Image_Info_Get_Object is None, "Image_Info_Get_Object should be a instance "
                image_info_dict = config.Parameters.Image_Info_Get_Object.get_image_info(image_path)                
                
                image_info_dict['url'] = config.Parameters.Image_Url_Prefix+sub_image_dir+'/'+item
                
                image_info_list.append(image_info_dict)
                
        album_info['image_info'] = image_info_list
        album_info['directory'] = sub_image_dir
        
        tar_info_json_file_path = os.path.join(tar_sub_image_path, config.Parameters.Album_Ddescription_File_Name)      
        
        with open(tar_info_json_file_path,'w',encoding='utf-8') as fp:
            json.dump(album_info, fp, indent=3, ensure_ascii=False)
            log(f'json file of image dir {sub_image_dir} created')
            
            
def json_integrate(temp_root):
    '''
    integrate json files to a single file
    '''
    sub_image_dirs = os.listdir(temp_root)
    
    album_dict = {}
    
    album_json_list = []
    
    for sub_image_dir in sub_image_dirs:  
        if os.path.isdir(os.path.join(temp_root,sub_image_dir)):
            json_file_path = os.path.join(temp_root,sub_image_dir, config.Parameters.Album_Ddescription_File_Name)   
            assert os.path.exists(json_file_path),f'file {json_file_path} not flund'
            
            with open(json_file_path) as fp:
                json_dict = json.load(fp)
            
            album_json_list.append(json_dict)
            
    album_dict['album'] = album_json_list
    
    integrate_json_path = os.path.join(temp_root, config.Parameters.Album_Total_Json)
    with open(integrate_json_path, mode='w', encoding='utf-8') as fp:
        json.dump(album_dict, fp, ensure_ascii=False, indent=3)
        log(f'total json {integrate_json_path} saved')
        
    return album_dict
        
def make_dir_json_md_of_album(temp_root, hexo_photos_path, album_dict):
    '''
    save md files to hexo source/photos dir
    '''
    assert os.path.isdir(hexo_photos_path) ,'hexo photos path {hexo_photos_path} does not exist'
    
    src_album_json_path = os.path.join(temp_root, config.Parameters.Album_Total_Json)
    assert os.path.exists(src_album_json_path), f'album json file {src_album_json_path} not found'
    tar_album_json_path = os.path.join(hexo_photos_path, config.Parameters.Album_Total_Json)
    
    shutil.copy(src_album_json_path, tar_album_json_path)
    log(f"json file {config.Parameters.Album_Total_Json} moved to hexo dir")
    for sub_image_dict in album_dict['album']:
        src_json_path = os.path.join(temp_root, sub_image_dict['directory'], config.Parameters.Album_Ddescription_File_Name)
        assert os.path.exists(src_json_path), f'sub json file {src_json_path} not found'
        
        tar_json_path = os.path.join(hexo_photos_path, sub_image_dict['directory'], config.Parameters.Album_Ddescription_File_Name)
        image_dir = os.path.join(hexo_photos_path, sub_image_dict['directory'])
        dir_check(image_dir)
        
        shutil.copyfile(src_json_path, tar_json_path)
        log(f"json file {sub_image_dict['directory'] +'_'+ config.Parameters.Album_Ddescription_File_Name} moved to hexo dir")
        
        with open(os.path.join(image_dir,config.Parameters.Album_Md_File_Name),'w', encoding='utf-8') as fp:
            fp.writelines('---'+'\n')
            fp.writelines('title: '+sub_image_dict['title']+'\n')
            fp.writelines('date: '+str(sub_image_dict['time']['year'])+'-'+str(sub_image_dict['time']['month'])+'-'+str(sub_image_dict['time']['day'])+'\n')
            fp.writelines('type: photography'+'\n')
            fp.writelines('album: '+sub_image_dict['directory']+'\n')
            fp.writelines('---'+'\n')
            log(f'create md file of {os.path.join(image_dir,config.Parameters.Album_Md_File_Name)}')