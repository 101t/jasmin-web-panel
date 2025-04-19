from django import forms


class SendMessageForm(forms.Form):
    send_type = forms.ChoiceField(
        label='Send Type', choices=(('smpp', 'SMPP'), ('http', 'HTTP')), initial='smpp',
        help_text='Choose the way to send SMS via gateway, smpp or http'
    )
    src_addr = forms.CharField(
        label='Header', max_length=20, initial="JasminSMS",
        help_text="Header (from) field, it's represent the source address")
    dst_addr = forms.CharField(
        label='MSISDN', max_length=20, initial='',
        help_text='MSISDN (to) field, it\'s represent the numbers, example: +1234567890'
    )
    text = forms.CharField(
        label='Message', max_length=500, initial='test message', widget=forms.Textarea(),
        help_text='Message (content) field, it\'s represent the message content'
    )
