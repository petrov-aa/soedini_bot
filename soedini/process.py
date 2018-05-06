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
        ratio = min_height / image.size[1]
        new_width = int(float(image.size[0])*ratio)
        new_height = int(float(image.size[1])*ratio)
        if new_width < min_width:
            ratio1 = min_width / new_width
            new_height = int(float(new_height) * ratio1)
            new_width = min_width
        image = image.resize((new_width, new_height), Image.ANTIALIAS)
        combined.paste(image, (x_offset, 0))
        x_offset += min_width

    return combined

