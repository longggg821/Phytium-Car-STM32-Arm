import os

files=os.listdir('./imgs/2测试筛选/')

fdata=open('./imgs/2测试筛选/2.txt','wb')
null=None
fdata.write('{\r\n'.encode('UTF-8'))
for file in files:
    if not file.endswith('.jpg'):
        continue
    fname=file.split('.')[0]
    fdata.write(('\t"%s": ['%(file)).encode('UTF-8'))
    if not os.path.exists('./imgs/2测试筛选/'+fname+'.json'):
        fdata.write(']\r\n'.encode('UTF-8'))
        continue
    imgjson=eval(open('./imgs/2测试筛选/'+fname+'.json','rb').read().decode('UTF-8'))
    balls=imgjson['shapes']

    fdata.write(('{"x": %s, "y": %s, "w": %s, "h": %s}'%(int(balls[0]['points'][0][0]), int(balls[0]['points'][0][1]), int(balls[0]['points'][1][0])-int(balls[0]['points'][0][0]), int(balls[0]['points'][1][1])-int(balls[0]['points'][0][1]))).encode('UTF-8'))
    
    for v in balls[1:]:
        fdata.write((', {"x": %s, "y": %s, "w": %s, "h": %s}'%(int(v['points'][0][0]), int(v['points'][0][1]), int(v['points'][1][0])-int(v['points'][0][0]), int(v['points'][1][1])-int(v['points'][0][1]))).encode('UTF-8'))
    fdata.write('],\r\n'.encode('UTF-8'))
fdata.write('}'.encode('UTF-8'))
fdata.close()