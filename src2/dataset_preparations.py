import pandas as pd
import torchvision
import json

from torch.utils.data import DataLoader
from classes import Imagem, ImgDataset
from definitions import *
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

def get_img_paths(root_path):
    stanford_training_set = {}
    for path, subdirs, files in os.walk(root_path):
        for img_name in files:
            stanford_training_set[img_name] = os.path.join(path, img_name)
    return stanford_training_set


def get_labels(root_path, csv_name: str):
    path = os.path.join(root_path, csv_name)
    if csv_name.endswith('.csv'):
        colnames = ['fname', 'x0', 'y0', 'x1', 'y1', 'label']
        labels = pd.read_csv(path, names=colnames, header=None)
        return labels
    else:
        with open(path) as f:
            labels = json.load(f)
            return labels


def get_dataset(folder, labels, has_annotation=True, is_validation=True):
    images = []
    print("Constructing dataset.")
    annotation_pos = 0
    for info_img in labels['images']:
        bboxes = []
        categories = []
        areas = []
        if has_annotation:
            while annotation_pos < len(labels['annotations']):
                annotation = labels['annotations'][annotation_pos]
                if annotation['image_id'] != info_img['id']:
                    break

                bboxes.append(annotation['bbox'])
                categories.append(annotation['category_id'])
                areas.append(annotation['area'])
                annotation_pos += 1

        if len(bboxes) > 0 or not has_annotation:
            path = os.path.join(folder, info_img['file_name'].replace('.png', '.jpg'))
            img = Imagem(path=path, bounding_box=bboxes, label=categories, areas=areas)
            images.append(img)

    return ImgDataset(images, is_validation)


def collate_fn(batch):
    return tuple(zip(*batch))


def create_data_loader(dataset, is_training_dataset, num_workers=0):
    train_loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=is_training_dataset,
        num_workers=num_workers,
        collate_fn=collate_fn
    )

    return train_loader


def create_model(num_classes):
    # load Faster RCNN pre-trained model
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)

    # get the number of input features
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # define a new head for the detector with required number of classes
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model