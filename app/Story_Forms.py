from wtforms import Form, FileField, TextAreaField, validators

class CreateStoryForm(Form):
    image = FileField(u'Image File', [validators.regexp(u'[^\\s]+(.*?)\\.(jpg|jpeg|png|gif|JPG|JPEG|PNG|GIF)$')])
    description = TextAreaField(u'Image Description')
