import math
from typing import List

import PIL.Image

from bot.models import Session


def transpose(matrix: List[list]) -> List[list]:
    """
    Функция транспонирования матриц, примеры:
    1. [[1], [2], [3], [4], [5], [6]] -> [[1, 2, 3, 4, 5, 6]]
    2. [[1, 2, 3, 4, 5, 6]] -> [[1], [2], [3], [4], [5], [6]]
    3. [[1,3,4], [4,5,6], [7,8,9]] -> [[1, 4, 7], [3, 5, 8], [4, 6, 9]]
    4. [[1,2], [3,4], [5,6]] -> [[1, 3, 5], [2, 4, 6]]
    :param matrix:
    :return:
    """
    return list(map(list, zip(*(i for i in matrix))))


def convert_list_to_matrix(lst: list) -> List[list]:
    return [lst]


def split_vector_by_rows(vector: List[list], row_count: int) -> List[list]:
    row = vector[0]
    length = len(row)
    per_row = math.ceil(length/row_count)
    left_edge = 0
    right_edge = per_row
    matrix = []
    while left_edge < length:
        matrix.append(row[left_edge:right_edge])
        left_edge = right_edge
        right_edge += per_row
    return matrix


def get_resized_image(image: PIL.Image.Image, max_width: int, max_height: int) -> PIL.Image.Image:
    """
    Масштабирует изображение так, что длинная его сторона уменьшается до соответствующей ей максимальной
    из указанных (max_width или max_height)
    :param image:
    :param max_width:
    :param max_height:
    :return:
    """
    image_height = image.size[1]
    image_width = image.size[0]
    if image_height >= image_width:
        ratio = float(max_width / image_width)
        new_image_height = math.ceil(image_height * ratio)
        new_image_width = math.ceil(max_width)
    else:
        ratio = float(max_height / image_height)
        new_image_width = math.ceil(image_width * ratio)
        new_image_height = math.ceil(max_height)
    image_clone = image.copy()
    image_clone.resize((new_image_width, new_image_height), PIL.Image.ANTIALIAS)
    image_clone = image_clone.crop((0, 0, max_width, max_width))
    return image_clone


def normalize_images(images: List[PIL.Image.Image]):
    widths, heights = zip(*(i.size for i in images))
    min_width = min(widths)
    min_height = min(heights)
    normalized_images = [get_resized_image(image, min_height, min_width) for image in images]
    return normalized_images, min_width, min_height


def get_combined_image(images: List[PIL.Image.Image], mode: str):
    normalized_images, min_width, min_height = normalize_images(images)
    row = convert_list_to_matrix(normalized_images)
    if mode == Session.Modes.HORIZONTAL:
        return render_image(row, min_width, min_height)
    if mode == Session.Modes.VERTICAL:
        column = transpose(row)
        return render_image(column, min_width, min_height)
    if mode == Session.Modes.TWO_ROWS:
        matrix = split_vector_by_rows(row, 2)
        return render_image(matrix, min_width, min_height)
    if mode == Session.Modes.SQUARE:
        # пробуем создать максимально квадратную матрицу из изображений
        matrix = split_vector_by_rows(row, math.ceil(math.sqrt(len(row[0]))))
        return render_image(matrix, min_width, min_height)
    raise Exception("Unknown mode.")


def render_image(matrix: List[List[PIL.Image.Image]], width: int, height: int):
    """
    Выводит матрицу изображений
    :param matrix:
    :param width:
    :param height:
    :return:
    """
    rows = len(matrix)
    columns = len(matrix[0])
    total_width = columns * width
    total_height = rows * height
    combined = PIL.Image.new('RGB', (total_width, total_height))
    for row in range(rows):
        for column in range(columns):
            if row > len(matrix) - 1 or column > len(matrix[row]) - 1:
                continue
            image = matrix[row][column]
            y_offset = row * height
            x_offset = column * width
            combined.paste(image, (x_offset, y_offset))
    return combined
