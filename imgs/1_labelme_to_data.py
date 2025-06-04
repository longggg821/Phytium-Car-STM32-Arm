import os

files=os.listdir('./imgs/1筛选/')

fdata=open('./imgs/1筛选/1.txt','wb')
null=None
fdata.write('{\r\n'.encode('UTF-8'))
for file in files:
    if not file.endswith('.jpg'):
        continue
    fname=file.split('.')[0]
    print(fname)
    imgjson=eval(open('./imgs/1筛选/'+fname+'.json','rb').read().decode('UTF-8'))
    dis='%.2f'%(47.0-float(7*(int(imgjson['shapes'][0]['points'][1][1])-int(imgjson['shapes'][0]['points'][0][1])))/35.0)#input('距离：')
    print('距离：',dis)
    is_lock_original=input('是否归位：')
    lock_angle=input('锁孔角度：')
    is_key_in=input('钥匙插入：')
    key_angle=input('钥匙角度：')
    fdata.write(('\t"%s": {"x": %s, "y": %s, "w": %s, "h": %s, "distance": %s, "is_lock_original": %s, "lock_angle": %s, "is_key_in": %s, "key_angle": %s},\r\n' % (
        file,
        int(imgjson['shapes'][0]['points'][0][0]), 
        int(imgjson['shapes'][0]['points'][0][1]), 
        int(imgjson['shapes'][0]['points'][1][0])-int(imgjson['shapes'][0]['points'][0][0]), 
        int(imgjson['shapes'][0]['points'][1][1])-int(imgjson['shapes'][0]['points'][0][1]),
        dis,
        is_lock_original,
        lock_angle,
        is_key_in,
        key_angle,
    )).encode('UTF-8'))
    
    # for v in imgjson['shapes'][1:]:
    #     fdata.write((', {"x": %s, "y": %s, "w": %s, "h": %s}'%(int(v['points'][0][0]), int(v['points'][0][1]), int(v['points'][1][0])-int(v['points'][0][0]), int(v['points'][1][1])-int(v['points'][0][1]))).encode('UTF-8'))
fdata.write('}'.encode('UTF-8'))
fdata.close()