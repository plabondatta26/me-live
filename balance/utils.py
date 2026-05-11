def custom_unique_slug_generator_for_title(sender,instance, *args, **kwargs):
    if not instance.slug:
        title = instance.title.lower()
        words = title.split(' ')
        temp = ''
        for word in words:
            if word.strip() != '':
                word_separation = word.split('-')
                inner_temp = ''
                for x in word_separation:
                    if x.strip() != '':
                        if inner_temp != '':
                            inner_temp += f"-{x.strip()}"
                        else:
                            inner_temp += x.strip()
                if inner_temp != '':
                    if temp != '':
                        temp += f"-{inner_temp}"
                    else:
                        temp += inner_temp
        # Checking for existing slug
        Klass = instance.__class__
        qs_objs = Klass.objects.filter(slug=temp)
        if qs_objs.exists():
            temp += f"-{qs_objs.count()+1}"
        instance.slug = temp