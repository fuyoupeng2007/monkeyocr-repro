import os
import time


import torch
from loguru import logger

from magic_pdf.model.batch_analyze_llm import BatchAnalyzeLLM
from magic_pdf.model.sub_modules.model_utils import get_vram

os.environ['NO_ALBUMENTATIONS_UPDATE'] = '1'

from magic_pdf.data.dataset import Dataset
from magic_pdf.libs.clean_memory import clean_memory
from magic_pdf.operators.models_llm import InferenceResultLLM
        

def doc_analyze_llm(
    dataset: Dataset,
    MonkeyOCR_model,
    start_page_id=0,
    end_page_id=None,
) -> InferenceResultLLM:

    end_page_id = end_page_id if end_page_id else len(dataset) - 1

    batch_analyze = False
    device = MonkeyOCR_model.device

    npu_support = False
    if str(device).startswith("npu"):
        import torch_npu
        if torch_npu.npu.is_available():
            npu_support = True

    if torch.cuda.is_available() and device != 'cpu' or npu_support:
        gpu_memory = int(os.getenv("VIRTUAL_VRAM_SIZE", round(get_vram(device))))
        if gpu_memory is not None and gpu_memory >= 8:

            if 8 <= gpu_memory < 10:
                batch_ratio = 2
            elif 10 <= gpu_memory <= 12:
                batch_ratio = 4
            elif 12 < gpu_memory <= 16:
                batch_ratio = 8
            elif 16 < gpu_memory <= 24:
                batch_ratio = 16
            else:
                batch_ratio = 32

            if batch_ratio >= 1:
                logger.info(f'gpu_memory: {gpu_memory} GB, batch_ratio: {batch_ratio}')
                batch_model = BatchAnalyzeLLM(model=MonkeyOCR_model, batch_ratio=batch_ratio)

    model_json = []
    doc_analyze_start = time.time()

    images = []
    for index in range(len(dataset)):
        if start_page_id <= index <= end_page_id:
            page_data = dataset.get_page(index)
            img_dict = page_data.get_image()
            images.append(img_dict['img'])
    analyze_result = batch_model(images)

    for index in range(len(dataset)):
        page_data = dataset.get_page(index)
        img_dict = page_data.get_image()
        page_width = img_dict['width']
        page_height = img_dict['height']
        if start_page_id <= index <= end_page_id:
            result = analyze_result.pop(0)
        else:
            result = []

        page_info = {'page_no': index, 'height': page_height, 'width': page_width}
        page_dict = {'layout_dets': result, 'page_info': page_info}
        model_json.append(page_dict)

    gc_start = time.time()
    clean_memory(device)
    gc_time = round(time.time() - gc_start, 2)
    logger.info(f'gc time: {gc_time}')

    doc_analyze_time = round(time.time() - doc_analyze_start, 2)
    doc_analyze_speed = round((end_page_id + 1 - start_page_id) / doc_analyze_time, 2)
    logger.info(
        f'doc analyze time: {round(time.time() - doc_analyze_start, 2)},'
        f' speed: {doc_analyze_speed} pages/second'
    )

    return InferenceResultLLM(model_json, dataset)
