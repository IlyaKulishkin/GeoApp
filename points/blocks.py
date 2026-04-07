from wagtail.blocks import StructBlock, ListBlock, CharBlock, RichTextBlock, StreamBlock
from wagtail.images.blocks import ImageChooserBlock


class SliderItemBlock(StructBlock):
    image = ImageChooserBlock(label="Изображение", required=True)
    caption = CharBlock(label="Подпись", required=False)

    class Meta:
        icon = "image"
        label = "Слайд"


class SliderBlock(StructBlock):
    slides = ListBlock(
        SliderItemBlock(),
        min_num=3,
        max_num=10,
        label="Слайды"
    )

    class Meta:
        icon = "image"
        label = "Слайдер"
        template = "blocks/slider.html"


class HeaderBlock(StructBlock):
    title = CharBlock(label="Заголовок", required=True)
    description = RichTextBlock(
        label="Описание",
        features=['bold', 'italic', 'underline'],
        required=False
    )

    class Meta:
        icon = "title"
        label = "Заглавный блок"
        template = "blocks/header.html"