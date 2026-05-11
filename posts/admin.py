from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Post,PostComment,PostImage, PostVideo

# admin.site.register(Post)
admin.site.register(PostComment)
# admin.site.register(PostImage)
# admin.site.register(PostVideo) 


class PostImageInline(admin.StackedInline):
    model = PostImage
    readonly_fields = ['post_image','image','likes']

    def post_image(self, obj):
        return mark_safe('<img src="{url}" width="200" />'.format(
                url = obj.image.url,
                width=obj.image.width,
                height=obj.image.height,
            )
        )

class PostVideoInline(admin.StackedInline):
    model = PostVideo
    readonly_fields = ['likes']

# class PostCommentInline(admin.StackedInline):
#     model = PostComment

@admin.register(Post)
class  PostAdmin(admin.ModelAdmin):
    inlines = [PostImageInline, PostVideoInline,]
    # readonly_fields = ['user','likes','pending_text','text','pending_datetime','updated_datetime']
    # search_fields = ['title','slug']