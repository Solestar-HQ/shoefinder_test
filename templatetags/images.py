from django import template 
register = template.Library()

from findyourshoe.models import (
    Model,
    ShoeImage
)


@register.simple_tag
def images_from(model):
    model_images = ShoeImage.objects.filter(
        brand=model.brand, 
        model=model
    ).values('color', 'image')
    
    model_colors = list(Model.objects.filter(name=model).values('colors'))
    print(f"COLORS: ", model_colors)
    
    images = {}
    # for image in model_images:
    #     if image['color'] not in images:
    #         images[image['color']] = []
    #     images[image['color']].append(image['image'])
    
    for i in range(len(model_colors)):
        print(f"I: ", i)
        if i < model_images.count():
            image = model_images[i]
            print(f"M Images: ", image)
            
        else:
            print(f"No model image")
        # if model_images[i]['color'] not in images:
        #     images[model_images[i]['color']] = []
        # images[model_images[i]['color']].append(model_images['image']) 

    
    return images