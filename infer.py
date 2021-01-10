import os
import time
import cv2
import numpy as np
import paddle.fluid as fluid
from PIL import Image, ImageFont, ImageDraw

# image mean
img_mean = 127.5
# image std.
img_std = 0.007843
# data label/
label_file = 'dataset/label_list'
# threshold value
score_threshold = 0.45
# infer model path
infer_model_path = 'models/vgg_ssd/infer'
# Whether use GPU to train.
use_gpu = True

if not os.path.exists(infer_model_path):
    raise ValueError("The model path [%s] does not exist." % infer_model_path)

place = fluid.CUDAPlace(0) if use_gpu else fluid.CPUPlace()
exe = fluid.Executor(place)
exe.run(fluid.default_startup_program())

[infer_program,
 feeded_var_names,
 target_var] = fluid.io.load_inference_model(dirname=infer_model_path, executor=exe)

with open(label_file, 'r', encoding='utf-8') as f:
    names = f.readlines()


# 图像预处理
def load_image(image_path):
    if not os.path.exists(image_path):
        raise ValueError("%s is not exist, you should specify data path correctly." % image_path)
    img = cv2.imread(image_path)
    img = cv2.resize(img, (300, 300))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.transpose((2, 0, 1))
    img = np.expand_dims(img, axis=0).astype(np.float32)
    img = (img - img_mean) * img_std
    return img


# 预测图像
def infer(image_path):
    img = load_image(image_path)
    nmsed_out_v, = exe.run(infer_program,
                           feed={feeded_var_names[0]: img},
                           fetch_list=target_var,
                           return_numpy=False)
    nmsed_out_v = np.array(nmsed_out_v)
    results = []
    for dt in nmsed_out_v:
        if dt[1] < score_threshold:
            continue
        results.append(dt)
    return results


# 限制数据的结果，保证在合理范围内
def clip_bbox(bbox):
    xmin = max(min(bbox[0], 1.), 0.)
    ymin = max(min(bbox[1], 1.), 0.)
    xmax = max(min(bbox[2], 1.), 0.)
    ymax = max(min(bbox[3], 1.), 0.)
    return xmin, ymin, xmax, ymax


# 对图像进行画框
def draw_image(image_path, results):
    img = cv2.imread(image_path)
    w, h, c = img.shape
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    for result in results:
        xmin, ymin, xmax, ymax = clip_bbox(result[2:])
        xmin, ymin, xmax, ymax = int(xmin * h), int(ymin * w), int(xmax * h), int(ymax * w)
        draw.rectangle([xmin, ymin, xmax, ymax], outline=(0, 0, 255), width=4)
        # 字体的格式
        font_style = ImageFont.truetype("font/simfang.ttf", 18, encoding="utf-8")
        # 绘制文本
        draw.text((xmin, ymin), '%s, %0.2f' % (names[int(result[0])], result[1]), (0, 255, 0),
                  font=font_style)
    # 显示图像
    cv2.imshow('result image', cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR))
    cv2.waitKey(1)


if __name__ == '__main__':
    # 将数据集中的图像一一预测并展示
    # images = os.listdir('dataset/images/')
    # for im in images:
    #     img_path = 'dataset/images/' + im
    #     result = infer(img_path)
    #     draw_image(img_path, result)
    #     time.sleep(1)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # 单张图像预测
    img_path = '000001.jpg'
    result = infer(img_path)
    draw_image(img_path, result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
