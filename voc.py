from importlib.resources import path
import numpy as np
import os
import xml.etree.ElementTree as ET
import pickle
import pathlib
import glob

def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

def derive_image_path_from_annotation(annotation_path: str) -> str:
    desired_path = pathlib.Path(annotation_path)
    name_only = str(desired_path.stem)
    parent_dir = str(desired_path.parent)

    image_dir = replace_last(parent_dir, "Annotation", "Image")
    image_path = pathlib.Path(image_dir).joinpath(f"{name_only}.jpg")
    return str(image_path)

def compute_dir(dir: str, extension: str , is_validation: bool):
        mod_path = pathlib.Path(dir).joinpath(f"**/*.{extension}" if is_validation == True else f"*.{extension}" )
        return [ str(x) for x in glob.glob(str(mod_path))]

def parse_voc_annotation(ann_dir, img_dir, cache_name, labels=[], is_validation = False):

    if  os.path.exists(cache_name):
        with open(cache_name, 'rb') as handle:
            cache = pickle.load(handle)
        all_insts, seen_labels = cache['all_insts'], cache['seen_labels']
    else:
        all_insts = []
        seen_labels = {}

        samples = compute_dir(ann_dir, "xml", is_validation)
        for item in samples[:3]:
            print(str(item),derive_image_path_from_annotation(str(item)))
        
        for annotation_xml_file in sorted(samples):
        #for ann in sorted(os.listdir(ann_dir)):
            img = {'object':[],  'xml_name_only': pathlib.Path(annotation_xml_file).stem }

            try:
                tree = ET.parse(annotation_xml_file)
            except Exception as e:
                print(e)
                print('Ignore this bad annotation: ' + annotation_xml_file)
                continue
            
            for elem in tree.iter():
                if 'filename' in elem.tag:
                    #img['filename'] = img_dir + elem.text
                    #img['filename'] = f"{img_dir}{pathlib.Path(ann).stem}.jpg"
                    x = derive_image_path_from_annotation(annotation_xml_file)
                    #print(x,ann_dir)
                    img['filename'] = x
                if 'width' in elem.tag:
                    img['width'] = int(elem.text)
                if 'height' in elem.tag:
                    img['height'] = int(elem.text)
                if 'object' in elem.tag or 'part' in elem.tag:
                    obj = {}
                    
                    for attr in list(elem):
                        if 'name' in attr.tag:
                            obj['name'] = attr.text

                            if obj['name'] in seen_labels:
                                seen_labels[obj['name']] += 1
                            else:
                                seen_labels[obj['name']] = 1
                            
                            if len(labels) > 0 and obj['name'] not in labels:
                                break
                            else:
                                img['object'] += [obj]
                                
                        if 'bndbox' in attr.tag:
                            for dim in list(attr):
                                if 'xmin' in dim.tag:
                                    obj['xmin'] = int(round(float(dim.text)))
                                if 'ymin' in dim.tag:
                                    obj['ymin'] = int(round(float(dim.text)))
                                if 'xmax' in dim.tag:
                                    obj['xmax'] = int(round(float(dim.text)))
                                if 'ymax' in dim.tag:
                                    obj['ymax'] = int(round(float(dim.text)))

            if len(img['object']) > 0:
                all_insts += [img]

        cache = {'all_insts': all_insts, 'seen_labels': seen_labels}
        with open(cache_name, 'wb') as handle:
            pickle.dump(cache, handle, protocol=pickle.HIGHEST_PROTOCOL)    
                        
    return all_insts, seen_labels