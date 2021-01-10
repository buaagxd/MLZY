import os
import random
import config
import xml.etree.ElementTree
from tqdm import tqdm


# 打乱数据
def shuffle_data(data_list_path):
    with open(data_list_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        random.shuffle(lines)
    with open(data_list_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


# 生成图像列表
def create(images_dir, annotations_dir, train_list_path, test_list_path, label_file):
    f_train = open(train_list_path, 'w', encoding='utf-8')
    f_test = open(test_list_path, 'w', encoding='utf-8')
    f_label = open(label_file, 'w', encoding='utf-8')
    f_label.write("background\n")
    label = set()
    images = os.listdir(images_dir)
    i = 0
    for image in tqdm(images):
        i += 1
        annotation_path = os.path.join(annotations_dir, image[:-3] + 'xml')
        image_path = os.path.join(images_dir, image)
        if not os.path.exists(annotation_path):
            continue
        root = xml.etree.ElementTree.parse(annotation_path).getroot()
        for object in root.findall('object'):
            label.add(object.find('name').text)
        if i % 20 == 0:
            f_test.write("%s\t%s\n" % (image_path.replace('\\', '/'), annotation_path.replace('\\', '/')))
        else:
            f_train.write("%s\t%s\n" % (image_path.replace('\\', '/'), annotation_path.replace('\\', '/')))
    for l in label:
        f_label.write("%s\n" % l)
    f_train.close()
    f_test.close()
    f_label.close()

    # 打乱训练数据
    shuffle_data(train_list_path)
    print('create data list done!')


if __name__ == '__main__':
    create('dataset/images', 'dataset/annotations', config.train_list, config.test_list, config.label_file)
