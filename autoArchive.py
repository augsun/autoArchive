
# -*- coding: utf-8 -*-
import os
import sys
import time
import hashlib
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import urllib
import urllib.request
import json
import base64

user_home_path = os.environ['HOME']

tempPrj_dir = os.path.dirname(os.path.abspath(__file__))

project_path = '%s/Desktop/crland/mixc' % user_home_path
# project_path = '%s/Desktop/4.15_卡券' % user_home_path

# 打包的 scheme
scheme_name = 'mixc'

# 打包的配置文件路径
exportOptions_path = '%s/Desktop/crland/mixc/_tool/archive/ExportOptions_enterprise.plist' % user_home_path

# 临时目录
temp_path = user_home_path

# 打包出来的 ipa目录 存放路径
ipa_dir_save_path = '%s/Desktop' % user_home_path

# fir 相关
fir_api_token = 'xxx'
fir_app_id = 'xxx'

from_EMail = 'xxx@xxx' # 发送邮箱
password = b'xxx' # base64 过的密码
smtp_server = 'xxx' # 邮箱 smtp

 to_EMails = ['xxx1@xxx', 'xxx2@xxx'] # 要群发的邮箱列表

log_pre_success = '✅ =====>'
log_pre_failure = '❌ =====>'

#
def pull_project():
    print('%s start pull_project' % (log_pre_success))
    os.chdir("%s" % project_path)
    ret = os.system('git pull')
    if ret == 0:
        print('%s pull_project success' % (log_pre_success))
        clean_project()
    else:
        print('%s pull_project failure' % (log_pre_failure))

#
def clean_project():
    print('%s start clean_project' % (log_pre_success))
    ret = os.system('xcodebuild clean')
    if ret == 0:
        print('%s clean_project success' % (log_pre_success))
        build_project()
    else:
        print('%s clean_project failure' % (log_pre_failure))

#
def build_project():
    print('%s start build_project' % (log_pre_success))
    ret = os.system ('xcodebuild -workspace %s.xcworkspace -scheme %s -destination generic/platform=iOS archive -configuration Release ONLY_ACTIVE_ARCH=NO -archivePath %s/%s' % (scheme_name, scheme_name, temp_path, scheme_name))
    if ret == 0:
        print('%s build_project success' % (log_pre_success))
        export_ipa()
    else:
        print('%s build_project failure' % (log_pre_failure))

#
def export_ipa():
    print('%s start export_ipa' % (log_pre_success))
    global ipa_dir_path
    ipa_dir_name_temp = time.strftime('mixc_%m-%d_%H-%M-%S', time.localtime(time.time()))
    ipa_dir_temp = '%s/%s' % (temp_path, ipa_dir_name_temp)
    
    ret0 = os.system ('xcodebuild -exportArchive -archivePath %s/%s.xcarchive -exportPath %s -exportOptionsPlist %s' % (temp_path, scheme_name, ipa_dir_temp, exportOptions_path))

    if ret0 == 0:
        print('%s export_ipa success' % (log_pre_success))

        ipa_dir_name = time.strftime('mixc_%m-%d_%H-%M-%S', time.localtime(time.time()))
        ipa_dir_path = '%s/%s' % (ipa_dir_save_path, ipa_dir_name)
        ret1 = os.system ('mv %s %s' % (ipa_dir_temp, ipa_dir_path))
        if ret1 == 0:
            print('%s mv export_ipa dir success' % (log_pre_success))

            ret2 = os.system('rm -r -f %s/%s.xcarchive' % (temp_path, scheme_name))
            if ret2 == 0:
                print('%s rm .xcarchive success' % (log_pre_success))

                ret3 = os.system('rm -r -f %s' % ipa_dir_temp)
                if ret3 == 0:
                    print('%s rm ipa_dir_temp success' % (log_pre_success))
                    upload_fir()
                else:
                    print('%s rm ipa_dir_temp failure' % (log_pre_failure))
            else:
                print('%s rm .xcarchive failure' % (log_pre_failure))
        else:
            print('%s mv export_ipa dir failure' % (log_pre_failure))
    else:
        print('%s export_ipa failure' % (log_pre_failure))

#
def upload_fir():
    commit_msgs = os.popen('git log --pretty=oneline -20').read()
    commit_msgs = "最近 20 个提交修改:\n %s" % (commit_msgs)



    print('%s start upload_fir' % (log_pre_success))
    ipa_path = '%s/%s.ipa' % (ipa_dir_path, scheme_name)
    ret = os.system('/usr/local/bin/fir p %s -T %s' % (ipa_path, fir_api_token))
    if ret == 0:
        print('%s upload_fir success' % (log_pre_success))
        send_mail()
    else:
        print('%s upload_fir failure' % (log_pre_failure))

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

#
def send_mail():
    print('%s start send_mail' % (log_pre_success))
    download_URL, master_release_downloadURL = fir_download_URL()

    appInfo = fir_app_Info()
    master_release = appInfo['master_release']
    created_at = master_release['created_at']
    created_at_Array = time.localtime(created_at)
    created_at_Time = time.strftime('%m-%d %H:%M:%S', created_at_Array)

text = 'Dear:\n\r最新 mixc_iOS_客户端 项目已打包完毕，请前往下载！\n' +\
            master_release_downloadURL + \
            '\n\n注:\n- 若没收到该最新邮件, 可从如下地址下载最新包(该地址为固定地址, 永远对应最新的包. 上面带 release_id 的地址可用于日后安装旧版本, 如回退验证.):\n' + \
            download_URL + \
            '\n\n- 该邮件为自动打包完成后发出.''

    msg = MIMEText(text, 'plain', 'utf-8')
    msg['From'] = _format_addr('Sun <%s>' % from_EMail)
    msg['To'] = ','.join(to_EMails)
    msg['Subject'] = Header('mixc_iOS_客户端_%s' % (created_at_Time), 'utf-8').encode()

    try:
        server = smtplib.SMTP()
        server.connect(smtp_server, 25)
        server.login(from_EMail, base64.b64decode(password).decode())
        server.sendmail(from_EMail, to_EMails, msg.as_string())
        server.quit()
        print('send_mail to:\n%s' %(to_EMails))
        print('%s send_mail success' % (log_pre_success))
    except smtplib.SMTPException:
        print('%s send_mail failure' % (log_pre_failure))

#
def fir_app_Info():
    url = 'http://api.fir.im/apps?api_token=%s' % (fir_api_token)
    res = urllib.request.urlopen(url).read()
    appInfoObj = json.loads(res)
    
    items = appInfoObj['items'];
    
    for item in items:
        id = item['id']
        if id == fir_app_id:
            master_release = item['master_release']
            return item

#
def fir_download_URL():
    url = 'http://api.fir.im/apps/%s?api_token=%s' % (fir_app_id, fir_api_token)
    res = urllib.request.urlopen(url).read()
    appInfo = json.loads(res)

    master_release_id = appInfo['master_release_id']
    short = appInfo['short']
    downloadURL = 'http://fir.im/%s' % (short)
    master_release_downloadURL = '%s?release_id=%s' % (downloadURL, master_release_id)
    return downloadURL, master_release_downloadURL

def main():
    pull_project()
    return

#
main()









