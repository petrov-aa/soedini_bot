from PIL import Image


def get_combined_image(image_list):
    """

    :rtype: Image
    :type image_list: list(Image)
    """
    image_path_list = map(lambda img: img.path, image_list)
    images = list(map(Image.open, image_path_list))
    widths, heights = zip(*(i.size for i in images))

    min_width = min(widths)
    min_height = min(heights)

    total_width = min_width * len(images)

    combined = Image.new('RGB', (total_width, min_height))

    x_offset = 0
    for image in images:
        combined.paste(image, (x_offset, 0))
        x_offset += image.size[0]

    return combined

